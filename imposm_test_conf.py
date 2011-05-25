# rename to `db_conf` to enable tests with PostGIS DB
_db_conf = dict(
    db='osm',
    # host='localhost',
    host='172.16.197.131',
    port=5432,
    user='osm',
    password='osm',
    sslmode='allow',
    prefix='osm_new_',
    proj='epsg:4326',
)
