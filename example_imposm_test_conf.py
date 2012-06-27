# update and save as imposm_test_conf.py to enable tests with PostGIS DB
db_conf = dict(
    db='osm',
    host='localhost',
    port=5432,
    user='osm',
    password='osm',
    sslmode='allow',
    prefix='osm_test_',
    proj='epsg:4326',
)
