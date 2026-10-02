#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Integration tests for the ``MAPZEN`` product, i.e. the Mapzen mosaic.

This mosaic is assembled from several upstream providers, the regions below are
chosen to cover plain SRTM data, the USGS 3DEP data in the United States and the
high latitudes that no SRTM product covers.
Each test clips a ~100x100 pixel DEM and compares it with the reference GeoTIFF
committed in ``tests/data/MAPZEN``, see ``CONTRIBUTING.rst``.
"""

from collections.abc import Callable

SIZE = 100 / 3600

IntegrationData = Callable[[str, str, tuple[float, float, float, float]], None]


def test_ne_rome(integration_data: IntegrationData) -> None:
    bounds = (12.4, 41.8, 12.4 + SIZE, 41.8 + SIZE)
    integration_data("MAPZEN", "ne_rome", bounds)


def test_nw_san_francisco(integration_data: IntegrationData) -> None:
    bounds = (-122.44, 37.74, -122.44 + SIZE, 37.74 + SIZE)
    integration_data("MAPZEN", "nw_san_francisco", bounds)


def test_nw_iceland(integration_data: IntegrationData) -> None:
    # above 60N no SRTM product provides data, only the mosaic does
    bounds = (-19.44, 64.56, -19.44 + SIZE, 64.56 + SIZE)
    integration_data("MAPZEN", "nw_iceland", bounds)


def test_se_sydney(integration_data: IntegrationData) -> None:
    bounds = (151.16, -33.9, 151.16 + SIZE, -33.9 + SIZE)
    integration_data("MAPZEN", "se_sydney", bounds)


def test_sw_santiago(integration_data: IntegrationData) -> None:
    bounds = (-70.6, -33.42, -70.6 + SIZE, -33.42 + SIZE)
    integration_data("MAPZEN", "sw_santiago", bounds)
