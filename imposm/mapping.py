# -:- encoding: UTF8 -:-
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
import imposm.geom

ANY = '__any__'

__all__ = [
    'LineStrings',
    'Polygons',
    'Points',
    'Options',
    'PolygonTable',
    'ZOrder',
    'PointTable',
    'String',
    'LocalizedName',
    'LineStringTable',
    'Direction',
    'OneOfInt',
    'Integer',
    'WayZOrder',
    'Bool',
    'GeneralizedTable',
    'UnionView',
    'set_default_name_field',
]

default_name_field = None

def set_default_name_type(type, column_name='name'):
    """
    Set new default type for 'name' field.
    """
    global default_name_field
    default_name_field = column_name, type

# changed by imposm.app if the projection is epsg:4326
import_srs_is_geographic = False

def meter_to_mapunit(meter):
    """
    Convert ``meter`` into the mapunit of the import.
    Only supports EPSG:4326 (degrees) at the moment, all other
    SRS will use meter as mapunit.
    """
    if import_srs_is_geographic:
        deg_to_meter = (40000 * 1000) / 360
        return meter / deg_to_meter
    return meter

def sqr_meter_to_mapunit(sqr_meter):
    """
    Convert ``sqr_meter`` into the mapunit of the import.
    Only supports EPSG:4326 (degrees) at the moment, all other
    SRS will use meter as mapunit.
    """
    if import_srs_is_geographic:
        return meter_to_mapunit(math.sqrt(sqr_meter))**2
    return sqr_meter

class Mapping(object):
    table = None
    fields = ()
    field_filter = ()
    classname = None
    _insert_stmt = None
    
    def __init__(self, name, mapping, fields=None, field_filter=None):
        self.name = name
        self.mapping = mapping
        self.fields = fields or tuple(self.fields)
        self._add_name_field()
        if field_filter:
            self.field_filter = field_filter

    def _add_name_field(self):
        """
        Add name field to default if not set.
        """
        if not any(1 for name, _type in self.fields if name == 'name'):
            if default_name_field:
                self.fields = (default_name_field,) + self.fields
            else:
                self.fields = (('name', Name()),) + self.fields
        
    @property
    def insert_stmt(self):
        if not self._insert_stmt:
            self._insert_stmt = self.table('osm_' + self.name, self).insert_stmt
        return self._insert_stmt
    
    def extra_field_names(self):
        extra_field_names = []
        for field_name, field_filter in self.field_filter:
            extra_field_names.append(field_name)
        
        for field_name, field in self.fields:
            field_names = field.extra_fields()
            if field_names is not None:
                extra_field_names.extend(field_names)
            else:
                extra_field_names.append(field_name)
        return extra_field_names
    
    def build_geom(self, osm_elem):
        try:
            geom = self.geom_builder.build_checked_geom(osm_elem)
            osm_elem.geom = geom
        except imposm.geom.InvalidGeometryError, ex:
            raise DropElem('invalid geometry: %s' % (ex, ))
    
    def field_values(self, osm_elem):
        return [t.value(osm_elem.tags.get(n), osm_elem) for n, t in self.fields]
    
    def filter(self, osm_elem):
        [t.filter(osm_elem.tags.get(n), osm_elem) for n, t in self.field_filter]
    
    def __repr__(self):
        return '<Mapping for %s>' % self.name


class TagMapper(object):
    def __init__(self, mappings):
        self.mappings = mappings
        self._init_map()

    def _init_map(self):
        self.point_mappings = {}
        self.line_mappings = {}
        self.polygon_mappings = {}
        self.point_tags = {}
        self.line_tags = {}
        self.polygon_tags = {}

        for mapping in self.mappings:
            if mapping.table is PointTable:
                tags = self.point_tags
                add_to = self.point_mappings
            elif mapping.table is LineStringTable:
                tags = self.line_tags
                add_to = self.line_mappings
            elif mapping.table is PolygonTable:
                tags = self.polygon_tags
                add_to = self.polygon_mappings
            
            for extra in mapping.extra_field_names():
                tags.setdefault(extra, set()).add('__any__')

            for tag, types in mapping.mapping.iteritems():
                add_to.setdefault(tag, {})
                for type in types:
                    tags.setdefault(tag, set()).add(type)
                    add_to[tag].setdefault(type, []).append(mapping)

    def for_nodes(self, tags):
        return self._mapping_for_tags(self.point_mappings, tags)

    def for_ways(self, tags):
        return (self._mapping_for_tags(self.line_mappings, tags) + 
                self._mapping_for_tags(self.polygon_mappings, tags))

    def for_relations(self, tags):
        return self._mapping_for_tags(self.polygon_mappings, tags)

    def _tag_filter(self, filter_tags):
        def filter(tags):
            for k in tags.keys():
                if k not in filter_tags:
                    del tags[k]
                else:
                    if '__any__' in filter_tags[k]:
                        pass
                    elif tags[k] in filter_tags[k]:
                        pass
                    else:
                        del tags[k]
            if 'name' in tags and len(tags) == 1:
                del tags['name']
        return filter

    def tag_filter_for_nodes(self):
        tags = dict(self.point_tags)
        return self._tag_filter(tags)

    def tag_filter_for_ways(self):
        tags = dict()
        for k, v in self.line_tags.iteritems():
            tags.setdefault(k, set()).update(v)
        
        for k, v in self.polygon_tags.iteritems():
            tags.setdefault(k, set()).update(v)
        return self._tag_filter(tags)

    def tag_filter_for_relations(self):
        tags = dict()
        for k, v in self.line_tags.iteritems():
            tags.setdefault(k, set()).update(v)
        for k, v in self.polygon_tags.iteritems():
            tags.setdefault(k, set()).update(v)
        tags['type'] = set(['multipolygon', 'boundary'])  # for type=multipolygon
        expected_tags = set(['type', 'name'])
        _rel_filter = self._tag_filter(tags)
        def rel_filter(tags):
            if tags.get('type') == 'multipolygon':
                pass
            elif tags.get('type') == 'boundary' and 'boundary' in tags:
                # a lot of the boundary relations are not multipolygon
                pass
            else:
                tags.clear()
                return
            tag_count = len(tags)
            _rel_filter(tags)
            if len(tags) < tag_count:
                # we removed tags...
                if not set(tags).difference(expected_tags):
                    # but no tags except name and type are left
                    # remove all, otherwise tags from longest
                    # way/ring would be used during MP building
                    tags.clear()
        return rel_filter

    def _mapping_for_tags(self, tag_map, tags):
        result = []
        mapping_set = set()

        for tag_name in tags:
            if tag_name in tag_map:
                tag_value = tags[tag_name]
                mappings = []
                if tag_value in tag_map[tag_name]:
                    mappings.extend(tag_map[tag_name][tag_value])
                elif ANY in tag_map[tag_name]:
                    mappings.extend(tag_map[tag_name][ANY])

                new_mappings = []
                for proc in mappings:
                    if proc not in mapping_set:
                        mapping_set.add(proc)
                        new_mappings.append(proc)
                if new_mappings:
                    result.append(((tag_name, tag_value), tuple(new_mappings)))
        
        return result


# marker classes
class PointTable(object):
    pass
class LineStringTable(object):
    pass
class PolygonTable(object):
    pass

class Points(Mapping):
    """
    Table class for point features.
    
    :PostGIS datatype: POINT (for multi-polygon support)
    """
    table = PointTable
    geom_builder = imposm.geom.PointBuilder()
    geom_type = 'POINT'

class LineStrings(Mapping):
    """
    Table class for line string features.
    
    :PostGIS datatype: LINESTRING (for multi-polygon support)
    """
    table = LineStringTable
    geom_builder = imposm.geom.LineStringBuilder()
    geom_type = 'LINESTRING'

class Polygons(Mapping):
    """
    Table class for polygon features.
    
    :PostGIS datatype: GEOMETRY (for multi-polygon support)
    """
    table = PolygonTable
    geom_builder = imposm.geom.PolygonBuilder()
    geom_type = 'GEOMETRY' # for multipolygon support


class GeneralizedTable(object):
    def __init__(self, name, tolerance, origin, where=None):
        self.name = name
        self.tolerance = tolerance
        self.origin = origin
        self.classname = origin.name
        self.fields = self.origin.fields
        self.where = where

class UnionView(object):
    def __init__(self, name, mappings, fields):
        self.name = name
        self.mappings = mappings
        self.fields = fields

class DropElem(Exception):
    pass


class FieldType(object):
    def extra_fields(self):
        """
        List with names of fields (keys) that should be processed
        during read-phase.
        
        Return ``None`` to use the field name from the mapping.
        Return ``[]`` if no extra fields (keys) are required.
        """
        return None
    
    def value(self, val, osm_elem):
        return val

class String(FieldType):
    """
    Field for string values.
    
    :PostgreSQL datatype: VARCHAR(255)
    """
    column_type = "VARCHAR(255)"

class Name(String):
    """
    Field for name values.
    
    Filters out common FixMe values.
    
    :PostgreSQL datatype: VARCHAR(255)
    """
    
    filter_out_names = set((
        'fixme', 'fix me', 'fix-me!',
        '0', 'none', 'n/a', 's/n',
        'kein name', 'kein',
        'unbenannt', 'unbekannt',
        'noch unbekannt', 'noch ohne namen',
        'noname', 'unnamed', 'namenlos', 'no_name', 'no name',
        'editme', '_edit_me_',
    ))

    def value(self, val, osm_elem):
        if val and val.lower() in self.filter_out_names:
            osm_elem.name = ''
            val = ''
        return val

class LocalizedName(Name):
    """
    Field for name values.
    
    :PostgreSQL datatype: VARCHAR(255)
    """
    def __init__(self, coalesce=['name', 'int_name']):
        self.coalesce_keys = coalesce
    
    def extra_fields(self):
        return self.coalesce_keys
    
    def value(self, val, osm_elem):
        for key in self.coalesce_keys:
            val = osm_elem.tags.get(key)
            if val and val.lower() not in self.filter_out_names:
                osm_elem.name = val
                return val
        else:
            osm_elem.name = ''
            return ''

class Bool(FieldType):
    """
    Field for boolean values.
    Converts false, no, 0 to False and true, yes, 1 to True.
    
    :PostgreSQL datatype: SMALLINT
    """
    # there was a reason this is not BOOL
    # something didn't supported it, cascadenik? don't remember
    column_type = "SMALLINT"

    aliases = {
        True: set(['false', 'no', '0', 'undefined']),
        False: set(['true', 'yes', '1', 'undefined']),
    }

    def __init__(self, default=True, neg_aliases=None):
        self.default = default
        self.neg_aliases = neg_aliases or self.aliases[default]

    def value(self, val, osm_elem):
        if val is None or val.strip().lower() in self.neg_aliases:
            return 0  # not self.default
        return 1  # self.default

    def filter(self, val, osm_elem):
        if self.value(val, osm_elem):
            raise DropElem

class Direction(FieldType):
    """
    Field type for one-way directions.
    Converts `yes`, `true` and `1` to ``1`` for one ways in the direction of
    the way, `-1` to ``-1`` for one ways against the direction of the way and
    ``0`` for all other values.
    
    :PostgreSQL datatype: SMALLINT
    """
    column_type = "SMALLINT"
    def value(self, value, osm_elem):
        if value:
            value = value.strip().lower()
            if value in ('yes', 'true', '1'):
                return 1
            if value == '-1':
                return -1
        return 0

class PseudoArea(FieldType):
    """
    Field for the (pseudo) area of a polygon in square meters.
    
    The value is just an approximation since the geometries are in
    EPSG:4326 and not in a equal-area projection. The approximation
    is good for smaller polygons (<1%) and should be precise enough
    to compare geometries for rendering order (larger below smaller).
    
    The area of the geometry is multiplied by the cosine of
    the mid-latitude to compensate the reduced size towards
    the poles.
    
    :PostgreSQL datatype: REAL
    
    .. versionadded:: 2.2.1
    """
    
    column_type = "REAL"
    
    def value(self, val, osm_elem):
        area = osm_elem.geom.area
        if not area:
            return None
        
        extent = osm_elem.geom.bounds
        mid_lat = extent[1] + (abs(extent[3] - extent[1]) / 2)
        sqr_deg = area * math.cos(math.radians(mid_lat))
        
        # convert deg^2 to m^2
        sqr_m = (math.sqrt(sqr_deg) * (40075160 / 360))**2
        return sqr_m
    
    def extra_fields(self):
        return []

class OneOfInt(FieldType):
    """
    Field type for integer values.
    Converts values to integers, drops element if is not included in
    ``values``.
    
    :PostgreSQL datatype: SMALLINT
    """
    column_type = "SMALLINT"

    def __init__(self, values):
        self.values = set(values)

    def value(self, value, osm_elem):
        if value in self.values:
            return int(value)
        raise DropElem

class Integer(FieldType):
    """
    Field type for integer values.
    Converts values to integers, defaults to ``NULL``.
    
    :PostgreSQL datatype: INTEGER
    """
    column_type = "INTEGER"

    def value(self, value, osm_elem):
        try:
            return int(value)
        except:
            return None

class ZOrder(FieldType):
    """
    Field type for z-ordering based on the feature type.
    
    :param types: list of mapped feature types,
        from highest to lowest ranking
    :PostgreSQL datatype: SMALLINT
    """
    
    column_type = "SMALLINT"

    def __init__(self, types):
        self.rank = {}
        for i, t in enumerate(types[::-1]):
            self.rank[t] = i

    def extra_fields(self):
        return []

    def value(self, val, osm_elem):
        return self.rank.get(osm_elem.type, 0)


class WayZOrder(FieldType):
    """
    Field type for z-ordered based on highway types.
    
    Ordering based on the osm2pgsql z-ordering:
    From ``roads`` = 3 to ``motorways`` = 9, ``railway`` = 7 and unknown = 0.
    Ordering changes with ``tunnels`` by -10, ``bridges`` by +10 and
    ``layer`` by 10 * ``layer``.
    
    :PostgreSQL datatype: SMALLINT
    """

    column_type = "SMALLINT"

    rank = {
     'minor': 3,
     'road': 3,
     'unclassified': 3,
     'residential': 3,
     'tertiary_link': 3,
     'tertiary': 4,
     'secondary_link': 3,
     'secondary': 5,
     'primary_link': 3,
     'primary': 6,
     'trunk_link': 3,
     'trunk': 8,
     'motorway_link': 3,
     'motorway': 9,
    }

    brunnel_bool = Bool()
    
    def extra_fields(self):
        return []

    def value(self, val, osm_elem):
        tags = osm_elem.tags
        z_order = 0
        l = self.layer(tags)
        z_order += l * 10
        r = self.rank.get(osm_elem.type, 0)
        if not r:
            r = 7 if 'railway' in tags else 0
        z_order += r

        if self.brunnel_bool.value(tags.get('tunnel'), {}):
            z_order -= 10

        if self.brunnel_bool.value(tags.get('bridge'), {}):
            z_order += 10

        return z_order

    def layer(self, tags):
        l = tags.get('layer', 0)
        try:
            return int(l)
        except ValueError:
            return 0

class Options(dict):
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('%s not in %r' % (name, self))
