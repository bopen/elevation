#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from elevation import fetch

DATA_DIR = Path(__file__).parent / "data"
REFERENCE = DATA_DIR / "reference.tif"


def test_fetch_tile(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    fetch.fetch_tile(REFERENCE.as_uri(), destination)

    assert destination.read_bytes() == REFERENCE.read_bytes()


def test_fetch_tile_gzip(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    fetch.fetch_tile((DATA_DIR / "reference.tif.gz").as_uri(), destination)

    assert destination.read_bytes() == REFERENCE.read_bytes()


def test_fetch_tile_zip(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    fetch.fetch_tile(
        (DATA_DIR / "reference.zip").as_uri(), destination, member="reference.tif"
    )

    assert destination.read_bytes() == REFERENCE.read_bytes()
