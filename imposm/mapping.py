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
    'LineStringTable',
    'Direction',
    'OneOfInt',
    'Integer',
    'WayZOrder',
    'Bool',
    'GeneralizedTable',
    'UnionView',
]


class Mapping(object):
    table = None
    fields = ()
    field_filter = ()
    classname = None
    _insert_stmt = None
    
    filter_out_names = set((
        'fixme', 'fix me', 'fix-me!',
        'kein name', 'kein',
        'unbenannt', 'unbekannt',
        'noch unbekannt', 'noch ohne namen',
        'noname', 'unnamed', 'namenlos', 'no_name', 'no name',
    ))
    
    def __init__(self, name, mapping, fields=None, field_filter=None):
        self.name = name
        self.mapping = mapping
        if fields:
            self.fields = fields
        if field_filter:
            self.field_filter = field_filter
        
    @property
    def insert_stmt(self):
        if not self._insert_stmt:
            self._insert_stmt = self.table('osm_' + self.name, self).insert_stmt
        return self._insert_stmt
    
    def name_filter(self, osm_elem):
        if osm_elem.name and osm_elem.name.lower() in self.filter_out_names:
            osm_elem.name = ''
    
    def extra_field_names(self):
        return [n for n,_ in self.fields] + [n for n,_ in self.field_filter]
    
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
        self.points = {}
        self.lines = {}
        self.polygons = {}
        self.nodes_tags = set()
        self.ways_tags = set()

        for mapping in self.mappings:
            if mapping.table is PointTable:
                tags = self.nodes_tags
                add_to = self.points
            elif mapping.table is LineStringTable:
                tags = self.ways_tags
                add_to = self.lines
            elif mapping.table is PolygonTable:
                tags = self.ways_tags
                add_to = self.polygons

            tags.update(mapping.extra_field_names())

            for tag, types in mapping.mapping.iteritems():
                add_to.setdefault(tag, {})
                tags.add(tag)
                for type in types:
                    add_to[tag].setdefault(type, [])
                    add_to[tag][type].append(mapping)

    def for_nodes(self, tags):
        return self._mapping_for_tags(self.points, tags)

    def for_ways(self, tags):
        return (self._mapping_for_tags(self.lines, tags) + 
                self._mapping_for_tags(self.polygons, tags))

    def for_relations(self, tags):
        return self._mapping_for_tags(self.polygons, tags)

    def _tag_filter(self, filter_tags):
        filter_tags['name'] = {'__any__': []}
        def filter(tags):
            for k in tags.keys():
                if k not in filter_tags:
                    del tags[k]
                else:
                    if tags[k] not in filter_tags[k] and '__any__' not in filter_tags[k]:
                        del tags[k]
            if 'name' in tags and len(tags) == 1:
                del tags['name']
        return filter

    def tag_filter_for_nodes(self):
        tags = dict(self.points)
        return self._tag_filter(tags)

    def tag_filter_for_ways(self):
        tags = dict(self.lines)
        tags.update(self.polygons)
        return self._tag_filter(tags)

    def tag_filter_for_relations(self):
        relation_tags = dict(self.lines)
        relation_tags.update(self.polygons)
        relation_tags['type'] = 'multipolygon'  # for type=multipolygon
        _rel_filter = self._tag_filter(relation_tags)
        def rel_filter(tags):
            if tags.get('type') != 'multipolygon':
                tags.clear()
                return
            _rel_filter(tags)
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
    def __init__(self, name, tolerance, origin):
        self.name = name
        self.tolerance = tolerance
        self.origin = origin
        self.classname = origin.name
        self.fields = self.origin.fields

class UnionView(object):
    def __init__(self, name, mappings, fields):
        self.name = name
        self.mappings = mappings
        self.fields = fields

class DropElem(Exception):
    pass


class FieldType(object):
    def value(self, val, osm_elem):
        return val

class String(FieldType):
    """
    Field for string values.
    
    :PostgreSQL datatype: VARCHAR(255)
    """
    column_type = "VARCHAR(255)"

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
