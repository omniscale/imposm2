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
import sys
import time
import datetime
import mmap
import multiprocessing

from multiprocessing import JoinableQueue
from Queue import Empty

import logging
log = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
    setproctitle
except ImportError:
    setproctitle = lambda x: None

class Timer(object):
    def __init__(self, title, logger):
        self.title = title
        self.logger = logger
        self.start_time = time.time()
    def stop(self):
        seconds = time.time() - self.start_time
        self.logger.message('%s took %s' % (self.title, format_total_time(seconds)))

class ParserProgress(multiprocessing.Process):
    log_every_seconds = 0.2

    def __init__(self):
        self.queue = multiprocessing.Queue()
        multiprocessing.Process.__init__(self)

    def run(self):
        last_log = time.time()
        counters = {'coords': 0, 'nodes':0, 'ways':0, 'relations':0}
        while True:
            log_statement = self.queue.get()
            if log_statement is None:
                break

            log_type, incr = log_statement
            counters[log_type] += incr
            if time.time() - last_log > self.log_every_seconds:
                last_log = time.time()
                self.print_log(counters)

    @staticmethod
    def message(msg):
        print >>sys.stderr, "[%s] %s" % (timestamp(), msg)
        sys.stderr.flush()

    def print_log(self, counters):
        print >>sys.stderr, "[%s] coords: %dk nodes: %dk ways: %dk relations: %dk\r" % (
            timestamp(),
            int(counters['coords']/1000),
            int(counters['nodes']/1000),
            int(counters['ways']/1000),
            int(counters['relations']/1000)
        ),
        sys.stderr.flush()

    def log(self, log_type, incr):
        self.queue.put((log_type, incr))

    def stop(self):
        sys.stderr.write('\n')
        sys.stderr.flush()
        self.queue.put(None)

class QuietParserProgress(ParserProgress):
    log_every_seconds = 60

class ProgressLog(object):
    log_every_seconds = 0.2

    def __init__(self, title=None, total=None):
        self.count = 0
        self.total = total
        self._total = '/%dk' % (total/1000) if total else ''
        self.title = title
        self.start_time = time.time()
        self.last_log = time.time()
        self.print_log()

    @staticmethod
    def message(msg):
        print >>sys.stderr, "[%s] %s" % (timestamp(), msg)
        sys.stderr.flush()

    def log(self, value=None, step=1):
        before = self.count//1000
        if value:
            self.count = value
        else:
            self.count += step
        if self.count//1000 > before:
            self.print_log()

    def print_log(self):
        if time.time() - self.last_log > self.log_every_seconds:
            self.last_log = time.time()
            print >>sys.stderr, "[%s] %s: %dk%s\r" % (
                timestamp(), self.title,
                int(self.count/1000), self._total,
            ),
            sys.stderr.flush()

    def stop(self):
        print >>sys.stderr
        seconds = time.time() - self.start_time
        total_time = format_total_time(seconds)
        print >>sys.stderr, "[%s] %s: total time %s for %d (%d/s)" % (
            timestamp(), self.title, total_time, self.count, self.count/seconds)
        sys.stderr.flush()

class QuietProgressLog(ProgressLog):
    log_every_seconds = 60

def timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S')

def format_total_time(seconds):
    h, m, s = seconds_to_hms(seconds)
    res = '%-02ds' % s
    if h or m:
        res = '%-02dm ' % m + res
        if h:
            res = '%-02dh ' % h + res
    return res

def seconds_to_hms(seconds):
    h, s = divmod(seconds, 60*60)
    m, s = divmod(s, 60)
    return h, m, s

class NullLog(object):
    def log_node(self):
        pass
    node = log_node

    def log_way(self):
        pass
    way = log_way

    def log_relation(self):
        pass
    relation = log_relation


class MMapReader(object):
    def __init__(self, m, size):
        self.m = m
        self.m.seek(0)
        self.size = size

    def read(self, size=None):
        if size is None:
            size = self.size - self.m.tell()
        else:
            size = min(self.size - self.m.tell(), size)
        return self.m.read(size)

    def readline(self):
        cur_pos = self.m.tell()
        if cur_pos >= self.size:
            return
        nl_pos = self.m.find('\n')
        self.m.seek(cur_pos)
        return self.m.read(nl_pos-cur_pos)

    def seek(self, n):
        self.m.seek(n)

class MMapPool(object):
    def __init__(self, n, mmap_size):
        self.n = n
        self.mmap_size = mmap_size
        self.pool = [mmap.mmap(-1, mmap_size) for _ in range(n)]
        self.free_mmaps = set(range(n))
        self.free_queue = JoinableQueue()

    def new(self):
        if not self.free_mmaps:
            self.free_mmaps.add(self.free_queue.get())
            self.free_queue.task_done()
        while True:
            try:
                self.free_mmaps.add(self.free_queue.get_nowait())
                self.free_queue.task_done()
            except Empty:
                break
        mmap_idx = self.free_mmaps.pop()
        return mmap_idx, self.pool[mmap_idx]

    def join(self):
        while len(self.free_mmaps) < self.n:
            self.free_mmaps.add(self.free_queue.get())
            self.free_queue.task_done()

    def get(self, idx):
        return self.pool[idx]

    def free(self, idx):
        self.free_queue.put(idx)


def create_pool(creator, size):
    pool = []
    for i in xrange(size):
        proc = creator()
        proc.start()
        pool.append(proc)
    return pool

def shutdown_pool(procs, queue=None, sentinel=None):
    if queue:
        for _ in range(len(procs)):
            queue.put(sentinel)
    for p in procs:
        p.join(timeout=10*60) # 10 min
        if p.is_alive():
            log.warn('could not join process %r, terminating process', p)
            p.terminate()

def estimate_records(files):
    records = 0
    for f in files:
        fsize = os.path.getsize(f)
        if f.endswith('.bz2'):
            fsize *= 11 # observed bzip2 compression factor on osm data
        if f.endswith('.pbf'):
            fsize *= 15 # observed pbf compression factor on osm data
        records += fsize/200

    return int(records)
