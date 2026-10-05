#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from elevation import util


def test_selfcheck() -> None:
    assert "NAME" not in util.selfcheck({"NAME": "true"})
    assert "NAME" in util.selfcheck({"NAME": "false"})


def test_selfcheck_verbose() -> None:
    assert util.selfcheck({"NAME": "true"}, verbose=True) == (
        "Checking 'NAME' ...\nYour system is ready."
    )
    assert util.selfcheck({"NAME": "false"}, verbose=True) == (
        "Checking 'NAME' ...\n'NAME' not found or not usable."
    )


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

    util.ensure_setup(root)

    assert (root / "cache").is_dir()
    # the spool folder is created on demand by the tile download
    assert not (root / "spool").exists()
