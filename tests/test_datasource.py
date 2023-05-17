# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - http://bopen.eu
#

import subprocess

import pytest

from elevation import datasource


def test_srtm3_tile_ilonlat():
    # values from http://srtm.csi.cgiar.org/SELECTION/inputCoord.asp
    assert datasource.srtm3_tile_ilonlat(-177.5, 52.5) == (1, 2)
    assert datasource.srtm3_tile_ilonlat(177.5, -47.5) == (72, 22)
    assert datasource.srtm3_tile_ilonlat(10.1, 44.9) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(14.9, 44.9) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(10.1, 40.1) == (39, 4)
    assert datasource.srtm3_tile_ilonlat(14.9, 40.1) == (39, 4)


def test_srtm1_tiles_names():
    assert list(datasource.srtm1_tiles_names(10.1, 44.9, 10.1, 44.9)) == [
        "N44/N44E010.tif"
    ]
    # NOTE this also tests int (not float) input
    assert list(datasource.srtm1_tiles_names(10, 44, 11, 45)) == ["N44/N44E010.tif"]


def test_srtm3_tiles_names():
    assert next(datasource.srtm3_tiles_names(10.1, 44.9, 10.1, 44.9)).endswith(
        "srtm_39_04.tif"
    )
    assert next(datasource.srtm3_tiles_names(25.50, 58.40, 27.67, 60.06)).endswith(
        "srtm_42_01.tif"
    )
    assert len(list(datasource.srtm3_tiles_names(9.9, 39.1, 15.1, 45.1))) == 9


def test_srtm_ellip_tiles_names():
    # Check the various subdirs in srtm_ellip
    ds1 = ["North/North_30_60/N44E010_wgs84.tif"]
    ds2 = ["North/North_0_29/N07W074_wgs84.tif"]
    ds3 = ["South/S20E015_wgs84.tif"]
    assert list(datasource.srtm_ellip_tiles_names(10.1, 44.9, 10.1, 44.9)) == ds1
    assert list(datasource.srtm_ellip_tiles_names(-73.99, 7.056, -73.90, 7.660)) == ds2
    assert (
        list(datasource.srtm_ellip_tiles_names(15.931, -19.194, 15.329, -19.961)) == ds3
    )


def test_ensure_tiles(mocker):
    mocker.patch("subprocess.check_call")
    cmd = datasource.ensure_tiles("/tmp", ["a", "b"])
    assert cmd == 'make -C /tmp download ENSURE_TILES="a b"'
    subprocess.check_call.assert_called_once_with(cmd, shell=True)


def test_do_clip(mocker):
    bounds = (1, 5, 2, 6)
    mocker.patch("subprocess.check_call")
    cmd = datasource.do_clip(path="/tmp", bounds=bounds, output="/out.tif")
    assert cmd.startswith(
        'make -C /tmp clip OUTPUT="/out.tif" PROJWIN="1 6 2 5" RUN_ID="'
    )
    subprocess.check_call.assert_called_with(cmd, shell=True)


def test_seed(mocker, tmpdir):
    root = tmpdir.join("root")
    bounds = (13.1, 43.1, 13.9, 43.9)
    mocker.patch("subprocess.check_call")
    datasource.seed(cache_dir=str(root), product="SRTM1", bounds=bounds)
    assert len(root.listdir()) == 1
    datasource_root = root.listdir()[0]
    expected_cmd = (
        'make -C %s download ENSURE_TILES="N43/N43E013.tif"' % datasource_root
    )
    subprocess.check_call.assert_any_call(expected_cmd, shell=True)

    with pytest.raises(RuntimeError):
        datasource.seed(
            cache_dir=str(root), product="SRTM1", bounds=(-180, -90, 180, 90)
        )


def test_build_bounds():
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


def test_clip(mocker, tmpdir):
    root = tmpdir.join("root")
    bounds = (13.1, 43.1, 14.9, 44.9)

    class UUID:
        hex = "asd"

    uuid_mock = mocker.Mock()
    uuid_mock.return_value = UUID
    mocker.patch("uuid.uuid4", uuid_mock)
    mocker.patch("subprocess.check_call")
    datasource.clip(
        cache_dir=str(root), product="SRTM1", bounds=bounds, output="out.tif"
    )
    assert len(root.listdir()) == 1
    datasource_root = root.listdir()[0]
    cmd = (
        'make -C %s clip OUTPUT="out.tif" PROJWIN="13.1 44.9 14.9 43.1" RUN_ID="asd"'
        % datasource_root
    )
    subprocess.check_call.assert_any_call(cmd, shell=True)


def test_clean(mocker, tmpdir):
    root = tmpdir.join("root")
    mocker.patch("subprocess.check_call")
    datasource.clean(cache_dir=str(root), product="SRTM1")
    assert len(root.listdir()) == 1
    datasource_root = root.listdir()[0]
    subprocess.check_call.assert_any_call(
        "make -C %s clean " % datasource_root, shell=True
    )
