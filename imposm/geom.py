# Copyright 2011, 2012 Omniscale (http://omniscale.com)
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
import codecs
import shapely.geometry
import shapely.geos
import shapely.prepared
from shapely.geometry.base import BaseGeometry
from shapely import geometry
from shapely import wkt
from shapely.topology import TopologicalError

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
    if SHAPELY_SUPPORTS_BUFFER:
        try:
            # buffer(0) is nearly fast as is_valid
            return geom.buffer(0)
        except ValueError:
            # shapely raises ValueError if buffer(0) result is empty
            raise InvalidGeometryError('geometry is empty')

    orig_geom = geom
    if not geom.is_valid:
        tolerance = TOLERANCE_METERS if meter_units else TOLERANCE_DEEGREES
        try:
            geom = geom.simplify(tolerance, False)
        except ValueError:
            # shapely raises ValueError if buffer(0) result is empty
            raise InvalidGeometryError('geometry is empty')

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

def load_wkt_polygon(wkt_files):
    """
    Loads WKT polygons from one or more text files.

    Returns the bbox and a Shapely MultiPolygon with
    the loaded geometries.
    """
    polygons = []
    if isinstance(wkt_files, basestring):
        wkt_files = [wkt_files]

    for geom_file in wkt_files:
        # open with utf-8-sig encoding to get rid of UTF8 BOM from MS Notepad
        with codecs.open(geom_file, encoding='utf-8-sig') as f:
            polygons.extend(load_polygon_lines(f, source=wkt_files))

    mp = shapely.geometry.MultiPolygon(polygons)
    # TODO check epsg code?
    return LimitPolygonGeometry(mp)

def load_polygon_lines(line_iter, source='<string>'):
    polygons = []
    for line in line_iter:
        geom = shapely.wkt.loads(line)
        if geom.type == 'Polygon':
            polygons.append(geom)
        elif geom.type == 'MultiPolygon':
            for p in geom:
                polygons.append(p)
        else:
            log.warn('ignoring non-polygon geometry (%s) from %s',
                geom.type, source)

    return polygons

class EmtpyGeometryError(Exception):
    pass

class LimitPolygonGeometry(object):
    def __init__(self, shapely_geom):
        self._geom = shapely_geom
        self._prepared_geom = None
        self._prepared_counter = 0
        self._prepared_max = 10000

    @property
    def geom(self):
        # GEOS internal data structure for prepared geometries grows over time,
        # recreate to limit memory consumption
        if not self._prepared_geom or self._prepared_counter > self._prepared_max:
            self._prepared_geom = shapely.prepared.prep(self._geom)
            self._prepared_counter = 0
        self._prepared_counter += 1
        return self._prepared_geom

    def intersection(self, geom):
        if self.geom.contains_properly(geom):
            # no need to limit contained geometries
            return geom

        new_geom = None
        if self.geom.intersects(geom):
            try:
                # can not use intersection with prepared geom
                new_geom = self._geom.intersection(geom)
            except TopologicalError:
                    pass

        if not new_geom or new_geom.is_empty:
            raise EmtpyGeometryError('No intersection or empty geometry')

        # we can't return results where the geometry type missmatches,
        # because we can't insert points into linestring tables for example

        if new_geom.type == geom.type:
            # same type is fine
            return new_geom

        if new_geom.type == 'MultiPolygon' and geom.type == 'Polygon':
            # polygon mappings should also support multipolygons
            return new_geom

        if hasattr(new_geom, 'geoms'):
            # geometry collection? return list of geometries
            geoms = []
            for part in new_geom.geoms:
                # only parts with same type
                if part.type == geom.type:
                    geoms.append(part)

            if geoms:
                return geoms

        raise EmtpyGeometryError('No intersection or empty geometry')
