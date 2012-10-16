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

from imposm.geom import LimitPolygonGeometry, EmtpyGeometryError
from shapely.wkt import loads

from nose.tools import raises

class TestLimitPolygonGeometry(object):

    @raises(EmtpyGeometryError)
    def test_linestring_no_intersection(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        limit_to.intersection(loads('LINESTRING(-100 -100, -50 -50)'))

    def test_linestring(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        geom = limit_to.intersection(loads('LINESTRING(-10 -10, 20 20)'))
        assert geom.almost_equals(loads('LINESTRING(0 0, 10 10)'))

    def test_linestring_contained(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        test_geom = loads('LINESTRING(1 1, 9 9)')
        geom = limit_to.intersection(test_geom)
        # should return unmodified input geometry
        assert geom is test_geom

    def test_linestring_multilinestring_result(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        geom = limit_to.intersection(loads('LINESTRING(-10 -20, 5 10, 20 -20)'))
        assert isinstance(geom, list)
        assert geom[0].almost_equals(loads('LINESTRING(0 0, 5 10)'))
        assert geom[1].almost_equals(loads('LINESTRING(5 10, 10 0)'))

    @raises(EmtpyGeometryError)
    def test_linestring_point_result(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        geom = limit_to.intersection(loads('LINESTRING(-10 -10, 0 0)'))

    def test_linestring_mixed_result(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        geom = limit_to.intersection(loads('LINESTRING(0 0, 5 -10, 5 10)'))
        # point and linestring, point not returned
        assert isinstance(geom, list)
        assert len(geom) == 1
        assert geom[0].almost_equals(loads('LINESTRING(5 0, 5 10)'))

    def test_polygon_mixed_result(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        test_geom = loads('POLYGON((0 -10, 0 5, 2.5 -5, 5 0, 7.5 -5, 10 5, 10 -10, 0 -10))')
        geom = limit_to.intersection(test_geom)
        # point and two polygons, point not returned
        assert isinstance(geom, list)
        assert len(geom) == 2
        assert geom[0].almost_equals(loads('POLYGON((1.25 0, 0 0, 0 5, 1.25 0))'))
        assert geom[1].almost_equals(loads('POLYGON((10 0, 8.75 0, 10 5, 10 0))'))

    def test_polygon_multipolygon_result(self):
        geom = 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
        limit_to = LimitPolygonGeometry(loads(geom))
        test_geom = loads('POLYGON((0 -10, 0 5, 2.5 -5, 5 -1, 7.5 -5, 10 5, 10 -10, 0 -10))')
        geom = limit_to.intersection(test_geom)
        # similar to above, but point does not touch the box, so we should get
        # a single multipolygon
        assert geom.almost_equals(loads(
            'MULTIPOLYGON(((1.25 0, 0 0, 0 5, 1.25 0)),'
            '((10 0, 8.75 0, 10 5, 10 0)))'))
