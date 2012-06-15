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

import optparse
import string
from os.path import join, dirname, exists

db_create_template = """
# run this as postgres user, eg:
# imposm-psqldb > create_db.sh; sudo su postgres; sh ./create_db.sh
set -xe
createuser --no-superuser --no-createrole --createdb ${user}
createdb -E UTF8 -O ${user} ${dbname}
createlang plpgsql ${dbname}
psql -d ${dbname} -f ${postgis_sql}
psql -d ${dbname} -f ${spatial_ref_sys_sql}
psql -d ${dbname} -f ${epsg900913_sql}
echo "ALTER TABLE geometry_columns OWNER TO ${user}; ALTER TABLE spatial_ref_sys OWNER TO ${user};" | psql -d ${dbname}
echo "ALTER USER ${user} WITH PASSWORD '${password}';" |psql -d ${dbname}
echo "host\t${dbname}\t${user}\t127.0.0.1/32\tmd5" >> ${pg_hba}
set +x
echo "Done. Don't forget to restart postgresql!"
""".strip()

def find_sql_files(version, mapping):
    
    pg_hba = '/path/to/pg_hba.conf \t\t# <- CHANGE THIS PATH'
    postgis_sql = '/path/to/postgis.sql \t\t# <- CHANGE THIS PATH'
    spatial_ref_sys_sql = '/path/to/spatial_ref_sys.sql \t# <- CHANGE THIS PATH' 
    
    if version in ('8.3', 'auto'):
        p = '/usr/share/postgresql-8.3-postgis/lwpostgis.sql'
        if exists(p):
            postgis_sql = p
        p = '/usr/share/postgresql-8.3-postgis/spatial_ref_sys.sql'
        if exists(p):
            spatial_ref_sys_sql = p
        p = '/etc/postgresql/8.3/main/pg_hba.conf'
        if exists(p):
            pg_hba = p
    
    if version in ('8.4', 'auto'):
        p = '/usr/share/postgresql/8.4/contrib/postgis.sql'
        if exists(p):
            postgis_sql = p
        p = '/usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql'
        if exists(p):
            postgis_sql = p
        p = '/usr/share/postgresql/8.4/contrib/spatial_ref_sys.sql'
        if exists(p):
            spatial_ref_sys_sql = p
        p = '/usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql'
        if exists(p):
            spatial_ref_sys_sql = p
        p = '/etc/postgresql/8.4/main/pg_hba.conf'
        if exists(p):
            pg_hba = p
    
    if version in ('9.1', 'auto'):
        p = '/usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql'
        if exists(p):
            postgis_sql = p
        p = '/usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql'
        if exists(p):
            spatial_ref_sys_sql = p
        p = '/etc/postgresql/9.1/main/pg_hba.conf'
        if exists(p):
            pg_hba = p
    
    mapping['postgis_sql'] = postgis_sql
    mapping['spatial_ref_sys_sql'] = spatial_ref_sys_sql
    mapping['pg_hba'] = pg_hba

def main():
    usage = '%prog [options]'
    desc = 'Outputs shell commands to create a PostGIS database.'
    parser = optparse.OptionParser(usage=usage, description=desc)
    parser.add_option('--database', dest='dbname', metavar='osm', default='osm')
    parser.add_option('--user', dest='user', metavar='osm', default='osm')
    parser.add_option('--password', dest='password', metavar='osm', default='osm')
    parser.add_option('--pg-version', dest='pg_version', metavar='8.3|8.4|auto', default='auto')
    
    (options, args) = parser.parse_args()

    mapping = {
        'user': options.user,
        'dbname': options.dbname,
        'password': options.password,
    }
    
    mapping['epsg900913_sql'] = join(dirname(__file__), '900913.sql')
    find_sql_files(options.pg_version, mapping)
    
    template = string.Template(db_create_template)
    print template.substitute(mapping)



if __name__ == '__main__':
    main()
