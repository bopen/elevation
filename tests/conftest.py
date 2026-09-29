#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Shared fixtures for the integration tests.

The ``tests/integration_*.py`` modules are never collected by a plain ``pytest``
run, they only run when they are selected explicitly, as the ``integration-tests``
Makefile target does.
"""

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import elevation

REFERENCE_DATA_DIR = Path(__file__).parent / "data"
EPSG_PATTERN = re.compile(r'ID\["EPSG",(\d+)\]')
SYSTEM_READY = "Your system is ready."


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-integration-data",
        action="store_true",
        help="Regenerate the reference data of the integration tests.",
    )


def gdalinfo_json(path: Path) -> dict[str, Any]:
    """Run ``gdalinfo`` with checksums and return the parsed JSON report."""
    cmd = ["gdalinfo", "-json", "-checksum", str(path)]
    info: dict[str, Any] = json.loads(subprocess.check_output(cmd))
    return info


def raster_fingerprint(info: dict[str, Any]) -> dict[str, Any]:
    """Reduce a ``gdalinfo`` report to the fields that identify the raster content.

    Byte equality is deliberately not required: GDAL changed the default GeoTIFF
    block size in 3.11 and zlib releases change the DEFLATE output, so the raster
    extent, grid, CRS, data type, nodata and pixel content are compared instead.
    """
    epsg_match = EPSG_PATTERN.search(info["coordinateSystem"]["wkt"])
    assert epsg_match is not None, "cannot determine the EPSG code of the raster"
    bands = [
        {
            "type": band["type"],
            "noDataValue": band.get("noDataValue"),
            "checksum": band["checksum"],
        }
        for band in info["bands"]
    ]
    return {"size": info["size"], "epsg": int(epsg_match.group(1)), "bands": bands}


def assert_same_raster(produced: Path, reference: Path) -> None:
    produced_info = gdalinfo_json(produced)
    reference_info = gdalinfo_json(reference)
    message = f"{produced} differs from the reference data {reference}"
    fingerprint = raster_fingerprint(produced_info)
    assert fingerprint == raster_fingerprint(reference_info), message
    assert produced_info["geoTransform"] == pytest.approx(
        reference_info["geoTransform"], rel=1e-9
    ), message


@pytest.fixture(scope="session")
def integration_cache_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Cache folder of the downloaded tiles, override with ELEVATION_INTEGRATION_CACHE."""
    override = os.environ.get("ELEVATION_INTEGRATION_CACHE")
    if override:
        return Path(override).expanduser()
    return tmp_path_factory.mktemp("elevation-integration")


@pytest.fixture(scope="session")
def integration_tools() -> None:
    """Fail early if the external tools used by the datasource Makefile are missing."""
    message = elevation.selfcheck()
    if message != SYSTEM_READY:
        pytest.fail(f"Integration tests need a working toolchain:\n{message}")


@pytest.fixture
def integration_data(
    request: pytest.FixtureRequest,
    integration_tools: None,
    integration_cache_dir: Path,
    tmp_path: Path,
) -> Callable[[str, str, tuple[float, float, float, float]], None]:
    """Clip a DEM and compare it with the reference data committed in ``tests/data``."""
    update = request.config.getoption("--update-integration-data")

    def integrate(
        product: str, name: str, bounds: tuple[float, float, float, float]
    ) -> None:
        reference = REFERENCE_DATA_DIR / product.lower() / f"{name}.tif"
        if not update and not reference.exists():
            pytest.skip(f"missing {reference}: run --update-integration-data")
        output = tmp_path / f"{name}.tif"
        elevation.clip(
            bounds=bounds,
            output=output,
            product=product,
            cache_dir=integration_cache_dir,
        )
        if update:
            reference.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(output, reference)
        else:
            assert_same_raster(output, reference)

    return integrate
