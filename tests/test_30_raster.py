#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from elevation import raster

SOURCE = Path(__file__).parent / "data" / "reference.tif"

requires_gdal = pytest.mark.skipif(
    shutil.which("gdal_translate") is None,
    reason="the GDAL command line tools are not installed",
)


def gdalinfo_json(path: Path) -> dict[str, Any]:
    """Return the ``gdalinfo`` report of *path*, with the band checksums."""
    report = subprocess.check_output(["gdalinfo", "-json", "-checksum", str(path)])
    info: dict[str, Any] = json.loads(report)
    return info


def test_write_cache_tile_command(tmp_path: Path, mocker: MockerFixture) -> None:
    check_call = mocker.patch("subprocess.check_call")
    destination = tmp_path / "cache" / "destination.tif"

    cmd = raster.write_cache_tile(SOURCE, destination, srcwin=(0, 0, 1, 1))

    assert cmd == [
        "gdal_translate",
        "-q",
        *raster.TILE_GDAL_OPTIONS.split(),
        "-srcwin",
        "0",
        "0",
        "1",
        "1",
        str(SOURCE),
        str(destination),
    ]
    check_call.assert_called_once_with(cmd)
    assert destination.parent.is_dir()


@requires_gdal
def test_write_cache_tile(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "destination.tif"

    raster.write_cache_tile(SOURCE, destination)

    source = gdalinfo_json(SOURCE)
    tile = gdalinfo_json(destination)
    assert tile["size"] == source["size"]
    assert tile["geoTransform"] == pytest.approx(source["geoTransform"])
    assert tile["coordinateSystem"] == source["coordinateSystem"]
    assert tile["metadata"]["IMAGE_STRUCTURE"]["COMPRESSION"] == "DEFLATE"
    tile_band, source_band = tile["bands"][0], source["bands"][0]
    assert tile_band["type"] == source_band["type"]
    assert tile_band.get("noDataValue") == source_band.get("noDataValue")
    assert tile_band["checksum"] == source_band["checksum"]
