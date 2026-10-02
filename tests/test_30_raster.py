#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from elevation import raster

SOURCE = Path(__file__).parent / "data" / "reference.tif"


def test_write_cache_tile(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "destination.tif"

    raster.write_cache_tile(SOURCE, destination)

    assert destination.exists()
