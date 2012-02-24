Tutorial
========

The import process is separated into multiple steps.

Create database
---------------

This is step zero, since you have to do it only once. This step creates a PostgreSQL database with the PostGIS extension enabled.

Imposm comes with a little tool that creates all command required to create a new database.

::

  imposm-psqldb --help

You can save the output of ``imposm-psqldb`` and use it as a shell script for the ``postgres`` user::

  imposm-psqldb > create-db.sh
  sudo su postgres
  vim ./create-db.sh # cross check if all path are set
  sh ./create-db.sh

For detailed step-by-step information, read the excellent `OpenStreetMap PostGIS tutorial <http://wiki.openstreetmap.org/wiki/Mapnik/PostGIS>`_.

Reading
-------

The first step is the reading of the OpenStreetMap data. Building the way and relation geometries requires random access to all nodes and ways, but this is not supported by the XML or PBF data formats. Imposm needs to stores all nodes, ways and relations in an intermediary data store that allows random access to all elements. It does this on-disk to keep the memory usage of Imposm low. Imposm uses TokyoCabinet key-value databases for this, which are fast and compact.

::

  imposm --read germany.osm.pbf

Imposm distributes the work across multiple processes to leverage modern multicore CPUs. It can set the number of processes with the ``--concurrency`` option. It defaults to the number of CPU cores on the host system.

::

  imposm --read --concurrency 2 europe.osm.pbf


Cache files
~~~~~~~~~~~

Imposm stores the cache files in the current working directory. You can change that path with ``--cache-dir``. Imposm can merge multiple OSM files into the same cache (e.g. when combining multiple extracts) with the ``--merge-cache`` option or it can overwrite existing caches with ``--overwrite-cache``.


Writing
-------

The second step is the writing of OpenStreetMap features into the database. It reads the features from the cached data from step one, builds all geometries and imports them into the according tables. It overwrites existing tables, :ref:`see below <production_tables>` how to work with existing datasets.

After the import, it creates the generalized tables and views.

You need to tell Imposm the configuration of your database.

::

  imposm --write --database osm --host localhost --user osm

Imposm uses `localhost` for the database host and `osm` for the database user by default. The database name is always required.

You can combine reading and writing::

  imposm --read --write -d osm hamburg.osm.bz2


Optimize
--------

This step is optional and it does some optimization on the created tables. It clusters each table based on the spatial index and does a vacuum analyze on the database.

::

  imposm --optimize -d osm


You can combine reading, writing and optimizing::

  imposm --read --write --optimize -d osm hamburg.osm.bz2


.. _production_tables:

Deploy production tables
------------------------

Since Imposm overwrites existing tables on import, it is recommended to use different table names for import and for production. Imposm supports this with table name prefixes.

Imposm adds ``osm_new_`` as a prefix to all tables names, e.g. ``motorways`` becomes ``osm_new_motorways``. You can change the prefix with the ``--deploy-production-tables``.

To rename all ``osm_new_*`` tables to ``osm_*``::

  imposm -d osm --deploy-production-tables

This renames any existing ``osm_*`` table to ``osm_old_*`` and then renames any ``osm_new_*`` tables to ``osm_*``. Existing backup tables (``osm_old_*``) are removed before. You can then check the results with a PostGIS client or your WMS server.

You can revert to the previous ``osm_*`` tables::

  imposm -d osm --recover-production-tables

And you can remove backup tables (``osm_old_*``)::

  imposm -d osm --remove-backup-tables

You can change the prefixes with ``--table-prefix``, ``--table-prefix-production`` and ``--table-prefix-backup``

Other options
-------------

Mapping
~~~~~~~

You can change the default mapping the the `-m`/`--mapping-file` option. See :doc:`mapping` for more information.

Projection
~~~~~~~~~~

Imposm uses the the web mercator projection (``EPSG:900913``) for the imports. You can change this with the ``--proj`` option.

Multipolygon Relation Building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imposm can ignore large multipolygon relations. You can set the maximum number of rings with the ``IMPOSM_MULTIPOLYGON_MAX_RING`` environment variable. Set to ``0`` process all sizes. The multipolygon builder improved since 2.2.0, so this is not needed anymore.

It will log complex multipolygon relations that take more than 60 seconds to build. You can change this time with the ``IMPOSM_MULTIPOLYGON_REPORT`` environment variable for debugging.
