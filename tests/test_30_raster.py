#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import rasterio

from elevation import raster

SOURCE = Path(__file__).parent / "data" / "reference.tif"


def test_write_cache_tile(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "destination.tif"

    raster.write_cache_tile(SOURCE, destination)

    with rasterio.open(SOURCE) as source, rasterio.open(destination) as tile:
        assert tile.dtypes[0] == source.dtypes[0]
        assert tile.count == source.count
        assert tile.nodata == source.nodata
        assert tile.crs == source.crs
        assert tile.transform == source.transform
        assert tile.profile["compress"] == "deflate"
        assert (tile.read() == source.read()).all()
