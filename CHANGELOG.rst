
1.1.4 (unreleased)
------------------

- Fix the ``eio distclean`` crash when the cache holds sub-folders.
- Fix the ``eio clip`` crash when neither ``--bounds`` nor ``--reference`` is given.
- Resolve a relative ``output`` against the current working directory.


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
- Drop support for python 3.4 and 3.5 add support for 3.7 and 3.8.
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
- Add docstrings for all Pyhton API functions.
  Closes issue `#15 <https://github.com/bopen/elevation/issues/15>`_.


0.9.11 (2016-09-23)
-------------------

- Revert the default product back to ``SRTM1`` by downloading from the
 `Amazon Terrain Tiles on AWS servcie <https://aws.amazon.com/public-data-sets/terrain>`_.
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
