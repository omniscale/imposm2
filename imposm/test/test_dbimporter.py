# Copyright 2012 Omniscale (http://omniscale.com)
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

from imposm.dbimporter import DictBasedImporter, TupleBasedImporter
from imposm import defaultmapping

from nose.tools import eq_, assert_almost_equal

class TestDictBasedImporter(object):
    def setup(self):
        dummy_db = None
        mapper = None
        self.importer = DictBasedImporter(None, dummy_db, mapper, None,
            dry_run=False)

    def test_insert(self):
        mappings = [
            (('highway', 'secondary'), [defaultmapping.mainroads]),
            (('railway', 'tram'), [defaultmapping.railways]),
            (('landusage', 'grass'), [defaultmapping.landusages]),
        ]
        assert self.importer.insert(mappings, 1234, [(0, 0), (1, 0), (1, 1), (0, 0)],
            {'highway': 'secondary', 'railway': 'tram', 'oneway': '1',
             'name': 'roundabout',
            }
        )

        # get items, sort by mapping_names so that landusages comes first
        queue_items = [self.importer.db_queue.get(), self.importer.db_queue.get()]
        queue_items.sort(key=lambda x: x['mapping_names'])

        polygon_item = queue_items[0]
        linestring_item = queue_items[1]

        eq_(linestring_item['mapping_names'], ['mainroads', 'railways'])
        eq_(linestring_item['osm_id'], 1234)
        eq_(linestring_item['fields'], {
            'highway': 'secondary',
            'railway': 'tram',
            'oneway': 1,
            'z_order': 7,
            'bridge': 0,
            'tunnel': 0,
            'name': 'roundabout',
            'ref': None
        })
        eq_(polygon_item['mapping_names'], ['landusages'])
        eq_(polygon_item['osm_id'], 1234)
        assert_almost_equal(polygon_item['fields']['area'], 6195822904.182782)
        del polygon_item['fields']['area']
        eq_(polygon_item['fields'], {
            'z_order': 27,
            'landusage': 'grass',
            'name': 'roundabout',
        })

class TestTupleBasedImporter(object):
    def setup(self):
        dummy_db = None
        mapper = None
        self.importer = TupleBasedImporter(None, dummy_db, mapper, None,
            dry_run=False)

    def test_insert(self):
        mappings = [
            (('highway', 'secondary'), [defaultmapping.mainroads]),
            (('railway', 'tram'), [defaultmapping.railways]),
            (('landusage', 'grass'), [defaultmapping.landusages]),
        ]
        assert self.importer.insert(mappings, 1234, [(0, 0), (1, 0), (1, 1), (0, 0)],
            {'highway': 'secondary', 'railway': 'tram', 'oneway': '1',
             'name': 'roundabout',
            }
        )

        mainroads_item = self.importer.db_queue.get()
        eq_(mainroads_item[0], defaultmapping.mainroads)
        eq_(mainroads_item[1], 1234)
        eq_(mainroads_item[3], ['roundabout', 'secondary', 0, 0, 1, None, 5])

        railways_item = self.importer.db_queue.get()
        eq_(railways_item[0], defaultmapping.railways)
        eq_(railways_item[1], 1234)
        eq_(railways_item[3], ['roundabout', 'tram', 0, 0, 7])

        landusages_item = self.importer.db_queue.get()
        eq_(landusages_item[0], defaultmapping.landusages)
        eq_(landusages_item[1], 1234)
        eq_(landusages_item[3], ['roundabout', 'grass', 6195822904.182782, 27])
