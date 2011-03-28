Imposm
======

Imposm is an importer for OpenStreetMap data. It reads XML and PBF files and can import the data into PostgreSQL/PostGIS databases.

It is designed to create databases that are optimized for rendering/WMS services.

It is developed and supported by `Omniscale <http://omniscale.com>`_, runs on Linux or Mac OS X and is released as open source under the `Apache Software License 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`_.

Features
--------

Custom database schemas
  It creates tables for different data types. This allows easier styling and better performance for rendering in WMS or tile services.

Multiple CPU/core support
  Impsom is parallel from the ground up. It distributes parsing and processing to multiple CPUs/cores.
  
Unify values
  For example, the boolean values `1`, `on`, `true` and `yes` all become ``TRUE``.

Filter by tags and values
  It only imports data you are going to render/use.

Efficient nodes cache
  It is necessary to store all nodes to build ways and relations. Imposm uses a file-based key-value database (`Tokyo Cabinet <http://fallabs.com/tokyocabinet/>`_) to cache this data. This reduces the memory usage.

Generalized tables
  It can automatically create tables with lower spatial resolutions, perfect for rendering large road networks in low resolutions for example.

Union views
  It can create views that combine multiple tables.

Limitations
-----------

It does not support differential updates (aka minutely database) at the moment.

It only supports PostGIS databases, but the code is quite modular (only a single file contains PostGIS dependent code) and support for SpatialLite, Oracle, etc. can be implemented.

It is quite efficient with memory. You can import 1GB .osm.bz2 (~Germany) on systems with 2GB RAM and Europe (~5GB PBF) works fine on a system with 8GB RAM. Larger imports (planet.osm) are still possible but will take longer if you don't have 16BG or more.

The multipolygon relation building is robust and returns valid polygons for nearly all relations, but it is not efficient for polygons with more than 1000 rings.

There is room for improvements for all of these limitations. Let us know if you want to help out (either with code, or with funding).

.. It is a lossy importer: It does not import every tag, but only tags configured with the data mapping. Topological information, required for routing, are also lost during import. This is intended, because Imposm is designed for rendering services.


Support
-------

There is a `mailing list at Google Groups <http://groups.google.com/group/imposm>`_ for all questions. You can subscribe by sending an email to: imposm+subscribe@googlegroups.com

For commercial support `contact Omniscale <http://omniscale.com/contact>`_.

Contents
--------

.. toctree::
   :maxdepth: 2

   install
   tutorial
   database_schema
   mapping


.. Indices and tables
.. ==================
.. 
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

