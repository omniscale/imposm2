from imposm.cache.internal import DeltaNodes as _DeltaNodes
from collections import deque
from itertools import izip
import bisect

def unzip_nodes(nodes):
    ids, lons, lats = [], [], []
    last_id = last_lon = last_lat = 0
    for id, lon, lat in nodes:
        ids.append(id - last_id)
        lons.append(lon - last_lon)
        lats.append(lat - last_lat)
        last_id = id
        last_lon = lon
        last_lat = lat
    
    return ids, lons, lats


def zip_nodes(ids, lons, lats):
    nodes = []
    last_id = last_lon = last_lat = 0
    for id, lon, lat in izip(ids, lons, lats):
        last_id += id
        last_lon += lon
        last_lat += lat
        
        nodes.append((
            last_id,
            last_lon,
            last_lat
        ))
    return nodes

class DeltaNodes(object):
    def __init__(self, data=None):
        self.nodes = []
        self.changed = False
        if data:
            self.deserialize(data)
    
    def get(self, osmid):
        i = bisect.bisect(self.nodes, (osmid, ))
        if i != len(self.nodes) and self.nodes[i][0] == osmid:
            return self.nodes[i]
        return None
    
    def add(self, osmid, lon, lat):
        # todo: overwrite
        self.changed = True
        if self.nodes and self.nodes[-1][0] < osmid:
            self.nodes.append((osmid, lon, lat))
        else:
            bisect.insort(self.nodes, (osmid, lon, lat))
    
    def serialize(self):
        ids, lons, lats = unzip_nodes(self.nodes)
        nodes = _DeltaNodes()
        nodes.id = ids
        nodes.lons = lons
        nodes.lats = lats
        return nodes.SerializeToString()
    
    def deserialize(self, data):
        nodes = _DeltaNodes()
        nodes.ParseFromString(data)
        self.nodes = zip_nodes(
            nodes.id, nodes.lon, nodes.lat)

class DeltaCoordsDB(object):
    def __init__(self, delta_nodes_cache_size=100, delta_nodes_size=6):
        self.delta_nodes = {}
        self.delta_node_ids = deque()
        self.delta_nodes_cache_size = delta_nodes_cache_size
        self.delta_nodes_size = delta_nodes_size
    
    def put(self, osmid, lon, lat):
        delta_id = osmid >> self.delta_nodes_size
        if delta_id not in self.delta_nodes:
            self.fetch_delta_node(delta_id)
        delta_node = self.delta_nodes[delta_id]
        delta_node.add(osmid, lon, lat)
    
    def get(self, osmid):
        delta_id = osmid >> self.delta_nodes_size
        if delta_id not in self.delta_nodes:
            self.fetch_delta_node(delta_id)
        return self.delta_nodes[delta_id].get(osmid)
    
    def _put(self, delta_node):
        pass
    
    def _get(self, delta_id):
        return None
    
    def fetch_delta_node(self, delta_id):
        if len(self.delta_node_ids) >= self.delta_nodes_cache_size:
            rm_id = self.delta_node_ids.popleft()
            rm_node = self.delta_nodes.pop(rm_id)
            if rm_node.changed:
                self._put(rm_node)
        new_node = self._get(delta_id)
        if new_node is None:
            new_node = DeltaNodes()
        self.delta_nodes[delta_id] = new_node
        self.delta_node_ids.append(delta_id)

def eq_(a, b):
    assert a == b, '%r == %r' % (a, b)

def test_unzip_nodes():
    ids, lons, lats = unzip_nodes((
        (100, 5, 53),
        (101, 6, 54),
        (120, 5, 54)
    ))
    eq_(ids, [100, 1, 19])
    eq_(lons, [5, 1, -1])
    eq_(lats, [53, 1, 0])

def test_zip_nodes():
    nodes = zip_nodes(
        [100, 1, 19],
        [5, 1, -1],
        [53, 1, 0]
    )
    eq_(nodes, [
        (100, 5, 53),
        (101, 6, 54),
        (120, 5, 54)
    ])

def test_delta_nodes():
    nodes = _DeltaNodes()
    ids, lons, lats = unzip_nodes((
        (100, 5, 53),
        (101, 6, 54),
        (120, 5, 54),
    ))
    nodes.id = ids
    nodes.lon = lons
    nodes.lat = lats
    data = nodes.SerializeToString()
    nodes = _DeltaNodes()
    nodes.ParseFromString(data)
    eq_(nodes.id, (100, 1, 19))
    eq_(nodes.lon, (5, 1, -1))
    eq_(nodes.lat, (53, 1, 0))


def test_delta_coords_db():
    db = DeltaCoordsDB()
    db.put(10, 1, 11)
    db.put(11, 2, 12)
    db.put(9, 3, 13)
    db.put(20, 4, 14)
    db.put(1000, 10, 11)
    db.put(1010, 20, 12)
    db.put(1020, 30, 13)
    db.put(2000, 40, 14)
    
    eq_(len(db.delta_nodes), 3)
    eq_(db.get(10), (10, 1, 11))
    eq_(db.get(11), (11, 2, 12))
    eq_(db.get(9), (9, 3, 13))
    eq_(db.get(20), (20, 4, 14))
    
    eq_(db.get(1000), (1000, 10, 11))
    eq_(db.get(1001), None)
    

if __name__ == '__main__':
    test_unzip_nodes()
    test_zip_nodes()
    test_delta_nodes()
    test_delta_coords_db()
