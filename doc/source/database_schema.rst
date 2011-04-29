Database Schema
===============

Tables
------

Imposm creates about a dozen tables for the most important features. You can change that with a :ref:`custom mapping <mapping>`.

Below is a list of all default tables. The names are the base names of the tables and the prefix `osm_new_` will be added as a prefix.

Point tables
~~~~~~~~~~~~

- amenities
- places
- transport_points

Polygon tables
~~~~~~~~~~~~~~

- admin
- buildings
- landusages
- aeroways
- waterareas

Linestring tables
~~~~~~~~~~~~~~~~~

- minorroads
- mainroads
- motorways
- railways
- waterways


Generalized tables
~~~~~~~~~~~~~~~~~~

Tables like above but with simplified geometries (tolerance 200m)

- motorways_gen0
- mainroads_gen0
- railways_gen0

Tables like above but with simplified geometries (tolerance 50m)

- motorways_gen1
- mainroads_gen1
- railways_gen1

.. note:: You need to change the tolerance values if your projection does not use meters (e.g. EPSG:4326).

Views
~~~~~

These views combine minorroads, mainroads, motorway and railways.

- roads
- roads_gen0
- roads_gen1


Columns
-------

Each table contains at least four columns:

- osm_id: The ID of the node, way or relation.
- name: The value for the `name` key.
- type: The value of the feature type that was mapped. E.g. `motorway`, `trunk`, `primary`, etc.
- geometry: The geometry itself.

Most tables contain additional columns. For example, all road tables contain `tunnle`, `bridge`, `z_order` and `ref` columns.

For now you need to use the `default mapping configuration <https://bitbucket.org/olt/imposm/src/tip/imposm/defaultmapping.py>`_ as the documentation.

.. .. data:: places
.. 
..   :type: points
..   :tags: place: country, state, region, county, city, town, village,
..     hamlet, suburb, locality
.. 
..   :column z_order: ordered by: country, state, region, county, city, town,
..     village, hamlet, suburb, locality,
..   
..   :column population: integer

