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
import os
import shapely.geometry
import shapely.geos
import shapely.prepared
from shapely.geometry.base import BaseGeometry
from shapely import geometry
from shapely import wkt
from shapely.ops import cascaded_union, linemerge
from shapely.topology import TopologicalError

try:
    import rtree
except ImportError:
    rtree = None

from imposm import config
from imposm.util.geom import load_polygons, load_datasource, build_multipolygon

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

def tile_bbox(bbox, grid_width):
    """
    Tile bbox into multiple sub-boxes, each of `grid_width` size.

    >>> list(tile_bbox((-1, 1, 0.49, 1.51), 0.5)) #doctest: +NORMALIZE_WHITESPACE
    [(-1.0, 1.0, -0.5, 1.5),
     (-1.0, 1.5, -0.5, 2.0),
     (-0.5, 1.0, 0.0, 1.5),
     (-0.5, 1.5, 0.0, 2.0),
     (0.0, 1.0, 0.5, 1.5),
     (0.0, 1.5, 0.5, 2.0)]
    """
    min_x = math.floor(bbox[0]/grid_width) * grid_width
    min_y = math.floor(bbox[1]/grid_width) * grid_width
    max_x = math.ceil(bbox[2]/grid_width) * grid_width
    max_y = math.ceil(bbox[3]/grid_width) * grid_width

    x_steps = math.ceil((max_x - min_x) / grid_width)
    y_steps = math.ceil((max_y - min_y) / grid_width)

    for x in xrange(int(x_steps)):
        for y in xrange(int(y_steps)):
            yield (
                min_x + x * grid_width,
                min_y + y * grid_width,
                min_x + (x + 1) * grid_width,
                min_y + (y + 1)* grid_width,
            )

def split_polygon_at_grid(geom, grid_width=0.1, current_grid_width=10.0):
    """
    >>> p = list(split_polygon_at_grid(geometry.box(-0.5, 1, 0.2, 2), 1))
    >>> p[0].contains(geometry.box(-0.5, 1, 0, 2))
    True
    >>> p[0].area == geometry.box(-0.5, 1, 0, 2).area
    True
    >>> p[1].contains(geometry.box(0, 1, 0.2, 2))
    True
    >>> p[1].area == geometry.box(0, 1, 0.2, 2).area
    True
    """
    if not geom.is_valid:
        geom = geom.buffer(0)

    for i, split_box in enumerate(tile_bbox(geom.bounds, current_grid_width)):
        try:
            polygon_part = geom.intersection(shapely.geometry.box(*split_box))
        except TopologicalError:
            continue
        if not polygon_part.is_empty and polygon_part.type.endswith('Polygon'):
            if grid_width >= current_grid_width:
                yield polygon_part
            else:
                for part in split_polygon_at_grid(polygon_part, grid_width, current_grid_width/10.0):
                    yield part

def load_geom(source):
    geom = load_datasource(source)
    if geom:
        # get the first and maybe only geometry
        if not check_wgs84_srs(geom[0]):
            log.error('Geometry is not in EPSG:4326')
            return None
        if rtree:
            return LimitRTreeGeometry(geom)
        else:
            log.info('You should install RTree for large --limit-to polygons')
            return LimitPolygonGeometry(build_multipolygon(geom)[1])
    return None

def check_wgs84_srs(geom):
    bbox = geom.bounds
    if bbox[0] >= -180 and bbox[1] >= -90 and bbox[2] <= 180 and bbox[3] <= 90:
        return True
    return False

class EmtpyGeometryError(Exception):
    pass

class LimitPolygonGeometry(object):
    def __init__(self, shapely_geom):
        self._geom = shapely_geom
        self._prepared_geom = None
        self._prepared_counter = 0
        self._prepared_max = 100000

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

        new_geom = filter_geometry_by_type(new_geom, geom.type)
        if new_geom:
            return new_geom

        raise EmtpyGeometryError('No intersection or empty geometry')

def filter_geometry_by_type(geometry, geom_type):
    """
    Filter (multi)geometry for compatible `geom_type`,
    because we can't insert points into linestring tables for example
    """
    if geometry.type == geom_type:
        # same type is fine
        return geometry

    if geometry.type == 'Polygon' and geom_type == 'MultiPolygon':
        # multipolygon mappings also support polygons
        return geometry

    if geometry.type == 'MultiPolygon' and geom_type == 'Polygon':
        # polygon mappings should also support multipolygons
        return geometry

    if hasattr(geometry, 'geoms'):
        # GeometryCollection or MultiLineString? return list of geometries
        geoms = []
        for part in geometry.geoms:
            # only parts with same type
            if part.type == geom_type:
                geoms.append(part)

        if geoms:
            return geoms

    return None

def flatten_polygons(polygons):
    for polygon in polygons:
        if polygon.type == 'MultiPolygon':
            for p in polygon.geoms:
                yield p
        else:
            yield polygon

def flatten_linestrings(linestrings):
    for linestring in linestrings:
        if linestring.type == 'MultiLineString':
            for ls in linestring.geoms:
                yield ls
        else:
            yield linestring

def filter_invalid_linestrings(linestrings):
    for linestring in linestrings:
        # filter out tiny linestrings, can become invalid geometries in postgis
        if linestring.length > 1e-9:
            yield linestring

class LimitRTreeGeometry(object):
    def __init__(self, polygons):
        index = rtree.index.Index()
        sub_polygons = []
        part_idx = 0
        for polygon in polygons:
            for part in split_polygon_at_grid(polygon):
                sub_polygons.append(part)
                index.insert(part_idx, part.bounds)
                part_idx += 1

        self.polygons = sub_polygons
        self.index = index

    def intersection(self, geom):
        intersection_ids = list(self.index.intersection(geom.bounds))

        if not intersection_ids:
            raise EmtpyGeometryError('No intersection or empty geometry')

        intersections = []
        for i in intersection_ids:

            polygon = self.polygons[i]

            if polygon.contains(geom):
                return geom

            if polygon.intersects(geom):
                try:
                    new_geom_part = polygon.intersection(geom)
                    new_geom_part = filter_geometry_by_type(new_geom_part, geom.type)
                    if new_geom_part:
                        if isinstance(new_geom_part, list):
                            intersections.extend(new_geom_part)
                        else:
                            intersections.append(new_geom_part)
                except TopologicalError:
                        pass

        if not intersections:
            raise EmtpyGeometryError('No intersection or empty geometry')

        # intersections from multiple sub-polygons
        # try to merge them back to a single geometry
        try:
            if geom.type.endswith('Polygon'):
                union = cascaded_union(list(flatten_polygons(intersections)))
            elif geom.type.endswith('LineString'):
                linestrings = flatten_linestrings(intersections)
                linestrings = list(filter_invalid_linestrings(linestrings))
                if not linestrings:
                    raise EmtpyGeometryError()
                union = linemerge(linestrings)
                if union.type == 'MultiLineString':
                    union = list(union.geoms)
            elif geom.type == 'Point':
                union = intersections[0]
            else:
                log.warn('unexpexted geometry type %s', geom.type)
                raise EmtpyGeometryError()
        except ValueError, ex:
            # likely an 'No Shapely geometry can be created from null value' error
            log.warn('could not create union: %s', ex)
            raise EmtpyGeometryError()
        return union
