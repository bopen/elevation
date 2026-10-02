#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Read the DEM sources and write the compressed cache tiles.

This module is not imported by ``elevation/__init__.py`` on purpose: it pulls in
``rasterio`` (and therefore libgdal and ``numpy``), which is far too heavy to pay
on every ``import elevation`` or ``eio`` invocation, so the callers import it
lazily where the raster work actually happens.
"""

from pathlib import Path

import rasterio


def write_cache_tile(source: str | Path, destination: Path) -> None:
    """Write *source* to *destination* as the internal compressed GeoTIFF tile.

    The data, its dtype, its nodata value, its georeferencing and its tags are
    preserved unchanged, only compression is added. The predictor must suit the
    data type: horizontal differencing for integers, floating point for floats.

    :param source: Any GDAL readable raster, local or remote.
    :param destination: Path of the cache GeoTIFF, parent folders are created.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(source) as source_dataset:
        dtype = source_dataset.dtypes[0]
        data = source_dataset.read()
        tags = source_dataset.tags()
        units = source_dataset.units
        profile = {
            "driver": "GTiff",
            "dtype": dtype,
            "count": source_dataset.count,
            "width": source_dataset.width,
            "height": source_dataset.height,
            "crs": source_dataset.crs,
            "transform": source_dataset.transform,
            "nodata": source_dataset.nodata,
            "compress": "DEFLATE",
            "zlevel": 9,
            "predictor": 3 if dtype.startswith("float") else 2,
        }
    with rasterio.open(destination, "w", **profile) as destination_dataset:
        # the metadata is set before the data because GDAL writes a smaller
        # file, by around 0.7%, when it does not have to update the directory
        destination_dataset.update_tags(**tags)
        for index, unit in enumerate(units, start=1):
            if unit is not None:
                destination_dataset.set_band_unit(index, unit)
        destination_dataset.write(data)
