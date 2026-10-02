#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Read the DEM sources and write the compressed cache tiles.

This module is not imported by ``elevation/__init__.py`` on purpose: it pulls in
``rioxarray`` (and therefore ``rasterio``, ``xarray`` and libgdal), which is far
too heavy to pay on every ``import elevation`` or ``eio`` invocation, so the
callers import it lazily where the raster work actually happens.
"""

from pathlib import Path

import rioxarray


def write_cache_tile(source: str | Path, destination: Path) -> None:
    """Write *source* to *destination* as the internal compressed GeoTIFF tile.

    The data, its dtype, its nodata value and its georeferencing are preserved
    unchanged, only compression is added. The predictor must suit the data type:
    horizontal differencing for integers, floating point for floats.

    :param source: Any GDAL readable raster, local or remote.
    :param destination: Path of the cache GeoTIFF, parent folders are created.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    # the default band_as_variable=False always returns a DataArray.
    with rioxarray.open_rasterio(source, mask_and_scale=False) as array:  # type: ignore[union-attr]
        array.rio.to_raster(
            destination,
            recalc_transform=False,
            compress="DEFLATE",
            zlevel=9,
            predictor=3 if array.dtype.kind == "f" else 2,
        )
