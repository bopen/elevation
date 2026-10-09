
2.0.0 (unreleased)
---------------------

- Honour the ``EIO_CACHE_DIR`` environment variable in the Python API, not only in the
  ``eio`` command line.
- Replace the datasource ``Makefile`` with Python: tiles are downloaded with ``fsspec``
  and written to the cache and clipped with ``gdal_translate``, the mosaic is still
  built with ``gdalbuildvrt``.
- Drop the ``make``, ``curl``, ``unzip`` and ``gunzip`` dependencies: tile downloads are
  now sequential.
- Make caching the tiles missing upstream, e.g. ocean tiles, more robust
- Drop the ``reference`` optional dependencies: the bounds of a reference data source
  are read with the ``gdalinfo`` and ``ogrinfo`` command line tools.
- Add the ``--gdal-options`` option and the ``EIO_CLIP_GDAL_OPTIONS`` variable to pass
  GDAL creation options, e.g. ``-co COMPRESS=LZW``, to the clip.
- Download the original SRTM GL1 data from OpenTopography for the ``SRTM1_GEOID`` product.
- Add the ``MAPZEN`` product for the global Mapzen terrain tiles mosaic and make
  it the default product.
- Add the ``GLO-30`` and ``GLO-90`` products for the Copernicus DEM global 30m and 90m
  DSM on the EGM2008 geoid. They are distributed by the Earth Data Hub as a cloud-hosted
  Zarr store that is read in place, one chunk at a time, and cached as GeoTIFF tiles
  like the other products, so the credentials in ``~/.netrc`` are used and GDAL 3.8 or
  later is required.
- Retire the ``SRTM1`` product name: requesting it raises an error pointing to the
  migration notes.
- Accept ``str`` or ``Path`` for all path-valued arguments.
- Resolve relative ``output`` and cache folder paths against the current working
  directory.
- Add the ``eio dataset`` command and the ``elevation.dataset`` function to show the
  STAC metadata of the datasets.
- Add the ``--verbose`` option to ``eio selfcheck`` to show the tools as they are tested.
- Add the ``--max_download_tiles`` option and the ``EIO_SEED_MAX_DOWNLOAD_TILES``
  and ``EIO_CLIP_MAX_DOWNLOAD_TILES`` variables to the ``seed`` and ``clip``
  commands to limit the number of tiles to download, counting only the tiles that
  are not cached yet; the default is raised from 9 to 25.
- Drop support for Python 3.6-3.10: only Python >= 3.11 is supported.
- Move the packaging metadata to ``pyproject.toml`` and remove ``setup.py``
  and ``setup.cfg``.
- Manage the development environment and dependencies with ``uv`` and a ``Makefile``.
- Replace ``black``, ``isort`` and ``flake8`` with ``ruff`` and add ``mypy``
  strict type checking.
- Add lower bounds to the dependencies, checked by the ``minver-tests`` job.
- Build the documentation with Sphinx through ``make docs-build``.
- Modernise the CI with uv-based jobs, pre-commit checks and a PyPI
  trusted-publishing release job.


1.1.3 (2021-04-08)
------------------

- Move to ``setuptools_scm`` for version management.


1.1.2 (2021-03-16)
------------------

- Fixed SRTM3 downloads.
  See `#44 <https://github.com/bopen/elevation/pull/44>`_.


1.1.0 (2020-11-18)
------------------

- Drop Python 2 support. Sorry it is not possible to test it anymore.
- Drop support for python 3.4 and 3.5; add support for 3.7 and 3.8.
- Add support for SRTM1_ELLIP dataset, thanks to `kxtells <https://github.com/kxtells>`_.
  See `#42 <https://github.com/bopen/elevation/pull/42>`_.


1.0.6 (2019-03-01)
------------------

- Updated URL for CGIAR-CSI.


1.0.5 (2018-10-31)
------------------

- Updated dependencies.


1.0.4 (2018-05-18)
------------------

- Updated supported python versions.


1.0.3 (2018-05-16)
------------------

- Docs and dependencies updates.


1.0.2 (2018-05-16)
------------------

- Nothing changed yet.


1.0.1 (2017-01-22)
------------------

- Fixed project metadata.
- Update dependencies versions (using pip-tools).


1.0.0 (2016-11-03)
------------------

- Fix clean command.
  Closes issue `#21 <https://github.com/bopen/elevation/issues/21>`_.
- Add docstrings for all Python API functions.
  Closes issue `#15 <https://github.com/bopen/elevation/issues/15>`_.


0.9.11 (2016-09-23)
-------------------

- Revert the default product back to ``SRTM1`` by downloading from the
 `Amazon Terrain Tiles on AWS service <https://aws.amazon.com/public-data-sets/terrain>`_.
  Closes issue `#18 <https://github.com/bopen/elevation/issues/18>`_.


0.9.10 (2016-09-04)
-------------------

- Change default product to ``SRTM3`` as direct access to ``SRTM1`` has been apparently discontinued.
  See issue `#18 <https://github.com/bopen/elevation/issues/18>`_.
- Added ``-r/--reference`` and ``-m/--margin`` options to define the bounds from a GDAL/OGR data source.
  Install the ``rasterio`` and ``fiona`` packages with ``pip`` to enable it.
  Issue `#14 <https://github.com/bopen/elevation/issues/14>`_.
- Enable reading defaults from environment variables prefixed with ``EIO``,
  e.g. ``EIO_PRODUCT=SRTM3`` and ``EIO_CLIP_MARGIN=10%``.


0.9.9 (2016-04-01)
------------------

- Enforce the no-bulk-download policy.


0.9.8 (2016-03-31)
------------------

- Make ``clean`` remove empty tiles as they may be due to temporary server failures.


0.9.7 (2016-03-30)
------------------

- Fixed user visible documentation.


0.9.6 (2016-03-30)
------------------

- Initial public beta release.
