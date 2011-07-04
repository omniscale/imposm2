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

from imposm.base import OSMElem
from imposm.mapping import Name, LocalizedName


def test_name_field():
    name = Name()
    elem = OSMElem(1, [], 'test', tags={'name': 'fixme'})
    assert name.value('fixme', elem) == ''
    assert elem.name == ''
    
    elem = OSMElem(1, [], 'test', tags={'name': 'Foo Street'})
    assert name.value('Foo Street', elem) == 'Foo Street'
    assert elem.name == 'Foo Street'

def test_localized_name_field():
    name = LocalizedName(['name:de', 'name:en', 'foo'])
    elem = OSMElem(1, [], 'test', tags={'name': 'Foo'})
    assert name.value(None, elem) == ''
    assert elem.name == ''

    elem = OSMElem(1, [], 'test', tags={'name:de': 'Foo', 'name:en': 'Bar'})
    assert name.value(None, elem) == 'Foo'
    assert elem.name == 'Foo'

    elem = OSMElem(1, [], 'test', tags={'name:es': 'Foo', 'name:en': 'Bar'})
    assert name.value(None, elem) == 'Bar'
    assert elem.name == 'Bar'

    elem = OSMElem(1, [], 'test', tags={'name:es': 'Foo', 'foo': 'Bar'})
    assert name.value(None, elem) == 'Bar'
    assert elem.name == 'Bar'
    
