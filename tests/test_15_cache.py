#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from elevation import cache


def test_lock_tiles(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with cache.lock_tiles(root, ["a.tiff"]):
        assert (root / "cache" / "a.tiff.lock").exists()


def test_lock_vrt(tmp_path: Path) -> None:
    root = tmp_path / "root"

    with cache.lock_vrt(root, "SRTM1_GEOID"):
        assert (root / "SRTM1_GEOID.vrt.lock").exists()


def test_ensure_setup(tmp_path: Path) -> None:
    root = tmp_path / "root"

    cache.ensure_setup(root)

    assert (root / "cache").is_dir()
    # the spool folder is created on demand by the tile download
    assert not (root / "spool").exists()
