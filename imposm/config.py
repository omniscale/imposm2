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

# import relations with missing rings
import_partial_relations = False

# select relation builder: union or contains
relation_builder = 'contains'

# log relation that take longer than x seconds
imposm_multipolygon_report = 60

# skip relations with more rings (0 skip nothing)
imposm_multipolygon_max_ring = 0

# split ways that are longer than x nodes (0 to split nothing)
imposm_linestring_max_length = 0

# create a SERIAL PRIMARY KEY column (id) for all Postgres tables
# solves cases where osm_id is not unique (e.g. tram and road share the
# same way and are combined in a union view)
imposm_pg_serial_id = True

# cache coords in a compact storage (with delta encoding)
# use this when memory is limited (default)
imposm_compact_coords_cache = True