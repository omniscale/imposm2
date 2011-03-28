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

from __future__ import division
import os
import time

from imposm.geom import (
    PolygonBuilder,
    LineStringBuilder,
    InvalidGeometryError,
    IncompletePolygonError,
)
from imposm.merge import merge

import imposm.base
import imposm.geom
import shapely.geometry
import shapely.ops
import shapely.geos
import shapely.prepared


import logging
log = logging.getLogger(__name__)

IMPOSM_MULTIPOLYGON_REPORT = float(os.environ.get('IMPOSM_MULTIPOLYGON_REPORT', 60))
IMPOSM_MULTIPOLYGON_MAX_RING = int(os.environ.get('IMPOSM_MULTIPOLYGON_MAX_RING', 1000))

class RelationBuilder(object):
    def __init__(self, relation, ways_cache, coords_cache):
        self.relation = relation
        self.polygon_builder = PolygonBuilder()
        self.linestring_builder = LineStringBuilder()
        self.ways_cache = ways_cache
        self.coords_cache = coords_cache
    
    def fetch_ways(self):
        ways = []
        for member in self.relation.members:
            # skip label nodes, relations of relations, etc
            if member[1] != 'way': continue
            way = self.ways_cache.get(member[0])
            if way is None:
                log.debug('way not found %s:%s', self.relation.osm_id, member[0])
                raise IncompletePolygonError('way not found %s:%s' % (self.relation.osm_id, member[0]))
            if way.partial_refs:
                log.warn('multiple linestrings in way %s (relation %s)',
                       member[0], self.relation.osm_id)
                raise IncompletePolygonError()
            
            way.coords = self.fetch_way_coords(way)
            ways.append(way)
        return ways
    
    def build_rings(self, ways):
        rings = []
        incomplete_rings = []
        
        for ring in (Ring(w) for w in ways):
            if ring.is_closed():
                ring.geom = self.polygon_builder.build_checked_geom(ring, validate=True)
                rings.append(ring)
            else:
                incomplete_rings.append(ring)
        
        merged_rings = self.build_ring_from_incomplete(incomplete_rings)
        
        return rings + merged_rings
        
    def build_ring_from_incomplete(self, incomplete_rings):
        
        rings = merge_rings(incomplete_rings)
        for ring in rings:
            if not ring.is_closed():
                raise InvalidGeometryError('linestrings from relation %s do not form a ring' %
                        self.relation.osm_id)
            
            ring.geom = self.polygon_builder.build_checked_geom(ring, validate=True)
        return rings
    
    def fetch_way_coords(self, way):
        """
        Fetch all coordinates of way.refs.
        """
        coords = self.coords_cache.get_coords(way.refs)
        if coords is None:
            log.debug('missing coord from way %s in relation %s',
                way.osm_id, self.relation.osm_id)
            raise IncompletePolygonError()
        
        return coords
    
    def build_relation_geometry(self, rings):
        """
        Build relation geometry from rings.
        """
        rings.sort(key=lambda x: x.geom.area, reverse=True)
        
        # add/subtract all rings from largest
        polygon = rings.pop(0)
        polygon.inserted = True
        rel_tags = relation_tags(self.relation.tags, polygon.tags)
        
        geom = polygon.geom
        for r in rings:
            if geom.contains(r.geom):
                # inside -> hole -> subtract
                geom = geom.difference(r.geom)
                if tags_same_or_empty(rel_tags, r.tags):
                    r.inserted = True
                else:
                    r.inserted = False
            else:
                # outside or overlap -> merge(union) to multipolygon or to polygon
                try:
                    geom = geom.union(r.geom)
                except shapely.geos.TopologicalError:
                    raise InvalidGeometryError('multipolygon relation (%s) result is invalid'
                                               ' (topological error)' % self.relation.osm_id)
                r.inserted = True
        if not geom.is_valid:
            raise InvalidGeometryError('multipolygon relation (%s) result is invalid' %
                                       self.relation.osm_id)
        
        self.relation.geom = geom
        self.relation.tags = rel_tags
        all_ways = polygon.ways
        for r in rings:
            all_ways.extend(r.ways)
        self.relation.ways = all_ways
    
    def mark_inserted_ways(self, inserted_ways_queue):
        for w in self.relation.ways:
            if w.inserted:
                inserted_ways_queue.put(w.osm_id)
    
    def build(self):
        try:
            time_start = time.time()
            ways = self.fetch_ways()
            time_ways = time.time() - time_start
            if not ways:
                raise IncompletePolygonError('no ways found')
            time_start = time.time()
            rings = self.build_rings(ways)
            time_rings = time.time() - time_start

            if len(rings) > IMPOSM_MULTIPOLYGON_MAX_RING:
                log.warn('skipping relation %d with %d ways (%.1fms) and %d rings (%.1fms): too many rings',
                    self.relation.osm_id, len(ways), time_ways*1000, len(rings), time_rings*1000)
            
            time_start = time.time()
            self.build_relation_geometry(rings)
            time_relations = time.time() - time_start
            
            if time_ways + time_rings + time_relations > IMPOSM_MULTIPOLYGON_REPORT:
                log.warn('building relation %d with %d ways (%.1fms) and %d rings (%.1fms) took %.1fms',
                    self.relation.osm_id, len(ways), time_ways*1000, len(rings), time_rings*1000, time_relations*1000)
        except InvalidGeometryError, ex:
            log.debug(ex)
            raise IncompletePolygonError(ex)
        except IncompletePolygonError:
            raise
        except Exception, ex:
            log.warn('error while building multipolygon:')
            log.exception(ex)
            raise IncompletePolygonError(ex)

def relation_tags(rel_tags, way_tags):
    result = dict(rel_tags)
    
    if 'type' in result: del result['type']
    if 'name' in result: del result['name']
    
    if not result:
        # use way_tags
        result.update(way_tags)
    else:
        if 'name' in rel_tags:
            # put back name
            result['name'] = rel_tags['name']
        
    return result

def tags_differ(a, b):
    a_ = dict(a)
    a_.pop('name', None)
    b_ = dict(b)
    b_.pop('name', None)
    return a_ != b_

def tags_same_or_empty(a, b):
    return (
        not b or
        not tags_differ(a, b)
    )

def merge_rings(rings):
    """
    Merge rings at the endpoints.
    """
    endpoints = {}
    for ring in rings:
        left = ring.refs[0]
        right = ring.refs[-1]
        orig_ring = None
        insert_endpoint = None
        if left in endpoints:
            orig_ring = endpoints.pop(left)
            if left == orig_ring.refs[-1]:
                orig_ring.refs = orig_ring.refs + ring.refs[1:]
                orig_ring.coords = orig_ring.coords + ring.coords[1:]
            else:
                orig_ring.refs = orig_ring.refs[::-1] + ring.refs[1:]
                orig_ring.coords = orig_ring.coords[::-1] + ring.coords[1:]
            orig_ring.ways.extend(ring.ways)
            orig_ring.tags.update(ring.tags)
            if right in endpoints and endpoints[right] is not orig_ring:
                # close gap
                ring = endpoints.pop(right)
                if right == ring.refs[0]:
                    orig_ring.refs = orig_ring.refs + ring.refs[1:]
                    orig_ring.coords = orig_ring.coords + ring.coords[1:]
                else:
                    orig_ring.refs = orig_ring.refs[:-1] + ring.refs[::-1]
                    orig_ring.coords = orig_ring.coords[:-1] + ring.coords[::-1]
                orig_ring.ways.extend(ring.ways)
                orig_ring.tags.update(ring.tags)
                right  = orig_ring.refs[-1]
                endpoints[right] = orig_ring
            else:
                endpoints[right] = orig_ring
        elif right in endpoints:
            orig_ring = endpoints.pop(right)
            if right == orig_ring.refs[0]:
                orig_ring.refs = ring.refs[:-1] + orig_ring.refs
                orig_ring.coords = ring.coords[:-1] + orig_ring.coords
            else:
                orig_ring.refs = orig_ring.refs[:-1] + ring.refs[::-1]
                orig_ring.coords = orig_ring.coords[:-1] + ring.coords[::-1]
            orig_ring.ways.extend(ring.ways)
            orig_ring.tags.update(ring.tags)
            endpoints[left] = orig_ring
        else:
            endpoints[left] = ring
            endpoints[right] = ring
    return list(set(endpoints.values()))

class Ring(object):
    """
    Represents a ring (i.e. polygon without holes) build from one
    or more ways. Stores references to the building ways.
    """
    def __init__(self, way):
        self.ways = [way]
        self.osm_id = way.osm_id
        self.refs = way.refs
        self.coords = way.coords
        self.tags = dict(way.tags)
        self._inserted = way
    
    def __repr__(self):
        return 'Ring(%r, %r, %r)' % (self.osm_id, self.tags, self.ways)
    
    def merge(self, ring, without_refs=False):
        """
        Try to merge `ring.refs` with this ring.
        Returns `self` on success, else `None`.
        """
        if without_refs:
            result = None
        else:
            result = merge(self.refs, ring.refs)
            if result is None:
                return None
        
        self.ways.extend(ring.ways)
        self.refs = [result]
        self.tags.update(ring.tags)
        return self
    
    def is_closed(self):
        return len(self.refs) >= 4 and self.refs[0] == self.refs[-1]
    
    def _set_inserted(self, value):
        for w in self.ways:
            w.inserted = value
        self._inserted = value
    
    def _get_inserted(self):
        return self._inserted
    
    # propagate inserted to ways
    inserted = property(_get_inserted, _set_inserted)
