Data Mapping
============

.. module:: imposm.mapping

The data mapping defines which `OSM feature types <http://wiki.openstreetmap.org/wiki/Map_Features>`_ should be imported in which table. The mapping is described with a Python file using classes from ``imposm.mapping`` package.

See `defaultmapping.py <https://bitbucket.org/olt/imposm/src/tip/imposm/defaultmapping.py>`_ as an example.

Tables
------

There are three classes for the base geometries: ``Points``, ``LineStrings``  and ``Polygons``. All three classes take the same arguments:

``name``
  The name of the resulting table (without any prefix).
  
``mapping``
  The mapping of tags keys and tag values that should be inserted into this table.
  
``fields``
  Mapping of additional tags into table columns.

``field_filter``
  Filter table entries based on field values.

.. _mapping:

mapping
~~~~~~~

Mapping should be a dictionary where the keys are the feature keys (e.g. `highway`, `leisure`, `amenity`, etc.) and the values are tuples of the feature values (e.g. `motorway`, `trunk`, `primary`, etc.).

For a table with bus stops, tram stops and railways stations and halts the mapping should look like the following::

  mapping = {
      'highway': (
          'bus_stop',
      ),
      'railway': (
          'station',
          'halt',
          'tram_stop',
      )
  }


fields
~~~~~~

Fields should be a list (or tuple) of column name and column type tuples. You can use fields to add additional columns to your tables. There are predefined classes for the most common types. These classes can do processing on the values, like converting `1`, `yes` and `true` to ``TRUE`` for boolean columns.

For example::

  fields = (
      ('tunnel', Bool()),
      ('bridge', Bool()),
      ('oneway', Direction()),
      ('ref', String()),
      ('z_order', WayZOrder()),
  )


Most types will use the column name to get the value from the tags. For example, ``('tunnel', Bool())`` will convert the values of the key ``tunnel`` to a boolean.

Name field
^^^^^^^^^^

There is a default field for names if you do not supply a field for the `name` column. You can change the default with :func:`set_default_name_type`.

.. autofunction:: set_default_name_type


Classes
~~~~~~~

.. autoclass:: Points
.. autoclass:: LineStrings
.. autoclass:: Polygons

Example Mapping
---------------

Here is a example of a data mapping that creates a table ``towers``. All nodes with ``man_made=tower`` or ``man_made=water_tower`` will be inserted. It will also create the column ``height`` with the values of the ``height`` tag as integers. [#]_
::

  towers = Points(
    name = 'towers',
    mapping = {
      'man_made': (
        'tower',
        'water_tower',
      )
    }
    fields = (
      ('height', Integer()),
    )
 )

.. [#] It will set the height to ``NULL`` for non-integer values (like values with a unit, ``15 m`` or ``80 ft``). A custom column type ``Height()`` could automatically convert these values to a common unit. This is left as an exercise for the reader.

Column types
------------

.. autoclass:: String()
.. autoclass:: Bool(default=True)
.. autoclass:: Integer
.. autoclass:: Direction
.. autoclass:: OneOfInt
.. autoclass:: ZOrder
.. autoclass:: WayZOrder
.. autoclass:: PseudoArea
.. autoclass:: Name
.. autoclass:: LocalizedName



