Global geographic elevation data made easy.
Elevation provides easy download, cache and access of the global datasets:

- ``TERRAIN_TILES``: `Terrain Tiles <https://registry.opendata.aws/terrain-tiles/>`_
  hosted on `Amazon S3 <https://aws.amazon.com/public-data-sets/terrain>`_,
  global 1 arc second (30m) DEMs in the SRTM HGT format
  assembled by Mapzen from several open data providers,
  including NASA/NGA SRTM, USGS 3DEP, EUDEM, ArcticDEM, GMTED2010 and ETOPO1.
- ``SRTM1``: `SRTM 30m Global 1 arc second V003 <https://lpdaac.usgs.gov/products/srtmgl1nv003/>`_
  produced by NASA and NGA hosted on `OpenTopography <https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1>`_.
- ``SRTM3``: `SRTM 90m Digital Elevation Database v4.1 <https://bigdata.cgiar.org/srtm-90m-digital-elevation-database/>`_
  produced by CGIAR-CSI.
- ``SRTM1_ELLIP``: `SRTM GL1 Ellipsoidal (30m heights on the WGS84 ellipsoid) <https://portal.opentopography.org/raster?opentopoID=OTSRTM.082016.4326.1>`_
  hosted on OpenTopography.

Note that any download policies and attribution requirements of the respective providers apply.

.. highlight: console


Installation
------------

Install the `latest version of Elevation <https://pypi.org/project/elevation>`_
from the Python Package Index::

    $ pip install elevation

The following dependencies need to be installed and working:

- `GNU make <https://www.gnu.org/software/make/>`_
- `curl <https://curl.haxx.se/>`_
- unzip
- `gunzip <https://www.gzip.org/>`_
- `GDAL command line tools <https://www.gdal.org/>`_

The following command runs some basic checks and reports common issues::

    $ eio selfcheck
    Your system is ready.

GNU make, curl and unzip come pre-installed with most operating systems.
The best way to install GDAL command line tools varies across operating systems
and distributions, please refer to the
`GDAL install documentation <https://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries>`_.

Note that *elevation* v2.0 requires Python 3.11 or later.
To get the last version supporting Python 2 please use ``pip install "elevation==1.0.6"``.


Command line usage
------------------

Identify the geographic bounds of the area of interest and fetch the DEM with the ``eio`` command.
For example to clip the 30m DEM of Rome, around 41.9N 12.5E, to the ``Rome-30m-DEM.tif`` file
using the default ``TERRAIN_TILES`` product::

    $ eio clip -o Rome-30m-DEM.tif --bounds 12.35 41.8 12.65 42

For the SRTM 30m DEM use::

    $ eio --product SRTM1 clip -o Rome-SRTM1-30m-DEM.tif --bounds 12.35 41.8 12.65 42

For the SRTM 90m DEM use::

    $ eio --product SRTM3 clip -o Rome-90m-DEM.tif --bounds 12.35 41.8 12.65 42

The ``--bounds`` option accepts latitude and longitude coordinates
(more precisely in geodetic coordinates in the WGS84 reference system EPSG:4326 for those who care)
given as ``left bottom right top`` similarly to the ``rio`` command form ``rasterio``.

If you have installed the optional ``reference`` dependencies ``rasterio`` and ``fiona``
(``pip install "elevation[reference]"``)
you can clip a DEM on the same extent of any other geospatial data source supported by GDAL and OGR,
for example if you have a georeferenced image ``MyImage.tif`` you can clip the corresponding DEM with::

    $ eio clip -o MyImage-DEM.tif --reference MyImage.tif  # enable with: $ pip install rasterio

The ``--reference`` option can also take vector data as input::

    $ eio clip -o MyShapefile-DEM.tif --reference MyShapefile.shp  # enable with: $ pip install fiona

The first time an area is accessed Elevation downloads the data tiles from
the AWS S3, CGIAR-CSI or OpenTopography servers and
caches them in GeoTIFF compressed formats,
subsequent accesses to the same and nearby areas are much faster.

The ``clip`` sub-command doesn't allow automatic download of a large amount of DEM tiles,
please refer to the upstream providers' websites to learn the preferred procedures for bulk download.

To clean up stale temporary files and fix the cache in the event of a server error use::

    $ eio clean


Command line reference
----------------------

The ``eio`` command has the following sub-commands and options::

    $ eio --help
    Usage: eio [OPTIONS] COMMAND [ARGS]...

    Options:
      --version                Show the version and exit.
      --product [TERRAIN_TILES|SRTM1|SRTM3|SRTM1_ELLIP]
                               DEM product choice.  [default:
                               TERRAIN_TILES]
      --cache_dir DIRECTORY    Root of the DEM cache folder.  [default:
                               /Users/amici/Library/Caches/elevation2]
      --help                   Show this message and exit.

    Commands:
      clean      Clean up the product cache from temporary files.
      clip       Clip the DEM to given bounds.
      distclean  Remove the product cache entirely.
      info       Show info about the product cache.
      seed       Seed the DEM to given bounds.
      selfcheck  Audit the system for common issues.

The ``clip`` sub-command::

    $ eio clip --help
    Usage: eio clip [OPTIONS]

    Options:
      -o, --output FILE     Path to output file. Existing files will be
                            overwritten.  [default: out.tif]
      --bounds FLOAT...     Output bounds in 'left bottom right top' order.
      -m, --margin TEXT     Decimal degree margin added to the bounds. Use '%' for
                            percent margin.  [default: 0]
      -r, --reference PATH  Use the extent of a reference GDAL/OGR data source as
                            output bounds.
      --help                Show this message and exit.

Defaults can be defined by setting environment variables prefixed with ``EIO``,
e.g. ``EIO_PRODUCT=SRTM3`` and ``EIO_CLIP_MARGIN=10%``.


Python API
----------

Every command has a corresponding API function in the ``elevation`` module:

.. highlight: python

>>> import elevation
>>> # clip the SRTM1 30m DEM of Rome and save it to Rome-DEM.tif
>>> elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output="Rome-DEM.tif")
>>> # clean up stale temporary files and fix the cache in the event of a server error
>>> elevation.clean()


Project resources
-----------------

============= =========================================================
Documentation https://elevation.bopen.eu
Support       https://stackoverflow.com/search?q=python+elevation
Development   https://github.com/bopen/elevation
Download      https://pypi.org/project/elevation
Code quality  .. image:: https://codecov.io/gh/bopen/elevation/branch/main/graph/badge.svg
                :target: https://codecov.io/gh/bopen/elevation
                :alt: Coverage status on Codecov
============= =========================================================


Contributing
------------

Contributions are very welcome. Please see the `CONTRIBUTING`_ document for
the best way to help.
If you encounter any problems, please file an issue along with a detailed description.

.. _`CONTRIBUTING`: https://github.com/bopen/elevation/blob/main/CONTRIBUTING.rst

Authors:

- B-Open Solutions srl - `@bopen <https://github.com/bopen>`_ - https://bopen.eu
- Alessandro Amici - `@alexamici <https://github.com/alexamici>`_


License
-------

Elevation is free and open source software
distributed under the terms of the `Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_.
