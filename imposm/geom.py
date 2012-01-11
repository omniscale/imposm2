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

import math

import shapely.geos
from shapely.geometry.base import BaseGeometry
from shapely import geometry
from shapely import wkt

from imposm import config

import logging
log = logging.getLogger(__name__)

class InvalidGeometryError(Exception):
    pass

class IncompletePolygonError(Exception):
    pass


TOLERANCE_DEEGREES = 1e-8
TOLERANCE_METERS = 1e-3

# older versions had unhandled floating point execptions in .buffer(0)
SHAPELY_SUPPORTS_BUFFER = shapely.geos.geos_capi_version >= (1, 6, 0)

def validate_and_simplify(geom, meter_units=False):
    if geom.is_empty:
        raise InvalidGeometryError('geometry is empty')

    if SHAPELY_SUPPORTS_BUFFER:
        # buffer(0) is nearly fast as is_valid 
        return geom.buffer(0)
    
    orig_geom = geom
    if not geom.is_valid:
        tolerance = TOLERANCE_METERS if meter_units else TOLERANCE_DEEGREES
        geom = geom.simplify(tolerance, False)
        if not geom.is_valid:
            raise InvalidGeometryError('geometry is invalid, could not simplify: %s' %
                                       orig_geom)
    return geom

class GeomBuilder(object):
    def build(self, osm_elem):
        # TODO is this method still in use?
        try:
            if isinstance(osm_elem.coords, BaseGeometry):
                return osm_elem.coords
            geom_wkt = self.to_wkt(osm_elem.coords)
            if geom_wkt is not None:
                geom = wkt.loads(geom_wkt)
        except Exception, ex:
            raise InvalidGeometryError('unable to build geometry %s: %s %s' %
                                       (osm_elem.osm_id, ex, osm_elem.coords))
        if geom_wkt is None or geom is None:
            # unable to build valid wkt (non closed polygon, etc)
            raise InvalidGeometryError()
        return geom    
    
    def check_geom_type(self, geom):
        return

    def build_geom(self, osm_elem):
        try:
            if isinstance(osm_elem.coords, BaseGeometry):
                if osm_elem.coords.is_empty:
                    raise InvalidGeometryError('empty geometry')
                self.check_geom_type(osm_elem.coords)
                return osm_elem.coords
            geom = self.to_geom(osm_elem.coords)
        except InvalidGeometryError, ex:
            raise InvalidGeometryError('unable to build geometry %s: %s %s' %
                                       (osm_elem.osm_id, ex, osm_elem.coords))
        if geom is None:
            # unable to build valid wkt (non closed polygon, etc)
            raise InvalidGeometryError()
        return geom    

class PointBuilder(GeomBuilder):
    def to_wkt(self, data):
        if len(data) != 2:
            return None
        return 'POINT(%f %f)' % data
    
    def to_geom(self, data):
        if len(data) != 2:
            return None
        return geometry.Point(*data)
    
    def check_geom_type(self, geom):
        if geom.type != 'Point':
            raise InvalidGeometryError('expected Point, got %s' % geom.type)
    
    def build_checked_geom(self, osm_elem, validate=False):
        geom = self.build_geom(osm_elem)
        if not validate or geom.is_valid:
            return geom
        else:
            raise InvalidGeometryError('invalid geometry for %s: %s, %s' %
                                       (osm_elem.osm_id, geom, osm_elem.coords))

class PolygonBuilder(GeomBuilder):
    def to_wkt(self, data):
        if len(data) >= 4 and data[0] == data[-1]:
            return 'POLYGON((' + ', '.join('%f %f' % p for p in data) + '))'
        return None
    
    def to_geom(self, data):
        if len(data) >= 4 and data[0] == data[-1]:
            return geometry.Polygon(data)
        return None
    
    def check_geom_type(self, geom):
        if geom.type not in ('Polygon', 'MultiPolygon'):
            raise InvalidGeometryError('expected Polygon or MultiPolygon, got %s' % geom.type)
    
    def build_checked_geom(self, osm_elem, validate=False):
        geom = self.build_geom(osm_elem)
        if not validate:
            return geom
        try:
            return validate_and_simplify(geom)
        except InvalidGeometryError:
            raise InvalidGeometryError('invalid geometry for %s: %s, %s' %
                                       (osm_elem.osm_id, geom, osm_elem.coords))

class LineStringBuilder(GeomBuilder):
    def to_wkt(self, data):
        if len(data) <= 1:
            return None
        if len(data) == 2 and data[0] == data[1]:
            return None
        return 'LINESTRING(' + ', '.join('%f %f' % p for p in data) + ')'

    def check_geom_type(self, geom):
        if geom.type != 'LineString':
            raise InvalidGeometryError('expected LineString, got %s' % geom.type)

    def to_geom(self, data, max_length=None):
        if len(data) <= 1:
            return None
        if len(data) == 2 and data[0] == data[1]:
            return None
        if max_length is None:
            max_length = config.imposm_linestring_max_length
        if max_length and len(data) > max_length:
            chunks = math.ceil(len(data) / max_length)
            length = int(len(data) // chunks)
            lines = []
            for i in xrange(1, len(data), length):
                lines.append(geometry.LineString(data[i-1:i+length]))
            return lines
        return geometry.LineString(data)

    def build_checked_geom(self, osm_elem, validate=False):
        geom = self.build_geom(osm_elem)
        if not validate or geom.is_valid:
            return geom
        else:
            raise InvalidGeometryError('invalid geometry for %s: %s, %s' %
                                       (osm_elem.osm_id, geom, osm_elem.coords))
