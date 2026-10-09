#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

import shutil
import subprocess
import urllib.error
from email.message import Message
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from elevation import spatial

DATA_DIR = Path(__file__).parent / "data"
RASTER = DATA_DIR / "reference.tif"
VECTOR = DATA_DIR / "reference.geojson"
BOUNDS = (10.0, 40.0, 11.0, 41.0)


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
    source = f"vrt://{RASTER}?srcwin=0,0,1,1"

    cmd = spatial.call_gdal_translate(source, destination)

    assert cmd == [
        "gdal_translate",
        *spatial.DEFAULT_GDAL_OPTIONS.split(),
        source,
        str(destination),
    ]
    check_call.assert_called_once_with(cmd)
    assert destination.parent.is_dir()


def test_is_not_found(mocker: MockerFixture) -> None:
    url = "https://example.com/N41E012.tif"
    urlopen = mocker.patch("urllib.request.urlopen")
    assert not spatial.is_not_found(url)
    assert urlopen.call_args.args[0].full_url == url
    assert urlopen.call_args.args[0].get_method() == "HEAD"

    urlopen.side_effect = urllib.error.HTTPError(url, 404, "Not Found", Message(), None)
    assert spatial.is_not_found(url)

    urlopen.side_effect = urllib.error.HTTPError(
        url, 401, "Unauthorized", Message(), None
    )
    assert not spatial.is_not_found(url)


@pytest.mark.parametrize(
    "source,url",
    [
        ("/vsicurl/https://h/N41E012.tif", "https://h/N41E012.tif"),
        ("/vsigzip//vsicurl/https://h/N41E012.hgt.gz", "https://h/N41E012.hgt.gz"),
        (
            "/vsizip//vsicurl/https://h/srtm_39_04.zip/srtm_39_04.tif",
            "https://h/srtm_39_04.zip",
        ),
    ],
)
def test_call_gdal_translate_empty_on_notfound(
    tmp_path: Path, mocker: MockerFixture, source: str, url: str
) -> None:
    destination = tmp_path / "destination.tif"
    error = subprocess.CalledProcessError(1, "gdal_translate")
    mocker.patch("subprocess.check_call", side_effect=error)
    is_not_found = mocker.patch("elevation.spatial.is_not_found", return_value=False)

    with pytest.raises(subprocess.CalledProcessError):
        spatial.call_gdal_translate(source, destination, empty_on_notfound=True)
    is_not_found.assert_called_once_with(url)
    assert not destination.exists()

    is_not_found.return_value = True
    with pytest.raises(subprocess.CalledProcessError):
        spatial.call_gdal_translate(source, destination)

    spatial.call_gdal_translate(source, destination, empty_on_notfound=True)
    assert destination.read_bytes() == b""


def test_call_gdal_translate_empty_on_notfound_local(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    is_not_found = mocker.patch("elevation.spatial.is_not_found")

    with pytest.raises(subprocess.CalledProcessError):
        spatial.call_gdal_translate(
            str(RASTER.with_suffix(".bad")), tmp_path / "x.tif", empty_on_notfound=True
        )
    is_not_found.assert_not_called()


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
        *spatial.DEFAULT_GDAL_OPTIONS.split(),
        str(destination),
        *sources,
    ]
    check_call.assert_called_once_with(cmd)
    assert destination.parent.is_dir()


def test_call_gdal_translate(tmp_path: Path) -> None:
    raster = tmp_path / "with space" / RASTER.name
    raster.parent.mkdir()
    shutil.copyfile(RASTER, raster)
    destination = tmp_path / "with space" / "destination.tif"

    spatial.call_gdal_translate(str(raster), destination)

    source = spatial.gdal_json("gdalinfo -json -checksum", str(RASTER))
    tile = spatial.gdal_json("gdalinfo -json -checksum", str(destination))
    assert tile["size"] == source["size"]
    assert tile["geoTransform"] == pytest.approx(source["geoTransform"])
    assert tile["coordinateSystem"] == source["coordinateSystem"]
    tile_band, source_band = tile["bands"][0], source["bands"][0]
    assert tile_band["type"] == source_band["type"]
    assert tile_band.get("noDataValue") == source_band.get("noDataValue")
    assert tile_band["checksum"] == source_band["checksum"]
