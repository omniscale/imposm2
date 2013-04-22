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
import cgi
import urllib

from . postgis import PostGISDB
from .. mapping import Options

def DB(db_conf):
    if db_conf.get('name', 'postgis') == 'postgis':
        # default and backwards compat
        return PostGISDB(db_conf)
    raise ValueError('unknown db: %s' % (db_conf.name,))

def check_connection(db_conf):
    try:
        db = DB(db_conf)
        db.connection
    except Exception, e:
        return e

def db_conf_from_string(conf, base_db_conf):
    db_conf = _parse_rfc1738_args(conf)
    if 'proj' not in db_conf:
        db_conf.proj = base_db_conf.proj
    if 'prefix' not in db_conf:
        db_conf.prefix = base_db_conf.prefix
    return db_conf


def _parse_rfc1738_args(name):
    # from SQLAlchemy lib/sqlalchemy/engine/url.py
    # MIT licensed
    pattern = re.compile(r'''
            (?P<name>\w+)://
            (?:
                (?P<user>[^:/]*)
                (?::(?P<password>[^/]*))?
            @)?
            (?:
                (?P<host>[^/:]*)
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<db>.*))?
            '''
            , re.X)

    m = pattern.match(name)
    if m is not None:
        components = m.groupdict()
        if components['db'] is not None:
            tokens = components['db'].split('?', 2)
            components['db'] = tokens[0]
            query = (len(tokens) > 1 and dict(cgi.parse_qsl(tokens[1]))) or None
            if query is not None:
                query = dict((k.encode('ascii'), query[k]) for k in query)
        else:
            query = None
        components['query'] = query

        if components['password'] is not None:
            components['password'] = urllib.unquote_plus(components['password'])

        return Options(**components)
    else:
        raise ValueError(
            "Could not parse rfc1738 URL from string '%s'" % name)
