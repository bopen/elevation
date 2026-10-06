#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

import shutil
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from elevation import spatial

DATA_DIR = Path(__file__).parent / "data"
RASTER = DATA_DIR / "reference.tif"
VECTOR = DATA_DIR / "reference.geojson"
BOUNDS = (10.0, 40.0, 11.0, 41.0)

requires_gdal = pytest.mark.skipif(
    shutil.which("gdal_translate") is None,
    reason="the GDAL command line tools are not installed",
)


def test_import_bounds_raster() -> None:
    assert spatial.import_bounds(RASTER) == BOUNDS


def test_import_bounds_vector() -> None:
    assert spatial.import_bounds(VECTOR) == BOUNDS


def test_import_bounds_invalid() -> None:
    with pytest.raises(RuntimeError):
        spatial.import_bounds(RASTER.with_suffix(".bad"))


def test_selfcheck() -> None:
    assert "NAME" not in spatial.selfcheck({"NAME": "true"})
    assert "NAME" in spatial.selfcheck({"NAME": "false"})


def test_selfcheck_verbose() -> None:
    assert spatial.selfcheck({"NAME": "true"}, verbose=True) == (
        "Checking 'NAME' ...\nYour system is ready."
    )
    assert spatial.selfcheck({"NAME": "false"}, verbose=True) == (
        "Checking 'NAME' ...\n'NAME' not found or not usable."
    )


def test_call_gdal_translate_command(tmp_path: Path, mocker: MockerFixture) -> None:
    check_call = mocker.patch("subprocess.check_call")
    destination = tmp_path / "cache" / "destination.tif"
    source = f"-srcwin 0 0 1 1 {RASTER}"

    cmd = spatial.call_gdal_translate(source, destination)

    assert cmd == [
        "gdal_translate",
        *spatial.DEFAULT_GDAL_OPTIONS.split(),
        *source.split(),
        str(destination),
    ]
    check_call.assert_called_once_with(cmd)
    assert destination.parent.is_dir()


def test_call_gdalbuildvrt_command(tmp_path: Path, mocker: MockerFixture) -> None:
    check_call = mocker.patch("subprocess.check_call")
    destination = tmp_path / "cache" / "destination.vrt"
    sources = [
        str(tmp_path / "cache" / "N41E012.tif"),
        str(tmp_path / "cache" / "N42E012.tif"),
    ]

    cmd = spatial.call_gdalbuildvrt(sources, destination)

    assert cmd == [
        "gdalbuildvrt",
        *spatial.VRT_GDAL_OPTIONS.split(),
        str(destination),
        *sources,
    ]
    check_call.assert_called_once_with(cmd)
    assert destination.parent.is_dir()


@requires_gdal
def test_call_gdal_translate(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "destination.tif"

    spatial.call_gdal_translate(str(RASTER), destination)

    source = spatial.gdal_report(["gdalinfo", "-json", "-checksum", str(RASTER)])
    tile = spatial.gdal_report(["gdalinfo", "-json", "-checksum", str(destination)])
    assert tile["size"] == source["size"]
    assert tile["geoTransform"] == pytest.approx(source["geoTransform"])
    assert tile["coordinateSystem"] == source["coordinateSystem"]
    tile_band, source_band = tile["bands"][0], source["bands"][0]
    assert tile_band["type"] == source_band["type"]
    assert tile_band.get("noDataValue") == source_band.get("noDataValue")
    assert tile_band["checksum"] == source_band["checksum"]
