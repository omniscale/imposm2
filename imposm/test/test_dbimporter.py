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

from imposm.dbimporter import DictBasedImporter
from imposm import defaultmapping

from nose.tools import eq_

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
        ]
        self.importer.insert(mappings, 1234, [(0, 0), (1, 0), (1, 1), (0, 0)],
            {'highway': 'secondary', 'railway': 'tram', 'oneway': '1',
             'name': 'roundabout',
            }
        )

        queue_item = self.importer.db_queue.get()
        eq_(queue_item['mapping_names'], ['mainroads', 'railways'])
        eq_(queue_item['osm_id'], 1234)
        eq_(queue_item['fields'], {
            'highway': 'secondary',
            'railway': 'tram',
            'oneway': 1,
            'z_order': 7,
            'bridge': 0,
            'tunnel': 0,
            'name': 'roundabout',
            'ref': None
        })