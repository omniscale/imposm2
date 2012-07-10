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

from functools import partial
from multiprocessing import Process, JoinableQueue

from imposm.parser import OSMParser
from imposm.util import setproctitle

class ImposmReader(object):
    def __init__(self, mapping, cache, pool_size=2, merge=False, logger=None):
        self.pool_size = pool_size
        self.mapper = mapping
        self.merge = merge
        self.cache = cache
        self.reader = None
        self.logger = logger
        self.estimated_coords = 0

    def read(self, filename):
        nodes_queue = JoinableQueue(128)
        coords_queue = JoinableQueue(512)
        ways_queue = JoinableQueue(128)
        relations_queue = JoinableQueue(128)

        log_proc = self.logger()
        log_proc.start()

        marshal = True
        if self.merge:
            # merging needs access to unmarshaled data
            marshal = False

        estimates = {
            'coords': self.estimated_coords,
            'nodes': self.estimated_coords//50,
            'ways': self.estimated_coords//7,
            'relations': self.estimated_coords//1000,
        }

        coords_writer = CacheWriterProcess(coords_queue, self.cache.coords_cache,
            estimates['coords'], log=partial(log_proc.log, 'coords'),
            marshaled_data=marshal)
        coords_writer.start()

        nodes_writer = CacheWriterProcess(nodes_queue, self.cache.nodes_cache,
            estimates['nodes'], log=partial(log_proc.log, 'nodes'),
            marshaled_data=marshal)
        nodes_writer.start()


        ways_writer = CacheWriterProcess(ways_queue, self.cache.ways_cache,
            estimates['ways'], merge=self.merge, log=partial(log_proc.log, 'ways'),
            marshaled_data=marshal)
        ways_writer.start()

        relations_writer = CacheWriterProcess(relations_queue, self.cache.relations_cache,
            estimates['relations'], merge=self.merge, log=partial(log_proc.log, 'relations'),
            marshaled_data=marshal)
        relations_writer.start()

        log_proc.message('coords: %dk nodes: %dk ways: %dk relations: %dk (estimated)' % (
            estimates['coords']/1000, estimates['nodes']/1000, estimates['ways']/1000,
            estimates['relations']/1000)
        )

        # keep one CPU free for writer proc on hosts with 4 or more CPUs
        pool_size = self.pool_size if self.pool_size < 4 else self.pool_size - 1

        parser = OSMParser(pool_size, nodes_callback=nodes_queue.put, coords_callback=coords_queue.put,
            ways_callback=ways_queue.put, relations_callback=relations_queue.put, marshal_elem_data=marshal)

        parser.nodes_tag_filter = self.mapper.tag_filter_for_nodes()
        parser.ways_tag_filter = self.mapper.tag_filter_for_ways()
        parser.relations_tag_filter = self.mapper.tag_filter_for_relations()

        parser.parse(filename)

        coords_queue.put(None)
        nodes_queue.put(None)
        ways_queue.put(None)
        relations_queue.put(None)
        coords_writer.join()
        nodes_writer.join()
        ways_writer.join()
        relations_writer.join()
        log_proc.stop()
        log_proc.join()


class CacheWriterProcess(Process):
    def __init__(self, queue, cache, estimated_records=None, merge=False, log=None,
        marshaled_data=False):
        Process.__init__(self)
        self.daemon = True
        setproctitle('imposm writer')
        self.queue = queue
        self.cache = cache
        self.merge = merge
        self.log = log
        self.marshaled_data = marshaled_data
        self.estimated_records = estimated_records

    def run(self):
        # print 'creating %s (%d)' % (self.filename, self.estimated_records or 0)
        cache = self.cache(mode='w', estimated_records=self.estimated_records)
        if self.marshaled_data:
            cache_put = cache.put_marshaled
        else:
            cache_put = cache.put
        while True:
            data = self.queue.get()
            if data is None:
                self.queue.task_done()
                break
            if self.merge:
                for d in data:
                    if d[0] in cache:
                        elem = cache.get(d[0])
                        elem.merge(*d[1:])
                        d = elem.to_tuple()
                    cache_put(*d)
            else:
                for d in data:
                    cache_put(*d)
            if self.log:
                self.log(len(data))
            self.queue.task_done()
        cache.close()


