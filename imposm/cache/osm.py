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

from . tc import CoordDB, NodeDB, WayDB, RelationDB, DeltaCoordsDB

class OSMCache(object):
    def __init__(self, path, suffix='imposm_', prefix='.cache'):
        self.path = path
        self.suffix = suffix
        self.prefix = prefix
        self.coords_fname = os.path.join(path, suffix + 'coords' + prefix) 
        self.nodes_fname = os.path.join(path, suffix + 'nodes' + prefix) 
        self.ways_fname = os.path.join(path, suffix + 'ways' + prefix) 
        self.relations_fname = os.path.join(path, suffix + 'relations' + prefix) 
        self.caches = {}

    def close_all(self):
        for mode_, cache in self.caches.values():
            cache.close()
        self.caches = {}

    def coords_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.coords_fname, DeltaCoordsDB, mode, estimated_records)

    def nodes_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.nodes_fname, NodeDB, mode, estimated_records)

    def ways_cache(self, mode='r', estimated_records=None):
        return self._x_cache(self.ways_fname, WayDB, mode, estimated_records)

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