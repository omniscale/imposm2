from . postgis import PostGISDB

def DB(db_conf):
    return PostGISDB(db_conf)