# Copyright 2011 Omniscale (http://omniscale.com)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

import psycopg2
import psycopg2.extensions

import logging
log = logging.getLogger(__name__)

from imposm.mapping import UnionView, GeneralizedTable, Mapping

class PostGISDB(object):
    def __init__(self, db_conf):
        self.db_conf = db_conf
        self.srid = int(db_conf['proj'].split(':')[1])
        self._insert_stmts = {}
        self._connection = None
        self._cur = None

    @property
    def table_prefix(self):
        return self.db_conf.prefix

    def to_tablename(self, name):
        return self.table_prefix.rstrip('_') + '_' + name.lower()

    @property
    def connection(self):
        if not self._connection:
            kw = {}
            if self.db_conf.port:
                kw['port'] = int(self.db_conf.port)
            self._connection = psycopg2.connect(
                database=self.db_conf.db,
                host=self.db_conf.host,
                user=self.db_conf.user,
                password=self.db_conf.password,
                sslmode=self.db_conf.get('sslmode', 'allow'),
                **kw
            )
            self._connection.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        return self._connection
    
    @property
    def cur(self):
        if self._cur is None:
            self._cur = self.connection.cursor()
        return self._cur
    
    def insert(self, mapping, insert_data, tries=0):
        insert_stmt = self.insert_stmt(mapping)
        try:
            if tries:
                self.reconnect()
            self.cur.executemany(insert_stmt, insert_data)
        except psycopg2.OperationalError, ex:
            if tries >= 8:
                log.warn('%s, giving up', ex)
                raise
            seconds = 2 ** (tries + 1)
            log.warn('%s, retry in %d', ex, seconds)
            time.sleep(seconds)
            self.insert(mapping, insert_data, tries=tries + 1)
        except psycopg2.Error, ex:
            self.connection.rollback()
            for data in insert_data:
                try:
                    self.cur.execute(insert_stmt, data)
                except psycopg2.Error, ex:
                    log.warn('error while importing "%r": %s', data, ex)
                    self.connection.rollback()
                else:
                    self.connection.commit()

        self.connection.commit()
    
    def wkb_wrapper(self, wkb):
        return psycopg2.Binary(wkb)
    
    def reconnect(self):
        if self._connection:
            try:
                self._connection.close()
            except psycopg2.InterfaceError:
                pass
        self._connection = None
        self._cur = None

    def insert_stmt(self, mapping):
        if mapping.name not in self._insert_stmts:
            self._insert_stmts[mapping.name] = self._insert_stmt(mapping)

        return self._insert_stmts[mapping.name]

    def _insert_stmt(self, mapping):
        extra_arg_names = extra_args = ''
        if mapping.fields:
            extra_arg_names = [n for n, t in mapping.fields]
            extra_args = ', %s' * len(extra_arg_names)
            extra_arg_names = ', ' + ', '.join('"' + name + '"' for name in extra_arg_names)
        return """INSERT INTO "%(tablename)s"
            (osm_id, name, type, geometry %(extra_arg_names)s)
            VALUES (%%s, %%s, %%s, ST_Transform(ST_GeomFromWKB(%%s, 4326), %(srid)s)
                %(extra_args)s)
        """.strip() % dict(tablename=self.table_prefix + mapping.name, srid=self.srid,
            extra_arg_names=extra_arg_names, extra_args=extra_args)


    def create_tables(self, mappings):
        for mapping in mappings:
            self.create_table(mapping)

    def create_table(self, mapping):
        tablename = self.table_prefix + mapping.name
        cur = self.connection.cursor()
        cur.execute('SAVEPOINT pre_drop_tables')
        try:
            cur.execute('DROP TABLE "' + tablename + '" CASCADE')
        except psycopg2.ProgrammingError:
            cur.execute('ROLLBACK TO SAVEPOINT pre_drop_tables')

        extra_fields = ''
        for n, t in mapping.fields:
            extra_fields += ', "%s" %s ' % (n, t.column_type)

        cur.execute("""
            CREATE TABLE "%s" (
                osm_id INT4 PRIMARY KEY,
                name VARCHAR(255),
                type VARCHAR(255)
                %s
            );
        """ % (tablename, extra_fields))
        cur.execute("""
            SELECT AddGeometryColumn ('', '%(tablename)s', 'geometry',
                                      %(srid)s, '%(pg_geometry_type)s', 2)
        """ % dict(tablename=tablename, srid=self.srid,
                   pg_geometry_type=mapping.geom_type))
        cur.execute("""
            CREATE INDEX "%(tablename)s_geom" ON "%(tablename)s" USING GIST (geometry)
        """ % dict(tablename=tablename))
    
    def swap_tables(self, new_prefix, existing_prefix, backup_prefix):
        cur = self.connection.cursor()

        self.remove_tables(backup_prefix)
        
        cur.execute('SELECT tablename FROM pg_tables WHERE tablename like %s', (existing_prefix + '%', ))
        existing_tables = []
        for row in cur:
            table_name = row[0]
            if not table_name.startswith((new_prefix, backup_prefix)):
                existing_tables.append(table_name)

        cur.execute('SELECT indexname FROM pg_indexes WHERE indexname like %s', (existing_prefix + '%', ))
        existing_indexes = set()
        for row in cur:
            index_name = row[0]
            if not index_name.startswith((new_prefix, backup_prefix)):
                existing_indexes.add(index_name)
        
        cur.execute('SELECT tablename FROM pg_tables WHERE tablename like %s', (new_prefix + '%', ))
        new_tables = []
        for row in cur:
            table_name = row[0]
            new_tables.append(table_name)

        cur.execute('SELECT indexname FROM pg_indexes WHERE indexname like %s', (new_prefix + '%', ))
        new_indexes = set()
        for row in cur:
            index_name = row[0]
            new_indexes.add(index_name)
        
        if not new_tables:
            raise RuntimeError('did not found tables to swap')
        
        for table_name in existing_tables:
            rename_to = table_name.replace(existing_prefix, backup_prefix)
            cur.execute('ALTER TABLE "%s" RENAME TO "%s"' % (table_name, rename_to))
            if table_name + '_geom' in existing_indexes:
                cur.execute('ALTER INDEX "%s" RENAME TO "%s"' % (table_name + '_geom', rename_to + '_geom'))
            if table_name + '_pkey' in existing_indexes:
                cur.execute('ALTER INDEX "%s" RENAME TO "%s"' % (table_name + '_pkey', rename_to + '_pkey'))
            cur.execute('UPDATE geometry_columns SET f_table_name = %s WHERE f_table_name = %s', (rename_to, table_name))
            
        for table_name in new_tables:
            rename_to = table_name.replace(new_prefix, existing_prefix)
            cur.execute('ALTER TABLE "%s" RENAME TO "%s"' % (table_name, rename_to))
            if table_name + '_geom' in new_indexes:
                cur.execute('ALTER INDEX "%s" RENAME TO "%s"' % (table_name + '_geom', rename_to + '_geom'))
            if table_name + '_pkey' in new_indexes:
                cur.execute('ALTER INDEX "%s" RENAME TO "%s"' % (table_name + '_pkey', rename_to + '_pkey'))
            cur.execute('UPDATE geometry_columns SET f_table_name = %s WHERE f_table_name = %s', (rename_to, table_name))
        
    def remove_tables(self, prefix):
        cur = self.connection.cursor()
        cur.execute('SELECT tablename FROM pg_tables WHERE tablename like %s', (prefix + '%', ))
        remove_tables = [row[0] for row in cur]
        
        for table_name in remove_tables:
            cur.execute("DROP TABLE %s CASCADE" % (table_name, ))
            cur.execute("DELETE FROM geometry_columns WHERE f_table_name = %s", (table_name, ))
        

    def remove_views(self, prefix):
        cur = self.connection.cursor()
        cur.execute('SELECT viewname FROM pg_views WHERE viewname like %s', (prefix + '%', ))
        remove_views = [row[0] for row in cur]
        
        for view_name in remove_views:
            cur.execute('DROP VIEW "%s" CASCADE' % (view_name, ))
            cur.execute("DELETE FROM geometry_columns WHERE f_table_name = %s", (view_name, ))
        
    
    def create_views(self, mappings, ignore_errors=False):
        for mapping in mappings.values():
            if isinstance(mapping, UnionView):
                PostGISUnionView(self, mapping).create(ignore_errors=ignore_errors)
    
    def create_generalized_tables(self, mappings):
        mappings = [m for m in mappings.values() if isinstance(m, GeneralizedTable)]
        for mapping in sorted(mappings, key=lambda x: x.name, reverse=True):
            PostGISGeneralizedTable(self, mapping).create()

    def optimize(self, mappings):
        mappings = [m for m in mappings.values() if isinstance(m, (GeneralizedTable, Mapping))]
        for mapping in mappings:
            table_name = self.to_tablename(mapping.name)
            self.optimize_table(table_name, '%s_geom' % table_name)
        self.vacuum()

    def optimize_table(self, table_name, idx_name):
        cur = self.connection.cursor()
        print 'Clustering table %s' % table_name
        cur.execute('CLUSTER "%s" ON "%s"' % (idx_name, table_name))
        self.connection.commit()

    def vacuum(self):
        old_isolation_level = self.connection.isolation_level
        self.reconnect()
        self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = self.connection.cursor()
        print 'Vacuum analyze'
        cur.execute("VACUUM ANALYZE")
        self.connection.set_isolation_level(old_isolation_level)


class PostGISUnionView(object):
    def __init__(self, db, mapping):
        self.mapping = mapping
        self.db = db
        self.view_name = db.to_tablename(mapping.name)

    def _view_stmt(self):
        selects = []
        for mapping in self.mapping.mappings:
            field_str = ', '.join(self._mapping_fields(mapping))
            selects.append("""SELECT osm_id, name, type, geometry, %s,
                '%s' as class from "%s" """ % (
                field_str, mapping.classname or mapping.name, self.db.to_tablename(mapping.name)))

        selects = '\nUNION ALL\n'.join(selects)

        stmt = 'CREATE OR REPLACE VIEW "%s" as (\n%s\n)' % (self.view_name, selects)
        
        return stmt

    def _geom_table_stmt(self):
        stmt = "insert into geometry_columns values ('', 'public', '%s', 'geometry', 2, %d, 'GEOMETRY')" % (
            self.view_name, self.db.srid)
        return stmt

    def _mapping_fields(self, mapping):
        mapping_fields = set([n for n, t in mapping.fields])
        fields = []
        for name, default in self.mapping.fields:
            if name in mapping_fields:
                fields.append('"' + name + '"')
            else:
                if default is None:
                    default = 'null'
                elif isinstance(default, basestring):
                    default = "'%s'" % default
                else:
                    default = str(default)
                fields.append(default + ' as "' + name + '"')
        return fields

    def create(self, ignore_errors):
        cur = self.db.connection.cursor()
        cur.execute('BEGIN')
        try:
            cur.execute('SAVEPOINT pre_create_view')
            cur.execute(self._view_stmt())
        except psycopg2.ProgrammingError:
            cur.execute('ROLLBACK TO SAVEPOINT pre_create_view')
            if not ignore_errors:
                raise

        cur.execute('select * from geometry_columns where f_table_name = %s', (self.view_name, ))
        if not cur.fetchall():
            cur.execute(self._geom_table_stmt())


class PostGISGeneralizedTable(object):
    def __init__(self, db, mapping):
        self.db = db
        self.mapping = mapping
        self.table_name = db.to_tablename(mapping.name)

    def _idx_stmt(self):
        return 'CREATE INDEX "%s_geom" ON "%s" USING GIST (geometry)' % (
            self.table_name, self.table_name)

    def _geom_table_stmt(self):
        stmt = "insert into geometry_columns values ('', 'public', '%s', 'geometry', 2, %d, 'GEOMETRY')" % (
            self.table_name, self.db.srid)
        return stmt

    def _stmt(self):
        fields = ', '.join([n for n, t in self.mapping.fields])
        if self.mapping.where:
            where = ' WHERE ' + self.mapping.where
        else:
            where = ''
        return """CREATE TABLE "%s" AS (SELECT osm_id, name, type, %s,
            ST_Simplify(geometry, %f) as geometry from "%s"%s)""" % (
            self.table_name, fields, self.mapping.tolerance, self.db.to_tablename(self.mapping.origin.name),
            where)

    def create(self):
        cur = self.db.connection.cursor()
        cur.execute('BEGIN')
        try:
            cur.execute('SAVEPOINT pre_drop_table')
            cur.execute('DROP TABLE "%s" CASCADE' % (self.table_name, ))
        except psycopg2.ProgrammingError:
            cur.execute('ROLLBACK TO SAVEPOINT pre_drop_table')
        

        cur.execute(self._stmt())
        cur.execute(self._idx_stmt())

        cur.execute('select * from geometry_columns where f_table_name = %s', (self.table_name, ))
        if not cur.fetchall():
            cur.execute(self._geom_table_stmt())

