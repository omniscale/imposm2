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

import itertools
from imposm.merge import multimerge

__all__ = [
    'Node', 'Way', 'Relation',
]

class Node(object):
    def __init__(self, osm_id, tags, coord):
        self.osm_id = osm_id
        self.tags = tags
        self.coord = coord
    
    def __repr__(self):
        return 'Node(%r, %r, %r)' % (self.osm_id, self.tags, self.coord)

    def merge(self, tags, coord):
        pass

    def to_tuple(self):
        return self.osm_id, self.tags, self.coords

class Way(object):
    def __init__(self, osm_id, tags, refs, inserted=False):
        self.osm_id = osm_id
        self.tags = tags
        self.refs = refs
        self.partial_refs = None
        if refs and isinstance(refs[0], list):
            self.refs = refs[0]
            self.partial_refs = refs
        self.inserted = inserted

    def __repr__(self):
        return 'Way(%r, %r, %r, inserted=%r)' % (self.osm_id, self.tags,
            self.refs, self.inserted)

    def merge(self, tags, refs):
        self.tags.update(tags)

        if self.refs != refs:
            if self.partial_refs:
                merge_refs = []
                merge_refs.extend(self.partial_refs)
            else:
                merge_refs = self.refs
            merge_refs.append(refs)
            result = multimerge(merge_refs)
            if result is None:
                self.partial_refs = merge_refs
            else:
                self.refs = result
                self.partial_refs = None

    def to_tuple(self):
        return self.osm_id, self.tags, self.refs


class Relation(object):
    def __init__(self, osm_id, tags, members):
        self.osm_id = osm_id
        self.tags = tags
        self.members = members

    def merge(self, tags, members):
        self.tags.update(tags)
        if self.members != members:
            self.members = merge_relation_members(self.members, members)

    def to_tuple(self):
        return self.osm_id, self.tags, self.members

def merge_relation_members(a, b):
    """
    concatenate two lists of members, removing duplicates, retaining order
    """
    combined = []
    added_ids = set()
    for m in itertools.chain(a, b):
        if m[0] not in added_ids:
            combined.append(m)
            added_ids.add(m[0])
    return combined


class OSMElem(object):
    __slots__ = 'osm_id name coords cls type tags geom'.split()
    
    def __init__(self, osm_id, coords, type, tags):
        self.osm_id = osm_id
        self.name = tags.get('name')
        self.coords = coords
        self.cls = type[0]
        self.type = type[1]
        self.tags = tags
        self.geom = None