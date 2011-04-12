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

from __future__ import with_statement
import sys
import os
import optparse
import logging

import multiprocessing
from imposm.util import setproctitle

try:
    import shapely_speedups
except ImportError:
    pass
else:
    print 'patching shapely'
    shapely_speedups.patch_shapely()

import imposm.mapping
import imposm.util
import imposm.version
from imposm.writer import ImposmWriter
from imposm.db import DB
from imposm.reader import ImposmReader
from imposm.mapping import TagMapper

try:
    n_cpu = multiprocessing.cpu_count()
except NotImplementedError:
    n_cpu = 2

def setup_logging():
    imposm_log = logging.getLogger('imposm')
    imposm_log.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    imposm_log.addHandler(ch)

__version__ = imposm.version.__version__

def main():
    setproctitle('imposm: main')
    setup_logging()

    usage = '%prog [options] [input]...'
    parser = optparse.OptionParser(usage=usage, add_help_option=False,
        version="%prog " + __version__)
    parser.add_option('--help', dest='help', action='store_true',
        default=False, help='show this help message and exit')
    parser.add_option('-m', '--mapping-file', dest='mapping_file',
        metavar='<file>')
    parser.add_option('-h', '--host', dest='host', metavar='<host>')
    parser.add_option('-d', '--database', dest='db', metavar='<dbname>')
    parser.add_option('-U', '--user', dest='user', metavar='<user>')
    parser.add_option('--proj', dest='proj', metavar='EPSG:900913')
    
    parser.add_option('-c', '--concurrency', dest='concurrency', metavar='N',
                      type='int', default=n_cpu)

    parser.add_option('--merge', dest='merge', default=False,
        action='store_true')

    parser.add_option('--table-prefix',
        dest='table_prefix', default='osm_new_', metavar='osm_new_',
        help='prefix for imported tables')
    parser.add_option('--table-prefix-production',
        dest='table_prefix_production', default='osm_', metavar='osm_',
        help='prefix for production tables')
    parser.add_option('--table-prefix-backup',
        dest='table_prefix_backup', default='osm_old_', metavar='osm_old_',
        help='prefix for backup tables')



    parser.add_option('--read', dest='read', default=False,
        action='store_true')
    parser.add_option('--write', dest='write', default=False,
        action='store_true')
    parser.add_option('--optimize', dest='optimize', default=False,
        action='store_true')
    parser.add_option('--deploy-production-tables', dest='deploy_tables', default=False,
        action='store_true', help='remove backup tables, move production tables '
        'to backup tables and move import tables to production tables')
    parser.add_option('--recover-production-tables', dest='recover_tables', default=False,
        action='store_true', help='move production tables to import tables and'
        'move backup tables to production tables')
    parser.add_option('--remove-backup-tables', dest='remove_backup_tables', default=False,
        action='store_true')
        

    parser.add_option('-n', '--dry-run', dest='dry_run', default=False,
        action='store_true')

    (options, args) = parser.parse_args()

    if options.help:
        parser.print_help()
        sys.exit(1)

    mapping_file = os.path.join(os.path.dirname(__file__),
        'defaultmapping.py')
    if options.mapping_file:
        print 'loading %s as mapping' % options.mapping_file
        mapping_file = options.mapping_file

    mappings = {}
    execfile(mapping_file, mappings)
    tag_mapping = TagMapper([m for n, m in mappings.iteritems() 
        if isinstance(m, imposm.mapping.Mapping)])

    if (options.write or options.optimize or options.deploy_tables
        or options.remove_backup_tables or options.recover_tables):
        db_conf = mappings['db_conf']
        db_conf.host = options.host or db_conf.host
        if not options.db:
            parser.error('-d/--database is required for this mode')
        db_conf.db = options.db or db_conf.db
        db_conf.user = options.user or db_conf.user
        if options.user:
            from getpass import getpass
            db_conf.password = getpass('password for %(user)s at %(host)s:' % db_conf)
        
        if options.proj:
            if ':' not in options.proj:
                print 'ERROR: --proj should be in EPSG:00000 format'
                sys.exit(1)
            db_conf.proj = options.proj
    
    logger = imposm.util.ProgressLog
    
    imposm_timer = imposm.util.Timer('imposm', logger)
    
    if options.read:
        read_timer = imposm.util.Timer('reading', logger)
        
        if args:
            reader = ImposmReader(tag_mapping, merge=options.merge, pool_size=options.concurrency,
                                  logger=logger)
            reader.estimated_coords = imposm.util.estimate_records(args)
            for arg in args:
                logger.message('## reading %s' % arg)
                reader.read(arg)
        
        read_timer.stop()

    if options.write:
        db = DB(db_conf)
        write_timer = imposm.util.Timer('writing', logger)
        
        logger.message('## dropping/creating tables')
        if not options.dry_run:
            db.create_tables(tag_mapping.mappings)

        logger.message('## writing data')
        # create views so we can access the table during the insert, ignore
        # errors for missing tables (i.e. generalized tables)
        if not options.dry_run:
            db.create_views(mappings, ignore_errors=True)
            db.connection.commit()

        writer = ImposmWriter(tag_mapping, db, pool_size=options.concurrency,
                              logger=logger, dry_run=options.dry_run)
        writer.relations()
        writer.ways()
        writer.nodes()

        if not options.dry_run:
            db = DB(db_conf)
            db.create_generalized_tables(mappings)
            db.create_views(mappings)
            db.connection.commit()
        
        write_timer.stop()

    if options.optimize:
        db = DB(db_conf)
        optimize_timer = imposm.util.Timer('optimizing', logger)
        logger.message('## optimizing tables')
        db.optimize(mappings)
        optimize_timer.stop()
    
    if options.recover_tables:
        assert not options.deploy_tables, ('cannot swap and recover production '
            'tables at the same time')
        options.table_prefix, options.table_prefix_backup = \
            options.table_prefix_backup, options.table_prefix
        
    if options.deploy_tables or options.recover_tables:
        db = DB(db_conf)
        db.swap_tables(options.table_prefix, 
            options.table_prefix_production, options.table_prefix_backup)
        db.remove_views(options.table_prefix)
        db.db_conf.prefix = options.table_prefix_production
        db.create_views(mappings)
        db.connection.commit()
    
    if options.remove_backup_tables:
        db = DB(db_conf)
        db.remove_tables(options.table_prefix_backup)
        db.connection.commit()
    
    imposm_timer.stop()

if __name__ == '__main__':
    main()
