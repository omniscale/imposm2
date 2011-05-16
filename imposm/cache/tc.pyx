from imposm.base import Node, Way, Relation
from libc.stdint cimport uint32_t, int64_t

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)

cdef extern from "marshal.h":
    object PyMarshal_ReadObjectFromString(char *string, Py_ssize_t len)
    object PyMarshal_WriteObjectToString(object value, int version)

cdef extern from "tcutil.h":
    ctypedef int TCCMP()
    cdef int tccmpint32()
    cdef int tccmpint64()

cdef extern from "tcbdb.h":
    ctypedef enum:
        BDBFOPEN
        BDBFFATAL

    ctypedef enum:
        BDBOREADER = 1 << 0 # /* open as a reader */
        BDBOWRITER = 1 << 1 # /* open as a writer */
        BDBOCREAT = 1 << 2  # /* writer creating */
        BDBOTRUNC = 1 << 3  # /* writer truncating */
        BDBONOLCK = 1 << 4  # /* open without locking */
        BDBOLCKNB = 1 << 5  # /* lock without blocking */
        BDBOTSYNC = 1 << 6  # /* synchronize every transaction */

    ctypedef enum:
        BDBTLARGE = 1 << 0,  # /* use 64-bit bucket array */
        BDBTDEFLATE = 1 << 1 # /* compress each page with Deflate */
        BDBTBZIP = 1 << 2,   # /* compress each record with BZIP2 */
        BDBTTCBS = 1 << 3,   # /* compress each page with TCBS */
        BDBTEXCODEC = 1 << 4 # /* compress each record with outer functions */

    ctypedef void TCBDB
    ctypedef void BDBCUR

    TCBDB *tcbdbnew()
    void tcbdbdel(TCBDB *)
    int tcbdbecode(TCBDB *)

    bint tcbdbtune(TCBDB *db, int lmemb, int nmemb,
                   int bnum, int apow, int fpow, int opts)
    bint tcbdbsetcache(TCBDB *bdb, int lcnum, int ncnum)

    bint tcbdbsetcmpfunc(TCBDB *bdb, TCCMP cmp, void *cmpop)
    bint tcbdbsetmutex(TCBDB *bdb)

    bint tcbdbopen(TCBDB *, char *, int)
    bint tcbdbclose(TCBDB *) nogil
    bint tcbdbput(TCBDB *, void *, int, void *, int) nogil
    void *tcbdbget(TCBDB *, void *, int, int *) nogil
    void *tcbdbget3(TCBDB *bdb, void *kbuf, int ksiz, int *sp) nogil

    long tcbdbrnum(TCBDB *bdb)

    BDBCUR *tcbdbcurnew(TCBDB *bdb)
    void tcbdbcurdel(BDBCUR *cur)
    bint tcbdbcurfirst(BDBCUR *cur)
    bint tcbdbcurnext(BDBCUR *cur)
    void *tcbdbcurkey3(BDBCUR *cur, int *sp)
    void *tcbdbcurval3(BDBCUR *cur, int *sp)


DEF COORD_FACTOR = 11930464.7083 # ((2<<31)-1)/360.0

cdef uint32_t _coord_to_uint32(double x) nogil:
    return <uint32_t>((x + 180.0) * COORD_FACTOR)

cdef double _uint32_to_coord(uint32_t x) nogil:
    return <double>((x / COORD_FACTOR) - 180.0)

ctypedef struct coord:
    uint32_t x
    uint32_t y

cdef inline coord coord_struct(double x, double y) nogil:
    cdef coord p
    p.x = _coord_to_uint32(x)
    p.y = _coord_to_uint32(y)
    return p

_modes = {
    'w': BDBOWRITER | BDBOCREAT,
    'r': BDBOREADER | BDBONOLCK,
}

cdef class BDB:
    cdef TCBDB *db
    cdef object filename
    cdef int _opened
    cdef BDBCUR *_cur
    def __cinit__(self, filename, mode='w', estimated_records=0):
        self.db = tcbdbnew()
        self._opened = 0

    def __init__(self, filename, mode='w', estimated_records=0):
        self.filename = filename
        self._tune_db(estimated_records)
        tcbdbsetcmpfunc(self.db, tccmpint64, NULL)
        if not tcbdbopen(self.db, filename, _modes[mode]):
            raise IOError(tcbdbecode(self.db))
        self._opened = 1
    
    def _tune_db(self, estimated_records):
        if estimated_records:
            lmemb = 128 # default
            nmemb = -1
            fpow = 13 # 2^13 = 8196
            bnum = int((estimated_records*3)/lmemb)
            tcbdbtune(self.db, lmemb, nmemb, bnum, 5, fpow, BDBTLARGE | BDBTDEFLATE)
        else:
            tcbdbtune(self.db, -1, -1, -1, 5, 13, BDBTLARGE | BDBTDEFLATE)
    
    def get(self, int64_t osmid):
        """
        Return object with given id.
        Returns None if id is not stored.
        """
        cdef void *ret
        cdef int ret_size
        ret = tcbdbget3(self.db, <char *>&osmid, sizeof(int64_t), &ret_size)
        if not ret: return None
        return self._obj(osmid, PyMarshal_ReadObjectFromString(<char *>ret, ret_size))

    def get_raw(self, int64_t osmid):
        """
        Return object with given id.
        Returns None if id is not stored.
        """
        cdef void *ret
        cdef int ret_size
        ret = tcbdbget3(self.db, <char *>&osmid, sizeof(int64_t), &ret_size)
        if not ret: return None
        return PyString_FromStringAndSize(<char *>ret, ret_size)

    def put(self, int64_t osmid, data):
        return self.put_marshaled(osmid, PyMarshal_WriteObjectToString(data, 2))

    def put_marshaled(self, int64_t osmid, data):
        return tcbdbput(self.db, <char *>&osmid, sizeof(int64_t), <char *>data, len(data))

    cdef object _obj(self, int64_t osmid, data):
        """
        Create an object from the id and unmarshaled data.
        Should be overridden by subclasses.
        """
        return data

    def __iter__(self):
        """
        Return an iterator over the database.
        Resets any existing iterator.
        """
        if self._cur:
            tcbdbcurdel(self._cur)
        self._cur = tcbdbcurnew(self.db)
        if not tcbdbcurfirst(self._cur):
            return iter([])
        return self

    def __contains__(self, int64_t osmid):
        cdef void *ret
        cdef int ret_size
        ret = tcbdbget3(self.db, <char *>&osmid, sizeof(int64_t), &ret_size);
        if ret:
            return 1
        else:
            return 0
    
    def __len__(self):
        return tcbdbrnum(self.db)
    
    def __next__(self):
        """
        Return next item as object.
        """
        cdef int64_t osmid

        if not self._cur: raise StopIteration

        osmid, data = self._get_cur()

        # advance cursor, set to NULL if at the end
        if tcbdbcurnext(self._cur) == 0:
            tcbdbcurdel(self._cur)
            self._cur = NULL
        
        # return objectified item
        return self._obj(osmid, data)

    cdef object _get_cur(self):
        """
        Return the current object at the current cursor position
        as a tuple of the id and the unmarshaled data.
        """
        cdef int size
        cdef void *ret
        ret = tcbdbcurkey3(self._cur, &size)
        osmid = (<int64_t *>ret)[0]
        ret = tcbdbcurval3(self._cur, &size)
        value = PyMarshal_ReadObjectFromString(<char *>ret, size)
        return osmid, value

    def close(self):
        if self._opened:
            tcbdbclose(self.db)
        self._opened = 0
    
    def __dealloc__(self):
        if self._opened:
            tcbdbclose(self.db)
        tcbdbdel(self.db)

cdef class CoordDB(BDB):
    def put(self, osmid, x, y):
        return self._put(osmid, x, y)
    
    def put_marshaled(self, osmid, x, y):
        return self._put(osmid, x, y)
    
    cdef bint _put(self, int64_t osmid, double x, double y) nogil:
        cdef coord p = coord_struct(x, y)
        return tcbdbput(self.db, <char *>&osmid, sizeof(int64_t), <char *>&p, sizeof(coord))

    def get(self, int64_t osmid):
        cdef coord *value
        cdef int ret_size
        value = <coord *>tcbdbget3(self.db, <char *>&osmid, sizeof(int64_t), &ret_size)
        if not value: return
        return _uint32_to_coord(value.x), _uint32_to_coord(value.y)

    def get_coords(self, refs):
        cdef coord *value
        cdef int ret_size
        cdef int64_t osmid
        coords = list()
        for osmid in refs:
            value = <coord *>tcbdbget3(self.db, <char *>&osmid, sizeof(int64_t), &ret_size)
            if not value: return
            coords.append((_uint32_to_coord(value.x), _uint32_to_coord(value.y)))
        
        return coords

    cdef object _get_cur(self):
        cdef int size
        cdef int64_t osmid
        cdef void *ret
        cdef coord *value
        ret = tcbdbcurkey3(self._cur, &size)
        osmid = (<int64_t *>ret)[0]
        value = <coord *>tcbdbcurval3(self._cur, &size)
        return osmid, (_uint32_to_coord(value.x), _uint32_to_coord(value.y))

    cdef object _obj(self, int64_t osmid, data):
        return osmid, data

cdef class NodeDB(BDB):
    def put(self, osmid, tags, pos):
        return self.put_marshaled(osmid, PyMarshal_WriteObjectToString((tags, pos), 2))
    
    def put_marshaled(self, int64_t osmid, data):
        return tcbdbput(self.db, <char *>&osmid, sizeof(int64_t), <char *>data, len(data))

    cdef object _obj(self, int64_t osmid, data):
        return Node(osmid, data[0], data[1])

cdef class InsertedWayDB(BDB):
    def put(self, int64_t osmid):
        return tcbdbput(self.db, <char *>&osmid, sizeof(int64_t), 'x', 1);

    def __next__(self):
        """
        Return next item as object.
        """
        cdef int64_t osmid
        cdef int size
        cdef void *ret

        if not self._cur: raise StopIteration

        ret = tcbdbcurkey3(self._cur, &size)
        osmid = (<int64_t *>ret)[0]

        # advance cursor, set to NULL if at the end
        if tcbdbcurnext(self._cur) == 0:
            tcbdbcurdel(self._cur)
            self._cur = NULL

        return osmid

cdef class RefTagDB(BDB):
    """
    Database for items with references and tags (i.e. ways/relations).
    """
    def put(self, osmid, tags, refs):
        return self.put_marshaled(osmid, PyMarshal_WriteObjectToString((tags, refs), 2))
    
    def put_marshaled(self, int64_t osmid, data):
        return tcbdbput(self.db, <char *>&osmid, sizeof(int64_t), <char *>data, len(data))

cdef class WayDB(RefTagDB):
    cdef object _obj(self, int64_t osmid, data):
        return Way(osmid, data[0], data[1])

cdef class RelationDB(RefTagDB):
    cdef object _obj(self, int64_t osmid, data):
        return Relation(osmid, data[0], data[1])

from imposm.cache.internal import DeltaCoords as _DeltaCoords
from collections import deque
import bisect

cdef unzip_nodes(list nodes):
    cdef int64_t last_lon, last_lat, lon, lat
    cdef double lon_f, lat_f
    cdef int64_t last_id, id
    ids, lons, lats = [], [], []
    last_id = last_lon = last_lat = 0
    for id, lon_f, lat_f in nodes:
        lon = _coord_to_uint32(lon_f)
        lat = _coord_to_uint32(lat_f)
        
        ids.append(id - last_id)
        lons.append(lon - last_lon)
        lats.append(lat - last_lat)
        last_id = id
        last_lon = lon
        last_lat = lat
    
    return ids, lons, lats

cdef zip_nodes(tuple ids, tuple lons, tuple lats):
    cdef uint32_t last_lon, last_lat
    cdef int64_t last_id
    nodes = []
    last_id = last_lon = last_lat = 0

    for i in range(len(ids)):
        last_id += ids[i]
        last_lon += lons[i]
        last_lat += lats[i]
    
        nodes.append((
            last_id,
            _uint32_to_coord(last_lon),
            _uint32_to_coord(last_lat)
        ))
    return nodes

class DeltaNodes(object):
    def __init__(self, data=None):
        self.nodes = []
        self.changed = False
        if data:
            self.deserialize(data)
    
    def changed(self):
        return self.changed
    
    def get(self, int64_t osmid):
        i = bisect.bisect(self.nodes, (osmid, ))
        if i != len(self.nodes) and self.nodes[i][0] == osmid:
            return self.nodes[i][1:]
        return None
    
    def add(self, int64_t osmid, double lon, double lat):
        # todo: overwrite
        self.changed = True
        if self.nodes and self.nodes[-1][0] < osmid:
            self.nodes.append((osmid, lon, lat))
        else:
            bisect.insort(self.nodes, (osmid, lon, lat))
    
    def serialize(self):
        ids, lons, lats = unzip_nodes(self.nodes)
        nodes = _DeltaCoords()
        nodes.ids = ids
        nodes.lons = lons
        nodes.lats = lats
        return nodes.SerializeToString()
    
    def deserialize(self, data):
        nodes = _DeltaCoords()
        nodes.ParseFromString(data)
        self.nodes = zip_nodes(
            nodes.ids, nodes.lons, nodes.lats)

class DeltaCoordsDB(object):
    def __init__(self, filename, mode='w', estimated_records=0, delta_nodes_cache_size=100, delta_nodes_size=6):
        self.db = BDB(filename, mode, estimated_records)
        self.mode = mode
        self.delta_nodes = {}
        self.delta_node_ids = deque()
        self.delta_nodes_cache_size = delta_nodes_cache_size
        self.delta_nodes_size = delta_nodes_size
    
    def put(self, int64_t osmid, double lon, double lat):
        if self.mode == 'r':
            return None
        delta_id = osmid >> self.delta_nodes_size
        if delta_id not in self.delta_nodes:
            self.fetch_delta_node(delta_id)
        delta_node = self.delta_nodes[delta_id]
        delta_node.add(osmid, lon, lat)
        return True
    
    put_marshaled = put
    
    def get(self, osmid):
        delta_id = osmid >> self.delta_nodes_size
        if delta_id not in self.delta_nodes:
            self.fetch_delta_node(delta_id)
        return self.delta_nodes[delta_id].get(osmid)
    
    def get_coords(self, osmids):
        coords = []
        for osmid in osmids:
            coord = self.get(osmid)
            if coord is None:
                return
            coords.append(coord)
        return coords
    
    def close(self):
        for node_id, node in self.delta_nodes.iteritems():
            self._put(node_id, node)
        self.delta_nodes = {}
        self.delta_node_ids = deque()
        self.db.close()
    
    def _put(self, delta_id, delta_node):
        data = delta_node.serialize()
        self.db.put_marshaled(delta_id, data)
    
    def _get(self, delta_id):
        return DeltaNodes(data=self.db.get_raw(delta_id))
    
    def fetch_delta_node(self, delta_id):
        if len(self.delta_node_ids) >= self.delta_nodes_cache_size:
            rm_id = self.delta_node_ids.popleft()
            rm_node = self.delta_nodes.pop(rm_id)
            if rm_node.changed:
                self._put(rm_id, rm_node)
        new_node = self._get(delta_id)
        if new_node is None:
            new_node = DeltaNodes()
        self.delta_nodes[delta_id] = new_node
        self.delta_node_ids.append(delta_id)

