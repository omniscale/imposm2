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

from collections import defaultdict
from multiprocessing import Process

import threading
from Queue import Queue 

from imposm.base import OSMElem
from imposm.geom import IncompletePolygonError
from imposm.mapping import DropElem
from imposm.multipolygon import RelationBuilder
from imposm.util import setproctitle


import logging
log = logging.getLogger(__name__)

class ImporterProcess(Process):
    name = 'importer'

    def __init__(self, in_queue, db, mapper, osm_cache, dry_run):
        Process.__init__(self)
        self.daemon = True
        setproctitle('imposm %s process' % self.name)

        self.in_queue = in_queue
        self.mapper = mapper
        self.osm_cache = osm_cache
        self.db = db
        self.dry_run = dry_run

    def run(self):
        self.setup()
        # cProfile.runctx('self.doit()', globals(), locals(), 'profile%s.dat' % (self.name,))
        self.doit()
        self.teardown()

    def setup(self):
        self.db_queue = Queue(256)
        self.db_importer = DBImporter(self.db_queue, self.db, dry_run=self.dry_run)
        self.db_importer.start()

    def doit(self):
        pass

    def teardown(self):
        self.osm_cache.close_all()
        self.db_queue.put(None)
        self.db_importer.join()

    def insert(self, mappings, osm_id, geom, tags):
        inserted = False
        for type, ms in mappings:
            for m in ms:
                osm_elem = OSMElem(osm_id, geom, type, tags)
                try:
                    m.filter(osm_elem)
                    m.build_geom(osm_elem)
                    extra_args = m.field_values(osm_elem)
                    self.db_queue.put((m, osm_id, osm_elem, extra_args))
                    inserted = True
                except DropElem:
                    pass
        return inserted

class NodeProcess(ImporterProcess):
    name = 'node'

    def doit(self):        
        while True:
            nodes = self.in_queue.get()
            if nodes is None:
                break
            
            for node in nodes:
                mappings = self.mapper.for_nodes(node.tags)
                if not mappings:
                    continue

                self.insert(mappings, node.osm_id, node.coord, node.tags)

class WayProcess(ImporterProcess):
    name = 'way'

    def doit(self):
        coords_cache = self.osm_cache.coords_cache(mode='r')
        inserted_ways_cache = self.osm_cache.inserted_ways_cache(mode='r')
        inserted_ways = iter(inserted_ways_cache)

        try:
            skip_id = inserted_ways.next()
        except StopIteration:
            skip_id = 2**64

        while True:
            ways = self.in_queue.get()
            if ways is None:
                break

            for way in ways:
                # forward to the next skip id that is not smaller
                # than our current id
                while skip_id < way.osm_id:
                    try:
                        skip_id = inserted_ways.next()
                    except StopIteration:
                        skip_id = 2**64
                
                if skip_id == way.osm_id:
                    continue

                mappings = self.mapper.for_ways(way.tags)
                if not mappings:
                    continue

                coords = coords_cache.get_coords(way.refs)

                if not coords:
                    print 'missing coords for way %s' % (way.osm_id, )
                    continue

                self.insert(mappings, way.osm_id, coords, way.tags)


class RelationProcess(ImporterProcess):
    name = 'relation'

    def __init__(self, in_queue, db, mapper, osm_cache, dry_run, inserted_way_queue):
        ImporterProcess.__init__(self, in_queue, db, mapper, osm_cache, dry_run)
        self.inserted_way_queue = inserted_way_queue

    def doit(self):
        coords_cache = self.osm_cache.coords_cache(mode='r')
        ways_cache = self.osm_cache.ways_cache(mode='r')

        while True:
            relations = self.in_queue.get()
            if relations is None:
                break
            
            for relation in relations:
                builder = RelationBuilder(relation, ways_cache, coords_cache)
                try:
                    builder.build()
                except IncompletePolygonError, ex:
                    if str(ex):
                        log.debug(ex)
                    continue
                mappings = self.mapper.for_relations(relation.tags)
                if mappings:
                    inserted = self.insert(mappings, relation.osm_id, relation.geom, relation.tags)
                    if inserted:
                        builder.mark_inserted_ways(self.inserted_way_queue)


class DBImporter(threading.Thread):
    def __init__(self, queue, db, dry_run=False):
        threading.Thread.__init__(self)
        self.db = db
        self.db.reconnect()
        self.queue = queue
        self.cur = None
        self.dry_run = dry_run
        self.mappings = defaultdict(list)

    def run(self):
        # cProfile.runctx('self.doit()', globals(), locals())
        # def doit(self):
        while True:
            data = self.queue.get()
            if data is None:
                break

            mapping, osm_id, osm_elem, extra_args = data
            insert_data = self.mappings[mapping]
            
            if isinstance(osm_elem.geom, (list)):
                for geom in osm_elem.geom:
                    insert_data.append((osm_id, osm_elem.type, self.db.geom_wrapper(geom)) + tuple(extra_args))
            else:
                insert_data.append((osm_id, osm_elem.type, self.db.geom_wrapper(osm_elem.geom)) + tuple(extra_args))

            if len(insert_data) >= 128:
                if not self.dry_run:
                    self.db.insert(mapping, insert_data)
                del self.mappings[mapping]

        # flush
        for mapping, insert_data in self.mappings.iteritems():
            if not self.dry_run:
                self.db.insert(mapping, insert_data)

