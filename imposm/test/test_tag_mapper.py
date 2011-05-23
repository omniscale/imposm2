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
import imposm
from imposm.mapping import TagMapper

from nose.tools import eq_

class TestTagMapper(object):
    def __init__(self):
        mapping_file = os.path.join(os.path.dirname(__file__), '..',
            'defaultmapping.py')
        mappings = {}
        execfile(mapping_file, mappings)
        self.tag_mapping = TagMapper([m for n, m in mappings.iteritems() 
            if isinstance(m, imposm.mapping.Mapping)])
    
    def test_tag_filter_nodes(self):
        tag_filter_for_nodes = self.tag_mapping.tag_filter_for_nodes()
        tagfilter = lambda x: tag_filter_for_nodes(x) or x
        
        eq_(tagfilter({'name': 'foo'}), {})
        eq_(tagfilter({'name': 'foo', 'unknown': 'baz'}), {})
        eq_(tagfilter({'name': 'foo', 'place': 'unknown'}), {})
        eq_(tagfilter({'name': 'foo', 'place': 'village'}), {'name': 'foo', 'place': 'village'})
        eq_(tagfilter({'name': 'foo', 'place': 'village', 'highway': 'unknown'}),
            {'name': 'foo', 'place': 'village'})
        eq_(tagfilter({'name': 'foo', 'place': 'village', 'highway': 'bus_stop'}),
            {'name': 'foo', 'place': 'village', 'highway': 'bus_stop'})

    def test_tag_filter_ways(self):
        tag_filter_for_ways = self.tag_mapping.tag_filter_for_ways()
        tagfilter = lambda x: tag_filter_for_ways(x) or x
        
        eq_(tagfilter({'name': 'foo'}), {})
        eq_(tagfilter({'name': 'foo', 'unknown': 'baz'}), {})
        eq_(tagfilter({'name': 'foo', 'highway': 'unknown'}), {})
        eq_(tagfilter({'name': 'foo', 'highway': 'track'}), {'name': 'foo', 'highway': 'track'})
        eq_(tagfilter({'name': 'foo', 'place': 'village', 'highway': 'track'}),
            {'name': 'foo', 'highway': 'track'})
        eq_(tagfilter({'name': 'foo', 'railway': 'tram', 'highway': 'secondary'}),
            {'name': 'foo', 'railway': 'tram', 'highway': 'secondary'})

        # with __any__ value
        eq_(tagfilter({'name': 'foo', 'building': 'yes'}),
            {'name': 'foo', 'building': 'yes'})
        eq_(tagfilter({'name': 'foo', 'building': 'whatever'}),
            {'name': 'foo', 'building': 'whatever'})

    def test_tag_filter_relations(self):
        tag_filter_for_relations = self.tag_mapping.tag_filter_for_relations()
        tagfilter = lambda x: tag_filter_for_relations(x) or x
        
        eq_(tagfilter({'name': 'foo'}), {})
        eq_(tagfilter({'name': 'foo', 'unknown': 'baz'}), {})
        eq_(tagfilter({'name': 'foo', 'landuse': 'unknown'}), {})
        eq_(tagfilter({'name': 'foo', 'landuse': 'farm'}), {})
        eq_(tagfilter({'name': 'foo', 'landuse': 'farm', 'type': 'multipolygon'}),
            {'name': 'foo', 'landuse': 'farm', 'type': 'multipolygon'})
        eq_(tagfilter({'name': 'foo', 'landuse': 'unknown', 'type': 'multipolygon'}), {})
        eq_(tagfilter({'name': 'foo', 'landuse': 'farm', 'boundary': 'administrative', 'type': 'multipolygon'}),
            {'name': 'foo', 'landuse': 'farm', 'boundary': 'administrative', 'type': 'multipolygon'})
        
        # boundary relation for boundary
        eq_(tagfilter({'name': 'foo', 'landuse': 'farm', 'boundary': 'administrative', 'type': 'boundary'}),
            {'name': 'foo', 'landuse': 'farm', 'boundary': 'administrative', 'type': 'boundary'})
        # boundary relation for non boundary
        eq_(tagfilter({'name': 'foo', 'landuse': 'farm', 'type': 'boundary'}), {})

    def test_mapping_for_nodes(self):
        for_nodes = self.tag_mapping.for_nodes
        eq_mapping(for_nodes({'unknown': 'baz'}), [])
        eq_mapping(for_nodes({'place': 'unknown'}), [])
        eq_mapping(for_nodes({'place': 'city'}), [(('place', 'city'), ('places',))])
        eq_mapping(for_nodes({'place': 'city', 'highway': 'unknown'}), [(('place', 'city'), ('places',))])
        eq_mapping(for_nodes({'place': 'city', 'highway': 'bus_stop'}), 
            [(('place', 'city'), ('places',)), (('highway', 'bus_stop'), ('transport_points',))])

    def test_mapping_for_ways(self):
        for_ways = self.tag_mapping.for_ways
        eq_mapping(for_ways({'unknown': 'baz'}), [])
        eq_mapping(for_ways({'highway': 'unknown'}), [])
        eq_mapping(for_ways({'highway': 'track'}), [(('highway', 'track'), ('minorroads',))])
        eq_mapping(for_ways({'highway': 'secondary', 'railway': 'tram'}), 
            [(('railway', 'tram'), ('railways',)), (('highway', 'secondary'), ('mainroads',))])
        eq_mapping(for_ways({'highway': 'footway'}), 
            [(('highway', 'footway'), ('minorroads',)), (('highway', 'footway'), ('landusages',))])

        eq_mapping(for_ways({'highway': 'footway', 'landuse': 'park'}), 
            [(('highway', 'footway'), ('minorroads',)), (('landuse', 'park'), ('landusages',))])

    def test_mapping_for_relation(self):
        for_relations = self.tag_mapping.for_relations
        eq_mapping(for_relations({'unknown': 'baz'}), [])
        eq_mapping(for_relations({'landuse': 'unknown'}), [])
        eq_mapping(for_relations({'landuse': 'farm'}), [(('landuse', 'farm'), ('landusages',))])
        eq_mapping(for_relations({'landuse': 'farm', 'highway': 'secondary'}),
            [(('landuse', 'farm'), ('landusages',))])
        
        eq_mapping(for_relations({'landuse': 'farm', 'aeroway': 'apron'}),
            [(('aeroway', 'apron'), ('transport_areas',)), (('landuse', 'farm'), ('landusages',))])

        eq_mapping(for_relations({'boundary': 'administrative', 'admin_level': '8'}),
            [(('boundary', 'administrative'), ('admin',))])




def eq_mapping(actual_mappings, expected_mappings):
    assert len(actual_mappings) == len(expected_mappings), '%s != %s' % (actual_mappings, expected_mappings)
    actual_mappings = [(tags, tuple(m.name for m in mappings)) for tags, mappings in actual_mappings]
    actual_mappings.sort()
    expected_mappings.sort()
    eq_(actual_mappings, expected_mappings)
