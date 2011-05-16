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
    db = DeltaCoordsDB('/tmp/delta.db')
    db.put(10, 1, 11)
    db.put(11, 2, 12)
    db.put(9, 3, 13)
    db.put(20, 4, 14)
    db.put(1000, 10, 11)
    db.put(1010, 20, 12)
    db.put(1020, 30, 13)
    db.put(2000, 40, 14)
    db.close()

    db = DeltaCoordsDB('/tmp/delta.db')
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
