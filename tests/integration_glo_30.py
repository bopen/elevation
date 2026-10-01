#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Integration tests for the ``GLO-30`` product, i.e. Copernicus DEM 30m.

The product is a north-up Zarr store on the Earth Data Hub that is read in place
instead of being downloaded, so these tests also cover the Earth Data Hub
credentials in ``~/.netrc`` and the ``ZARR:`` GDAL connection string.
The regions are the same as the ones of ``GLO-90`` and ``SRTM3``, so the three
reference datasets cover the same areas and can be cross-checked.
Each test clips a ~100x100 pixel DEM and compares it with the reference GeoTIFF
committed in ``tests/data/GLO-30``, see ``CONTRIBUTING.rst`` to regenerate them.
"""

from collections.abc import Callable

SIZE = 100 / 3600

IntegrationData = Callable[[str, str, tuple[float, float, float, float]], None]


def test_ne_rome(integration_data: IntegrationData) -> None:
    bounds = (12.4, 41.8, 12.4 + SIZE, 41.8 + SIZE)
    integration_data("GLO-30", "ne_rome", bounds)


def test_nw_san_francisco(integration_data: IntegrationData) -> None:
    bounds = (-122.44, 37.74, -122.44 + SIZE, 37.74 + SIZE)
    integration_data("GLO-30", "nw_san_francisco", bounds)


def test_se_sydney(integration_data: IntegrationData) -> None:
    bounds = (151.16, -33.9, 151.16 + SIZE, -33.9 + SIZE)
    integration_data("GLO-30", "se_sydney", bounds)


def test_sw_santiago(integration_data: IntegrationData) -> None:
    bounds = (-70.6, -33.42, -70.6 + SIZE, -33.42 + SIZE)
    integration_data("GLO-30", "sw_santiago", bounds)
