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
import tempfile
from imposm.cache.tc import NodeDB, CoordDB
from imposm.cache.nodes import DeltaCoordsDB

from nose.tools import eq_, assert_almost_equal


class TestNodeDB(object):
    def setup(self):
        fd_, self.fname = tempfile.mkstemp('.db')
        self.db = NodeDB(self.fname)
    
    def teardown(self):
        os.unlink(self.fname)
    
    def test_insert(self):
        assert self.db.put(1000, {'foo': 2}, (123, 456))
        
        nd = self.db.get(1000)
        eq_(nd.osm_id, 1000)
        eq_(nd.tags, {'foo': 2})
        eq_(nd.coord, (123, 456))
    
    def test_read_only(self):
        assert self.db.put(1000, {'foo': 2}, (123, 456))
        self.db.close()
        self.db = NodeDB(self.fname, 'r')
        
        nd = self.db.get(1000)
        eq_(nd.osm_id, 1000)
        eq_(nd.tags, {'foo': 2})
        eq_(nd.coord, (123, 456))
        
        assert not self.db.put(1001, {'foo': 2}, (123, 456))
        assert not self.db.get(1001)

    def test_iter(self):
        assert self.db.put(1000, {'foo': 2}, (123, 456))
        
        nds = list(self.db)
        eq_(len(nds), 1)
        
        nd = nds[0]
        eq_(nd.osm_id, 1000)
        eq_(nd.tags, {'foo': 2})
        eq_(nd.coord, (123, 456))
        
class TestCoordDB(object):
    def setup(self):
        fd_, self.fname = tempfile.mkstemp('.db')
        self.db = DeltaCoordsDB(self.fname)
    
    def test_insert(self):
        assert self.db.put(1000, 123, 179.123456789)
        
        pos = self.db.get(1000)
        assert_almost_equal(pos[0], 123.0, 7)
        assert_almost_equal(pos[1], 179.123456789, 7)
    
    def test_read_only(self):
        assert self.db.put(1000, 123, 456)
        self.db.close()
        self.db = DeltaCoordsDB(self.fname, 'r')
        
        pos = self.db.get(1000)
        assert_almost_equal(pos[0], 123.0, 7)
        assert_almost_equal(pos[1], 456.0, 7)
        
        assert not self.db.put(1001, 123, 456)
        assert not self.db.get(1001)

    def _test_iter(self):
        assert self.db.put(1000, 123, 456)
        
        coords = list(self.db)
        eq_(len(coords), 1)
        
        osm_id, pos = coords[0]
        
        eq_(osm_id, 1000)
        assert_almost_equal(pos[0], 123.0, 7)
        assert_almost_equal(pos[1], 456.0, 7)
        