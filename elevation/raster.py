#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Write the tiles of the internal cache as compressed GeoTIFF.

The cache tiles are written with ``gdal_translate``, the same tool that clips the
final product, so the whole pipeline stays in the GDAL command line domain and any
GDAL readable source works, ``/vsicurl/`` and ``/vsizip/`` paths included.
"""

import subprocess
from collections.abc import Sequence
from pathlib import Path

# the VRT mosaic reads the tiles whole, the options only trade size for speed
TILE_GDAL_OPTIONS = "-co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2"


def write_cache_tile(
    source: str | Path,
    destination: Path,
    *,
    srcwin: Sequence[int] | None = None,
    gdal_options: str = TILE_GDAL_OPTIONS,
) -> list[str]:
    """Write *source* to *destination* as the internal compressed GeoTIFF tile.

    The data, its dtype, its nodata value, its georeferencing and its metadata are
    preserved unchanged, only compression is added. ``PREDICTOR=2`` in the default
    options suits the integer products, pass ``PREDICTOR=3`` for float ones.

    :param source: Any GDAL readable raster, local or remote.
    :param destination: Path of the cache GeoTIFF, parent folders are created.
    :param srcwin: Window of *source* to write, e.g. a single ``Zarr`` chunk.
    :param gdal_options: GDAL creation options of the cache tile.
    :return: The command arguments.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    window = [] if srcwin is None else ["-srcwin", *map(str, srcwin)]
    cmd = [
        "gdal_translate",
        "-q",
        *gdal_options.split(),
        *window,
        str(source),
        str(destination),
    ]
    subprocess.check_call(cmd)
    return cmd
