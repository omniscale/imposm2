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
from imposm.cache.tc import NodeDB, CoordDB, DeltaCoordsDB

from nose.tools import eq_, assert_almost_equal


class TestNodeDB(object):
    def setup(self):
        fd_, self.fname = tempfile.mkstemp('.db')
        self.db = NodeDB(self.fname)
    
    def teardown(self):
        os.unlink(self.fname)
    
    def test_insert(self):
        assert self.db.put(1000, {'foo': 2}, (123, 456))
        assert self.db.put(2**40, {'bar': 2}, (123, 456))
        
        nd = self.db.get(1000)
        eq_(nd.osm_id, 1000)
        eq_(nd.tags, {'foo': 2})
        eq_(nd.coord, (123, 456))

        nd = self.db.get(2**40)
        eq_(nd.osm_id, 2**40)

    
    def test_read_only(self):
        assert self.db.put(1000, {'foo': 2}, (123, 456))
        assert self.db.put(2**40, {'bar': 2}, (123, 456))
        self.db.close()
        self.db = NodeDB(self.fname, 'r')
        
        nd = self.db.get(1000)
        eq_(nd.osm_id, 1000)
        eq_(nd.tags, {'foo': 2})
        eq_(nd.coord, (123, 456))

        nd = self.db.get(2**40)
        eq_(nd.osm_id, 2**40)
        
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
    testclass = CoordDB
    def setup(self):
        fd_, self.fname = tempfile.mkstemp('.db')
        self.db = self.testclass(self.fname)

    def teardown(self):
        os.unlink(self.fname)

    def test_insert(self):
        assert self.db.put(1000, 123, 179.123456789)
        assert self.db.put(2**40, 123, 179.123456789)
        assert self.db.put(2**40+1, 123, 179.123456789)
        
        pos = self.db.get(1000)
        assert_almost_equal(pos[0], 123.0, 6)
        assert_almost_equal(pos[1], 179.123456789, 6)

        assert self.db.get(2**40)
        assert self.db.get(2**40+1)
    
    def test_read_only(self):
        assert self.db.put(1000, 123, 0)
        assert self.db.put(1001, -180.0, -90)
        assert self.db.put(1010, 180, 90)
        assert self.db.put(2**40, 123, 179.123456789)
        assert self.db.put(2**40+1, 123, 179.123456789)
        
        self.db.close()
        self.db = self.testclass(self.fname, 'r')
        
        pos = self.db.get(1000)
        assert_almost_equal(pos[0], 123.0, 6)
        assert_almost_equal(pos[1], 0.0, 6)

        pos = self.db.get(1001)
        assert_almost_equal(pos[0], -180.0, 6)
        assert_almost_equal(pos[1], -90.0, 6)
        
        pos = self.db.get(1010)
        assert_almost_equal(pos[0], 180.0, 6)
        assert_almost_equal(pos[1], 90.0, 6)
        
        assert self.db.get(2**40)
        assert self.db.get(2**40+1)
        
        assert not self.db.put(2001, 123, 456)
        assert not self.db.get(2001)


class TestDeltaCoordDB(TestCoordDB):
    testclass = DeltaCoordsDB

    def setup(self):
        fd_, self.fname = tempfile.mkstemp('.db')
        self.db = DeltaCoordsDB(self.fname)
