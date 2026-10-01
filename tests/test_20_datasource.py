#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import elevation
from elevation import datasource


def test_srtm3_tile_ilonlat() -> None:
    # values from https://srtm.csi.cgiar.org/SELECTION/inputCoord.asp
    assert datasource.srtm3_tile_ilonlat(-177.5, 52.5) == (1, 2)
    assert datasource.srtm3_tile_ilonlat(177.5, -47.5) == (72, 22)
    assert datasource.srtm3_tile_ilonlat(10.1, 44.9) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(14.9, 44.9) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(10.1, 40.1) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(14.9, 40.1) == (39, 4)


def test_srtm1_tiles_names() -> None:
    assert list(datasource.srtm1_tiles_names(10.1, 44.9, 10.1, 44.9)) == ["N44E010.tif"]
    # NOTE this also tests int (not float) input
    assert list(datasource.srtm1_tiles_names(10, 44, 11, 45)) == ["N44E010.tif"]


def test_terrain_tiles_names() -> None:
    assert list(datasource.terrain_tiles_names(10.1, 44.9, 10.1, 44.9)) == [
        "N44/N44E010.tif"
    ]
    # NOTE this also tests int (not float) input
    assert list(datasource.terrain_tiles_names(10, 44, 11, 45)) == ["N44/N44E010.tif"]


def test_srtm3_tiles_names() -> None:
    assert next(datasource.srtm3_tiles_names(10.1, 44.9, 10.1, 44.9)).endswith(
        "srtm_39_04.tif"
    )
    assert next(datasource.srtm3_tiles_names(25.50, 58.40, 27.67, 60.06)).endswith(
        "srtm_42_01.tif"
    )
    assert len(list(datasource.srtm3_tiles_names(9.9, 39.1, 15.1, 45.1))) == 9


def test_srtm_ellip_tiles_names() -> None:
    # Check the various subdirs in srtm_ellip
    ds1 = ["North/North_30_60/N44E010_wgs84.tif"]
    ds2 = ["North/North_0_29/N07W074_wgs84.tif"]
    ds3 = ["South/S20E015_wgs84.tif"]
    assert list(datasource.srtm_ellip_tiles_names(10.1, 44.9, 10.1, 44.9)) == ds1
    assert list(datasource.srtm_ellip_tiles_names(-73.99, 7.056, -73.90, 7.660)) == ds2
    assert (
        list(datasource.srtm_ellip_tiles_names(15.931, -19.194, 15.329, -19.961)) == ds3
    )


def test_ensure_tiles(mocker: MockerFixture) -> None:
    mock_check_call = mocker.patch("subprocess.check_call")
    cmd = datasource.ensure_tiles(Path("/tmp"), ["a", "b"])
    assert cmd == ["make", "-C", "/tmp", "download", "ENSURE_TILES=a b"]
    mock_check_call.assert_called_once_with(cmd)


def test_do_clip(mocker: MockerFixture) -> None:
    bounds = (1, 5, 2, 6)
    mock_check_call = mocker.patch("subprocess.check_call")
    cmd = datasource.do_clip(
        path=Path("/tmp"), bounds=bounds, output=Path("/out.tif"), product="SRTM3"
    )
    expected_cmd = ["make", "-C", "/tmp", "clip", "OUTPUT=/out.tif", "PROJWIN=1 6 2 5"]
    assert cmd[:-1] == expected_cmd
    mock_check_call.assert_called_with(cmd)


def test_seed(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    bounds = (13.1, 43.1, 13.9, 43.9)
    mock_check_call = mocker.patch("subprocess.check_call")
    datasource.seed(cache_dir=root, product="SRTM1_GEOID", bounds=bounds)
    assert len(list(root.iterdir())) == 1
    datasource_root = next(iter(root.iterdir()))
    expected_cmd = [
        "make",
        "-C",
        str(datasource_root),
        "download",
        "ENSURE_TILES=N43E013.tif",
    ]
    mock_check_call.assert_any_call(expected_cmd)

    with pytest.raises(RuntimeError):
        datasource.seed(cache_dir=root, bounds=(-180, -90, 180, 90))


def test_build_bounds() -> None:
    raw_bounds = (13.1, 43.1, 13.9, 43.9)
    assert datasource.build_bounds(raw_bounds, margin="0") == raw_bounds

    assert datasource.build_bounds(raw_bounds, margin="0.08") == (
        13.02,
        43.02,
        13.98,
        43.98,
    )
    assert datasource.build_bounds(raw_bounds, margin="10%") == (
        13.02,
        43.02,
        13.98,
        43.98,
    )


def test_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    bounds = (13.1, 43.1, 14.9, 44.9)
    mock_check_call = mocker.patch("subprocess.check_call")
    datasource.clip(cache_dir=root, bounds=bounds, output="out.tif")
    assert len(list(root.iterdir())) == 1
    datasource_root = next(iter(root.iterdir()))
    expected_cmd = [
        "make",
        "-C",
        str(datasource_root),
        "clip",
        f"OUTPUT={Path('out.tif').resolve()}",
        "PROJWIN=13.1 44.9 14.9 43.1",
    ]
    assert mock_check_call.call_args[0][0][:-1] == expected_cmd


def test_clean(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    mock_check_call = mocker.patch("subprocess.check_call")
    datasource.clean(cache_dir=root)
    assert len(list(root.iterdir())) == 1
    datasource_root = next(iter(root.iterdir()))
    mock_check_call.assert_any_call(["make", "-C", str(datasource_root), "clean"])


def test_retired_product() -> None:
    assert issubclass(elevation.ProductRetiredError, KeyError)
    with pytest.raises(elevation.ProductRetiredError) as excinfo:
        datasource.info(product="SRTM1")
    assert str(excinfo.value) == elevation.RETIRED_PRODUCTS["SRTM1"]


def test_cache_dir(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    default = tmp_path / "default"
    override = tmp_path / "override"
    argument = tmp_path / "argument"
    monkeypatch.setattr(datasource, "CACHE_DIR", default)
    mock_check_call = mocker.patch("subprocess.check_call")

    datasource.info()
    expected_cmd = ["make", "-C", str(default / "TERRAIN_TILES"), "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd

    monkeypatch.setenv("EIO_CACHE_DIR", str(override))
    datasource.info()
    expected_cmd = ["make", "-C", str(override / "TERRAIN_TILES"), "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd

    datasource.info(cache_dir=argument)
    expected_cmd = ["make", "-C", str(argument / "TERRAIN_TILES"), "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd


def test_make_options(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    bounds = (13.1, 43.1, 14.9, 44.9)
    mock_check_call = mocker.patch("subprocess.check_call")

    datasource.info(cache_dir=root, make_options="-s")
    expected_cmd = ["make", "-C", str(root / "TERRAIN_TILES"), "-s", "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd

    mock_check_call.reset_mock()
    datasource.clip(cache_dir=root, bounds=bounds, output="out.tif", make_options="-s")
    expected_cmd = ["make", "-C", str(root / "TERRAIN_TILES"), "-s"]
    assert mock_check_call.call_count == 4
    for call in mock_check_call.call_args_list:
        assert call[0][0][:4] == expected_cmd


def test_dataset() -> None:
    assert "id: SRTM3\n" in elevation.dataset("SRTM3")
    text = elevation.dataset()
    assert text.count("id: ") == len(elevation.PRODUCTS)
    assert "GLO-30" not in text
    assert text.endswith("\n")
    # the documents are separated by a blank line and a YAML document separator
    assert text.count("\n---\n") == len(elevation.PRODUCTS) - 1
    assert "\n\n---\nid: SRTM1_GEOID\n" in text
    with pytest.raises(KeyError):
        elevation.dataset("BOGUS")
