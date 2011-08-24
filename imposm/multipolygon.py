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
import imposm.config
import shapely.geometry
import shapely.ops
import shapely.geos
import shapely.prepared

import logging
log = logging.getLogger(__name__)

def RelationBuilder(*args, **kw):
    if imposm.config.relation_builder == 'contains':
        return ContainsRelationBuilder(*args, **kw)
    if imposm.config.relation_builder == 'union':
        return UnionRelationBuilder(*args, **kw)
    raise ValueError('unknown relation_builder "%s"'
        % (imposm.config.relation_builder, ))

class RelationBuilderBase(object):
    validate_rings = True
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
                if imposm.config.import_partial_relations:
                    continue
                else:
                    raise IncompletePolygonError('way not found %s:%s' % (self.relation.osm_id, member[0]))
            if way.partial_refs:
                log.warn('multiple linestrings in way %s (relation %s)',
                       member[0], self.relation.osm_id)
                raise IncompletePolygonError()
            
            way.coords = self.fetch_way_coords(way)
            if way.coords is None:
                if not imposm.config.import_partial_relations:
                    raise IncompletePolygonError()
            else:
                ways.append(way)
        return ways
    
    def build_rings(self, ways):
        rings = []
        incomplete_rings = []
        
        for ring in (Ring(w) for w in ways):
            if ring.is_closed():
                ring.geom = self.polygon_builder.build_checked_geom(ring, validate=self.validate_rings)
                rings.append(ring)
            else:
                incomplete_rings.append(ring)
        
        merged_rings = self.build_ring_from_incomplete(incomplete_rings)
        if len(rings) + len(merged_rings) == 0:
            raise IncompletePolygonError('linestrings from relation %s have no rings' % (self.relation.osm_id, ))
        
        return rings + merged_rings
        
    def build_ring_from_incomplete(self, incomplete_rings):
        
        rings = merge_rings(incomplete_rings)

        for ring in rings[:]:
            if not ring.is_closed():
                if imposm.config.import_partial_relations:
                    rings.remove(ring)
                    continue
                else:
                    raise InvalidGeometryError('linestrings from relation %s do not form a ring' %
                        self.relation.osm_id)
            ring.geom = self.polygon_builder.build_checked_geom(ring, validate=self.validate_rings)
        return rings
    
    def fetch_way_coords(self, way):
        """
        Fetch all coordinates of way.refs.
        """
        coords = self.coords_cache.get_coords(way.refs)
        if coords is None:
            log.debug('missing coord from way %s in relation %s',
                way.osm_id, self.relation.osm_id)
            return None
        return coords
    
    def build_relation_geometry(self, rings):
        """
        Build relation geometry from rings.
        """
        raise NotImplementedError()
        
    
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

            if (imposm.config.imposm_multipolygon_max_ring
                and len(rings) > imposm.config.imposm_multipolygon_max_ring):
                log.warn('skipping relation %d with %d ways (%.1fms) and %d rings (%.1fms): too many rings',
                    self.relation.osm_id, len(ways), time_ways*1000, len(rings), time_rings*1000)
                raise IncompletePolygonError('skipping too large multipolygon')
            time_start = time.time()
            self.build_relation_geometry(rings)
            time_relations = time.time() - time_start
            
            if time_ways + time_rings + time_relations > imposm.config.imposm_multipolygon_report:
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


class UnionRelationBuilder(RelationBuilderBase):
    def build_relation_geometry(self, rings):
        """
        Build relation geometry from rings.
        """
        rings.sort(key=lambda x: x.geom.area, reverse=True)
        
        # add/subtract all rings from largest
        polygon = rings[0]
        rel_tags = relation_tags(self.relation.tags, polygon.tags)
        polygon.mark_as_inserted(rel_tags)
        
        geom = polygon.geom
        for r in rings[1:]:
            if geom.contains(r.geom):
                # inside -> hole -> subtract
                geom = geom.difference(r.geom)
                r.mark_as_inserted(rel_tags)
            else:
                # outside or overlap -> merge(union) to multipolygon or to polygon
                try:
                    geom = geom.union(r.geom)
                except shapely.geos.TopologicalError:
                    raise InvalidGeometryError('multipolygon relation (%s) result is invalid'
                                               ' (topological error)' % self.relation.osm_id)
                r.mark_as_inserted(rel_tags)
        if not geom.is_valid:
            raise InvalidGeometryError('multipolygon relation (%s) result is invalid' %
                                       self.relation.osm_id)
        
        self.relation.geom = geom
        self.relation.tags = rel_tags
        all_ways = polygon.ways
        for r in rings:
            all_ways.extend(r.ways)
        self.relation.ways = all_ways

class ContainsRelationBuilder(RelationBuilderBase):
    validate_rings = False
    
    def _ring_is_hole(self, rings, idx):
        """
        Returns True if rings[idx] is a hole, False if it is a
        shell (also if hole in a hole, etc)
        """
        contained_counter = 0
        while True:
            idx = rings[idx].contained_by
            if idx is None:
                break
            contained_counter += 1
        
        return contained_counter % 2 == 1
    
    def build_relation_geometry(self, rings):
        """
        Build relation geometry from rings.
        """
        rings.sort(key=lambda x: x.geom.area, reverse=True)
        total_rings = len(rings)

        shells = set([rings[0]])

        for i in xrange(total_rings):
            test_geom = shapely.prepared.prep(rings[i].geom)
            for j in xrange(i+1, total_rings):
                if test_geom.contains(rings[j].geom):
                    # j in inside of i
                    if rings[j].contained_by is not None:
                        # j is inside a larger ring, remove that relationship
                        # e.g. j is hole inside a hole (i)
                        rings[rings[j].contained_by].holes.discard(rings[j])
                        shells.discard(rings[j])
                    
                    # remember parent
                    rings[j].contained_by = i
                    
                    # add ring as hole or shell
                    if self._ring_is_hole(rings, j):
                        rings[i].holes.add(rings[j])
                    else:
                        shells.add(rings[j])
            if rings[i].contained_by is None:
                # add as shell if it is not a hole
                shells.add(rings[i])
        
        rel_tags = relation_tags(self.relation.tags, rings[0].tags)

        # build polygons from rings
        polygons = []
        for shell in shells:
            shell.mark_as_inserted(rel_tags)
            exterior = shell.geom.exterior
            interiors = []
            for hole in shell.holes:
                hole.mark_as_inserted(rel_tags)
                interiors.append(hole.geom.exterior)
            
            polygons.append(shapely.geometry.Polygon(exterior, interiors))
            
        if len(polygons) == 1:
            geom = polygons[0]
        else:
            geom = shapely.geometry.MultiPolygon(polygons)
        
        geom = imposm.geom.validate_and_simplify(geom)
        if not geom.is_valid:
            raise InvalidGeometryError('multipolygon relation (%s) result is invalid' %
                                       self.relation.osm_id)
        self.relation.geom = geom
        self.relation.tags = rel_tags
        all_ways = []
        for r in rings:
            all_ways.extend(r.ways)
        self.relation.ways = all_ways
    

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
        self.inserted = way.inserted
        self.contained_by = None
        self.holes = set()
    
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
    
    def mark_as_inserted(self, tags):
        for w in self.ways:
            if tags_same_or_empty(tags, w.tags):
                w.inserted = True
        if tags_same_or_empty(tags, self.tags):
            self.inserted = True
