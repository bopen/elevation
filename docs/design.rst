
Design
======

This chapter documents the high-level design of the product and
it is intended for developers contributing to the project.

.. note:: **Users of the product need not bother with the following, unless they are curious :)**


Mission and vision
------------------

The project mission is to enable easy management of global digital elevation data.

Target use cases:

#. access DEM data on-demand from well-known repositories
#. download and store efficiently elevation data on large areas

Project goals:

#. data download from well-known repositories
#. compact storage of local data


Software architecture
---------------------

Logical components:

- the datasource Makefile
- the Python API
- the ``eio`` CLI


Version goals
-------------

This project strives to adhere to `semantic versioning <https://semver.org>`_.


1.1.0 (upcoming release)
~~~~~~~~~~~~~~~~~~~~~~~~

To be defined.


1.0.0
~~~~~

Minimal set of features to be operationally useful.
No completeness and no performance guarantees.

- Cache management:

  - new SRTM1 and old SRTM3 global high resolution digital elevation model

  - GNU Makefile for cache management (parallelism and dependency tracking)

  - GDAL VirtualRaster as main entry point
