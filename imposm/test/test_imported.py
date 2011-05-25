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

import re
import os
import tempfile
import shutil

from contextlib import contextmanager

import imposm.app
import imposm.db
import imposm.mapping

from nose.tools import eq_
from nose.plugins import skip

temp_dir = None
old_cwd = None

try:
    from imposm_test_conf import db_conf
    db_conf = imposm.mapping.Options(db_conf)
except ImportError:
    raise skip.SkipTest('no imposm_test_conf.py with db_conf found')

def setup_module():
    global old_cwd, temp_dir
    old_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    test_osm_file = os.path.join(os.path.dirname(__file__), 'test.out.osm')
    with capture_out():
        imposm.app.main(['--read', test_osm_file, '--write', '-d', db_conf.db, '--host', db_conf.host,
            '--proj', db_conf.proj])

class TestImported(object):
    def __init__(self):
        self.db = imposm.db.DB(db_conf)
    
    def test_point(self):
        cur = self.db.cur
        cur.execute('select osm_id, name, ST_AsText(geometry) from osm_new_places where osm_id = 1')
        results = cur.fetchall()
        eq_(len(results), 1)
        eq_(results[0], (1, 'Foo', 'POINT(13 47.5)'))

    def test_way(self):
        cur = self.db.cur
        cur.execute('select osm_id, name, ST_AsText(geometry) from osm_new_landusages where osm_id = 1001')
        results = cur.fetchall()
        eq_(len(results), 1)
        eq_(results[0][:-1], (1001, 'way 1001',))
        eq_(roundwkt(results[0][-1]), 'POLYGON((13.0 47.5,14.5 50.0,16.5 49.0,17.0 47.0,14.5 45.5,13.0 47.5),(14.0 47.5,15.0 47.0,15.5 48.0,14.5 48.5,14.0 47.5))')

        cur.execute('select osm_id, name, ST_AsText(geometry) from osm_new_landusages where osm_id = 2001')
        results = cur.fetchall()
        eq_(len(results), 1)
        eq_(results[0][:-1], (2001, 'way 2001',))
        eq_(roundwkt(results[0][-1]), 'POLYGON((23.0 47.5,24.5 50.0,26.5 49.0,27.0 47.0,24.5 45.5,23.0 47.5),(24.5 47.0,25.5 46.5,26.0 47.5,25.0 47.5,24.5 47.0),(24.2 48.25,25.25 47.7,25.7 48.8,24.7 49.25,24.2 48.25))')


        cur.execute('select osm_id, name, ST_AsText(geometry) from osm_new_landusages where osm_id = 3001')
        results = cur.fetchall()
        eq_(len(results), 1)
        eq_(results[0][:-1], (3001, 'way 3002',))
        eq_(roundwkt(results[0][-1]), 'POLYGON((33.0 47.5,34.5 50.0,36.5 49.0,37.0 47.0,34.5 45.5,33.0 47.5),(34.0 47.5,35.0 47.0,35.5 48.0,34.5 48.5,34.0 47.5))')


def roundwkt(wkt):
    def round_num(num_str):
        return str(round(float(num_str.group(0)), 2))
    return re.sub('\d+(\.\d+)?', round_num, wkt)

def teardown_module():
    if old_cwd:
        os.chdir(old_cwd)
    
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    

@contextmanager
def capture_out():
    import sys
    from cStringIO import StringIO

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    