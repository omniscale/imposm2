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

import os

import imposm.config

from . tc import DeltaCoordsDB, CoordDB, NodeDB, WayDB, InsertedWayDB, RelationDB

class OSMCache(object):
    def __init__(self, path, prefix='imposm_', suffix='.cache'):
        self.path = path
        self.prefix = prefix
        self.suffix = suffix
        self.coords_fname = os.path.join(path, prefix + 'coords' + suffix) 
        self.nodes_fname = os.path.join(path, prefix + 'nodes' + suffix) 
        self.ways_fname = os.path.join(path, prefix + 'ways' + suffix) 
        self.inserted_ways_fname = os.path.join(path, prefix + 'inserted_ways' + suffix) 
        self.relations_fname = os.path.join(path, prefix + 'relations' + suffix) 
        self.caches = {}

    def close_all(self):
        for mode_, cache in self.caches.values():
            cache.close()
        self.caches = {}

    def coords_cache(self, mode='r', estimated_records=None):
        if imposm.config.imposm_compact_coords_cache:
            coords_db = DeltaCoordsDB
        else:
            coords_db = CoordDB
        return self._x_cache(self.coords_fname, coords_db, mode, estimated_records)

    def nodes_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.nodes_fname, NodeDB, mode, estimated_records)

    def ways_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.ways_fname, WayDB, mode, estimated_records)

    def inserted_ways_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.inserted_ways_fname, InsertedWayDB, mode, estimated_records)

    def remove_inserted_way_cache(self):
        if os.path.exists(self.inserted_ways_fname):
            os.unlink(self.inserted_ways_fname)

    def relations_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.relations_fname, RelationDB, mode, estimated_records)

    def _x_cache(self, x, x_class, mode, estimated_records=None):
        if x in self.caches:
            current_mode, cache = self.caches[x]
            if current_mode == mode:
                return cache
            else:
                cache.close()
        cache = x_class(x, mode, estimated_records=estimated_records)
        self.caches[x] = mode, cache

        return cache
