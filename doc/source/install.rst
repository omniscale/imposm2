Installation
============

Requirements
------------

Imposm runs with Python 2.5, 2.6 and 2.7 and is tested on Linux and Mac OS X.

Other dependencies are:

- `psycopg2 <http://www.initd.org/psycopg/>`_: PostgreSQL adapter for Python
- `Tokyo Cabinet <http://fallabs.com/tokyocabinet/>`_: File-based key-value database for the internal cache
- `Google Protobuf <http://code.google.com/p/protobuf/>`_: PBF parsing library
- `GEOS <http://trac.osgeo.org/geos/>`_ Geospatial geometries library

Some parts are written as a C extension and so you need to have a C/C++ compiler and the Python header files.

Imposm also requires the following Python packages:

- `imposm.parser <http://dev.omniscale.net/imposm.parser/>`_: XML and PBF parsing sub-package
- `Shapely <http://trac.gispython.org/lab/wiki/Shapely>`_: Python bindings for GEOS. 1.2 or newer is required, >=1.2.10 is recommended.

These Python packages will be installed automatically when you install imposm with ``pip`` or ``easy_install`` (see below).

To install all requirements on Ubuntu::

  sudo aptitude install build-essential python-dev protobuf-compiler \
                        libprotobuf-dev libtokyocabinet-dev python-psycopg2 \
                        libgeos-c1

.. note::

  A lot of geometries in OpenStreetMap are not valid according to the simple feature model and you might get unexpected results when working with these invalid geometries in GEOS or PostGIS. Imposm tries to make all geometries valid with the help of GEOS, but GEOS fails to do this in rare conditions and sometimes even crashes one of the Imposm process. GEOS became much more robust and you should upgrade to at least 3.2 when you notice ``Assertion [...] failed`` errors.

  You can install GEOS into a local directory and let Imposm use it by setting the ``LD_LIBRARY_PATH`` environment variable::

    export LD_LIBRARY_PATH=~/local/lib
    imposm [args]

Installation
------------

Imposm is registered at the `Python Package Index <http://pypi.python.org/pypi/imposm>`_ and you can install it with ``pip`` or ``easy_install``.

::

  sudo aptitude install python-pip
  sudo pip install imposm

You should now be able to start Imposm::

  imposm --help

virtualenv
~~~~~~~~~~

It is recommended to install Imposm into a `virtual Python environment <venv>`_, especially if you are also running other Python based software.

On Ubuntu::

  sudo aptitude install python-virtualenv
  virtualenv venv
  venv/bin/pip install imposm

You can then start Imposm from directly your virtual environment::

  venv/bin/imposm --help

.. _`venv`: http://pypi.python.org/pypi/virtualenv

