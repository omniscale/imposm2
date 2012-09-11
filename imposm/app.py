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
import glob
import sys
import os
import optparse
import logging

import multiprocessing
from imposm.util import setproctitle

try:
    import shapely.speedups
    if shapely.speedups.available:
        print 'Enabling Shapely speedups.'
        shapely.speedups.enable()
except ImportError:
    try:
        import shapely_speedups
        print 'Patching Shapely.'
        shapely_speedups.patch_shapely()
    except ImportError:
        pass

import imposm.config
import imposm.mapping
import imposm.util
import imposm.version
from imposm.writer import ImposmWriter
from imposm.db.config import DB
from imposm.cache import OSMCache
from imposm.reader import ImposmReader
from imposm.mapping import TagMapper
from imposm.geom import load_geom

try:
    n_cpu = multiprocessing.cpu_count()
except NotImplementedError:
    n_cpu = 2

def setup_logging(debug=False):
    imposm_log = logging.getLogger('imposm')
    imposm_log.setLevel(logging.DEBUG if debug else logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    imposm_log.addHandler(ch)

__version__ = imposm.version.__version__

def main(argv=None):
    setproctitle('imposm: main')

    usage = '%prog [options] [input]...'
    parser = optparse.OptionParser(usage=usage, add_help_option=False,
        version="%prog " + __version__)
    parser.add_option('--help', dest='help', action='store_true',
        default=False, help='show this help message and exit')
    parser.add_option('--debug', action='store_true',
        default=False, help='show debug information')
    parser.add_option('--quiet', action='store_true',
        default=False, help='only print progress every 60 seconds')

    parser.add_option('-m', '--mapping-file', dest='mapping_file',
        metavar='<file>')
    parser.add_option('-h', '--host', dest='host', metavar='<host>')
    parser.add_option('-p', '--port', dest='port', metavar='<port>')
    parser.add_option('-d', '--database', dest='db', metavar='<dbname>')
    parser.add_option('-U', '--user', dest='user', metavar='<user>')
    parser.add_option('--proj', dest='proj', metavar='EPSG:900913')
    parser.add_option('--connection', dest='connection',
        help="connection string like postgis://user:pass@host:port/database,"
             " this overwrites the -h/-p/-d/-U options")

    parser.add_option('-c', '--concurrency', dest='concurrency', metavar='N',
                      type='int', default=n_cpu)

    parser.add_option('--merge-cache', dest='merge_cache', default=False,
        action='store_true')
    parser.add_option('--overwrite-cache', dest='overwrite_cache', default=False,
        action='store_true')
    parser.add_option('--cache-dir', dest='cache_dir', default='.',
        help="path where node/ways/relations should be cached [current working dir]")


    parser.add_option('--table-prefix',
        dest='table_prefix', default=None, metavar='osm_new_',
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

    parser.add_option('--limit-to', dest='limit_to', metavar='WKT file',
        help='limit imported geometries to WKT (multi)polygons in EPSG:4326')

    (options, args) = parser.parse_args(argv)

    setup_logging(debug=options.debug)

    if (argv and len(argv) == 0) or (not argv and len(sys.argv) == 1):
        options.help = True

    if not any([options.read, options.write, options.optimize, options.deploy_tables,
        options.recover_tables, options.remove_backup_tables]):
        options.help = True

    if options.help:
        parser.print_help()
        sys.exit(1)

    if options.quiet:
        logger = imposm.util.QuietProgressLog
        logger_parser = imposm.util.QuietParserProgress
    else:
        logger = imposm.util.ProgressLog
        logger_parser = imposm.util.ParserProgress

    if options.proj:
        if ':' not in options.proj:
            print 'ERROR: --proj should be in EPSG:00000 format'
            sys.exit(1)
        # check proj if meter_to_mapunit needs to do anything
        if options.proj.lower() == 'epsg:4326':
            imposm.mapping.import_srs_is_geographic = True

    mapping_file = os.path.join(os.path.dirname(__file__),
        'defaultmapping.py')
    if options.mapping_file:
        print 'loading %s as mapping' % options.mapping_file
        mapping_file = options.mapping_file

    polygon = None
    if options.limit_to:
        logger.message('## reading --limit-to %s' % options.limit_to)
        polygon_timer = imposm.util.Timer('reading', logger)
        polygon = load_geom(options.limit_to)
        polygon_timer.stop()
        if polygon is None:
            print 'ERROR: No valid polygon/multipolygon found'
            sys.exit(1)

    mappings = {}
    execfile(mapping_file, mappings)
    tag_mapping = TagMapper([m for n, m in mappings.iteritems()
        if isinstance(m, imposm.mapping.Mapping)], limit_to=polygon)

    if 'IMPOSM_MULTIPOLYGON_REPORT' in os.environ:
        imposm.config.imposm_multipolygon_report = float(os.environ['IMPOSM_MULTIPOLYGON_REPORT'])
    if 'IMPOSM_MULTIPOLYGON_MAX_RING' in os.environ:
        imposm.config.imposm_multipolygon_max_ring = int(os.environ['IMPOSM_MULTIPOLYGON_MAX_RING'])

    if options.table_prefix:
        options.table_prefix = options.table_prefix.rstrip('_') + '_'
    if options.table_prefix_production:
        options.table_prefix_production = options.table_prefix_production.rstrip('_') + '_'
    if options.table_prefix_backup:
        options.table_prefix_backup = options.table_prefix_backup.rstrip('_') + '_'

    if (options.write or options.optimize or options.deploy_tables
        or options.remove_backup_tables or options.recover_tables):
        db_conf = mappings['db_conf']
        if options.table_prefix:
            db_conf.prefix = options.table_prefix
        else:
            options.table_prefix = db_conf.prefix.rstrip('_') + '_'

        if options.connection:
            from imposm.db.config import db_conf_from_string
            db_conf = db_conf_from_string(options.connection, db_conf)
        else:
            db_conf.host = options.host or db_conf.host
            db_conf.port = options.port or getattr(db_conf, 'port', None) #backw. compat
            if not options.db:
                parser.error('-d/--database is required for this mode')
            db_conf.db = options.db or db_conf.db
            db_conf.user = options.user or db_conf.user
            if options.user:
                from getpass import getpass
                db_conf.password = getpass('password for %(user)s at %(host)s:' % db_conf)

        if options.proj:
            db_conf.proj = options.proj

    imposm_timer = imposm.util.Timer('imposm', logger)

    if options.read:
        if not options.merge_cache:
            cache_files = glob.glob(os.path.join(options.cache_dir, 'imposm_*.cache'))
            if cache_files:
                if not options.overwrite_cache:
                    print (
                        "ERROR: found existing cache files in '%s'. "
                        'remove files or use --overwrite-cache or --merge-cache.'
                        % os.path.abspath(options.cache_dir)
                    )
                    sys.exit(2)
                for cache_file in cache_files:
                    os.unlink(cache_file)

    cache = OSMCache(options.cache_dir)

    if options.read:
        read_timer = imposm.util.Timer('reading', logger)

        if not args:
            print "no file(s) supplied"
            sys.exit(2)

        reader = ImposmReader(tag_mapping, cache=cache, merge=options.merge_cache,
            pool_size=options.concurrency, logger=logger_parser)
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
            db.commit()

        writer = ImposmWriter(tag_mapping, db, cache=cache,
            pool_size=options.concurrency, logger=logger,
            dry_run=options.dry_run)
        writer.relations()
        writer.ways()
        writer.nodes()

        if not options.dry_run:
            db = DB(db_conf)

            logger.message('## creating generalized tables')
            generalized_timer = imposm.util.Timer('generalizing tables', logger)
            db.create_generalized_tables(mappings)
            generalized_timer.stop()

            logger.message('## creating union views')
            view_timer = imposm.util.Timer('creating views', logger)
            db.create_views(mappings)
            view_timer.stop()

            db.commit()

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
        db.commit()

    if options.remove_backup_tables:
        db = DB(db_conf)
        db.remove_tables(options.table_prefix_backup)
        db.commit()

    imposm_timer.stop()

if __name__ == '__main__':
    main()
