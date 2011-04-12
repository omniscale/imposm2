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

import array

from multiprocessing import Process, JoinableQueue

from imposm.dbimporter import NodeProcess, WayProcess, RelationProcess
from imposm.util import create_pool, shutdown_pool
from imposm.cache import OSMCache

class ImposmWriter(object):
    def __init__(self, mapping, db, cache, pool_size=2, logger=None, dry_run=False):
        self.mapping = mapping
        self.db = db
        self.mapper = mapping
        self.cache = cache
        self.pool_size = pool_size
        self.logger = logger
        self.dry_run = dry_run

    def _write_elem(self, proc, elem_cache, log, pool_size, proc_args=[]):
        queue = JoinableQueue(16)

        importer = lambda: proc(queue, self.db, self.mapper, self.cache, self.dry_run, *proc_args)
        pool = create_pool(importer, pool_size)

        data = []
        for i, elem in enumerate(elem_cache):
            if elem.tags:
                data.append(elem)
            if len(data) >= 128:
                queue.put(data)
                log.log(i)
                data = []
        queue.put(data)

        shutdown_pool(pool, queue)
        log.stop()
        self.cache.close_all()

    def relations(self):
        cache = self.cache.relations_cache()
        log = self.logger('relations', len(cache))
        inserted_way_queue = JoinableQueue()
        way_marker = WayMarkerProcess(inserted_way_queue, self.cache, self.logger)
        way_marker.start()

        self._write_elem(RelationProcess, cache, log, self.pool_size, [inserted_way_queue])

        inserted_way_queue.put(None)
        way_marker.join()

    def ways(self):
        cache = self.cache.ways_cache()
        log = self.logger('ways', len(cache))
        self._write_elem(WayProcess, cache, log, self.pool_size)

    def nodes(self):
        cache = self.cache.nodes_cache()
        log = self.logger('nodes', len(cache))
        self._write_elem(NodeProcess, cache, log, self.pool_size)
        

class WayMarkerProcess(Process):
    def __init__(self, queue, cache, logger):
        Process.__init__(self)
        self.daemon = True
        self.queue = queue
        self.cache = cache
        self.logger = logger
    
    def run(self):
        inserted_ways = array.array('I')
        while True:
            osmid = self.queue.get()
            if osmid is None:
                break
            inserted_ways.append(osmid)

        self.update_inserted_ways(inserted_ways)

    def update_inserted_ways(self, inserted_ways):
        log = self.logger('marking inserted ways', len(inserted_ways))
        cache = self.cache.ways_cache(mode='w')
        for i, osmid in enumerate(inserted_ways):
            way = cache.get(osmid)
            way.tags['_inserted_'] = True
            cache.put(osmid, way.tags, way.refs)
            if i % 100 == 0:
                log.log(i)
        cache.close()
        log.stop()