#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from elevation import util


def test_selfcheck() -> None:
    assert "NAME" not in util.selfcheck({"NAME": "true"})
    assert "NAME" in util.selfcheck({"NAME": "false"})


def test_lock_tiles(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with util.lock_tiles(root, ["a.tiff"]):
        assert (root / "cache" / "a.tiff.lock").exists()


def test_lock_vrt(tmp_path: Path) -> None:
    root = tmp_path / "root"

    with util.lock_vrt(root, "SRTM1_GEOID"):
        assert (root / "SRTM1_GEOID.vrt.lock").exists()


def test_ensure_setup(tmp_path: Path) -> None:
    root = tmp_path / "root"
    created_folders = util.ensure_setup(root)
    assert len(created_folders) == 0
    assert len(list(tmp_path.iterdir())) == 1

    folders = ["etc", "lib"]
    created_folders = util.ensure_setup(root, folders=folders)
    assert len(created_folders) == 2
    assert created_folders[0].name == "etc"
    assert created_folders[1].name == "lib"
    assert len(list(root.iterdir())) == 3

    created_folders = util.ensure_setup(root, folders=folders)
    assert len(created_folders) == 0
    assert len(list(root.iterdir())) == 3
