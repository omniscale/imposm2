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

from multiprocessing import Process, JoinableQueue

from imposm.dbimporter import NodeProcessTuple, WayProcessTuple, RelationProcessTuple
from imposm.dbimporter import NodeProcessDict, WayProcessDict, RelationProcessDict
from imposm.util import create_pool, shutdown_pool

import_processes = {
    'tuple': {
        'node': NodeProcessTuple,
        'way': WayProcessTuple,
        'relation': RelationProcessTuple,
    },
    'dict': {
        'node': NodeProcessDict,
        'way': WayProcessDict,
        'relation': RelationProcessDict,
    }
}

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
        self.cache.remove_inserted_way_cache()
        cache = self.cache.relations_cache()
        log = self.logger('relations', len(cache))
        inserted_way_queue = JoinableQueue()
        way_marker = WayMarkerProcess(inserted_way_queue, self.cache, self.logger)
        way_marker.start()

        self._write_elem(import_processes[self.db.insert_data_format]['relation'],
            cache, log, self.pool_size, [inserted_way_queue])

        inserted_way_queue.put(None)
        way_marker.join()

    def ways(self):
        cache = self.cache.ways_cache()
        log = self.logger('ways', len(cache))
        self._write_elem(import_processes[self.db.insert_data_format]['way'],
            cache, log, self.pool_size)
        self.cache.remove_inserted_way_cache()

    def nodes(self):
        cache = self.cache.nodes_cache()
        log = self.logger('nodes', len(cache))
        self._write_elem(import_processes[self.db.insert_data_format]['node'],
            cache, log, self.pool_size)


class WayMarkerProcess(Process):
    def __init__(self, queue, cache, logger):
        Process.__init__(self)
        self.daemon = True
        self.queue = queue
        self.cache = cache
        self.logger = logger

    def run(self):
        inserted_ways = self.cache.inserted_ways_cache('w')
        while True:
            osmid = self.queue.get()
            if osmid is None:
                break
            inserted_ways.put(osmid)

        inserted_ways.close()

