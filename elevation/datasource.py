#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import os
import shutil
from collections.abc import Callable, Iterator, Sequence
from importlib import resources
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import appdirs

from . import cache, spatial

__all__ = [
    "CACHE_DIR",
    "DEFAULT_GDAL_OPTIONS",
    "DEFAULT_OUTPUT",
    "DEFAULT_PRODUCT",
    "MARGIN",
    "PRODUCTS",
    "RETIRED_PRODUCTS",
    "ProductRetiredError",
    "clean",
    "clip",
    "dataset",
    "distclean",
    "info",
    "resolve_cache_dir",
    "seed",
]

CACHE_DIR: str = appdirs.user_cache_dir("elevation", "bopen")
DEFAULT_OUTPUT = "out.tif"
DEFAULT_GDAL_OPTIONS = "-co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2"
CACHE_EXT = ".tif"
MARGIN = "0"

# NOTE:
#   0.0001388888889 == 0.5" is half pixel for DEMs with 1" spacing (DTED L2)
#   0.0004166666667 == 1.5" is half pixel for DEMs with 3" spacing (DTED L1)
EDH_L2_CHUNK_INDECES_TRANSFORM = (-180.0001388888889, 1.0, 90.00013888888888, -0.5)
EDH_L1_CHUNK_INDECES_TRANSFORM = (-180.00041666666667, 2.0, 90.00041666666667, -2.0)
DTED_L2_TILE_INDECES_TRANSFORM = (-0.0001388888889, 1.0, -0.0001388888889, 1.0)
CGIAR_L1_TILE_INDECES_TRANSFORM = (-185.0004166666667, 5.0, 65.0004166666667, -5.0)


def resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    """Return the DEM cache folder to use, as an absolute path.

    The ``cache_dir`` argument takes precedence over the ``EIO_CACHE_DIR`` environment
    variable, that takes precedence over the ``CACHE_DIR`` default.
    """
    if cache_dir is None:
        cache_dir = os.environ.get("EIO_CACHE_DIR") or CACHE_DIR
    return Path(cache_dir).resolve()


def latlon_to_indeces(
    transform: tuple[float, float, float, float], lon: float, lat: float
) -> tuple[int, int]:
    lon_start, lon_step, lat_start, lat_step = transform
    ilon = math.floor((lon - lon_start) / lon_step)
    ilat = math.floor((lat - lat_start) / lat_step)
    return ilon, ilat


Tile = tuple[tuple[int, int], str]


def dted_l2_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}.tif",
) -> Iterator[Tile]:
    ileft, itop = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, left, top)
    iright, ibottom = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, right, bottom)
    # special case often used *integer* top and right to avoid downloading unneeded tiles
    if isinstance(top, int) or top.is_integer():
        itop -= 1
    if isinstance(right, int) or right.is_integer():
        iright -= 1
    for ilon in range(ileft, iright + 1):
        slon = f"{'E' if ilon >= 0 else 'W'}{abs(ilon):03d}"
        for ilat in range(ibottom, itop + 1):
            slat = f"{'N' if ilat >= 0 else 'S'}{abs(ilat):02d}"
            yield (ilon, ilat), tile_name_template.format(**locals())


def cgiar_l1_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_template: str = "srtm_{ilon:02d}_{ilat:02d}.tif",
) -> Iterator[Tile]:
    ileft, itop = latlon_to_indeces(CGIAR_L1_TILE_INDECES_TRANSFORM, left, top)
    iright, ibottom = latlon_to_indeces(CGIAR_L1_TILE_INDECES_TRANSFORM, right, bottom)
    for ilon in range(ileft, iright + 1):
        for ilat in range(itop, ibottom + 1):
            if ilon > 0 and ilat > 0:
                yield (ilon, ilat), tile_template.format(**locals())


def srtm_ellip_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}_wgs84.tif",
) -> Iterator[Tile]:
    ileft, itop = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, left, top)
    iright, ibottom = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, right, bottom)
    # special case often used *integer* top and right to avoid downloading unneeded tiles
    if isinstance(top, int) or top.is_integer():
        itop -= 1
    if isinstance(right, int) or right.is_integer():
        iright -= 1
    for ilon in range(ileft, iright + 1):
        slon = f"{'E' if ilon >= 0 else 'W'}{abs(ilon):03d}"
        for ilat in range(ibottom, itop + 1):
            slat = f"{'N' if ilat >= 0 else 'S'}{abs(ilat):02d}"
            subdir = "North" if ilat >= 0 else "South"
            north_subdir = "North_30_60" if ilat >= 30 else "North_0_29"
            fname = tile_name_template.format(**locals())

            if ilat >= 0:
                yield (ilon, ilat), f"{subdir}/{north_subdir}/{fname}"
            else:
                yield (ilon, ilat), f"{subdir}/{fname}"


def prepare_tile_download_uncompress(
    tile_name: str,
    spool: Path,
    datasource_url: str,
    tile_ext: str = ".tif",
    compressed_ext: str | None = None,
    **kwargs: Any,
) -> tuple[str, Path | None]:
    source, spool_name, member = tile_source(
        datasource_url, tile_name, tile_ext, compressed_ext
    )
    spooled = spool / spool_name
    fetch_tile(source, spooled, member=member)
    return str(spooled), spooled


def zarr_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    transform: tuple[float, float, float, float],
) -> Iterator[Tile]:
    ileft, itop = latlon_to_indeces(transform, left, top)
    iright, ibottom = latlon_to_indeces(transform, right, bottom)
    for ilon in range(ileft, iright + 1):
        for ilat in range(itop, ibottom + 1):
            if ilon >= 0 and ilat >= 0:
                yield (ilon, ilat), f"{ilat}/{ilon}.tif"


def prepare_tile_zarr(
    datasource_url: str,
    variable_path: str,
    ilat: int,
    ilon: int,
    chunks: tuple[int, int],
    **kwargs: Any,
) -> tuple[str, Path | None]:
    srcwin = [ilon * chunks[0], ilat * chunks[1], chunks[0], chunks[1]]
    gdal_source = (
        f"-srcwin {' '.join(map(str, srcwin))} "
        + f'ZARR:"/vsicurl/{datasource_url}":{variable_path}'
    )
    return gdal_source, None


class DatasourceSpec(TypedDict):
    # a local product has one URL per tile (``tiles``), a remote one is a
    # single chunked source (``grid``): the key tells the two apart
    cached_tiles: Callable[..., Iterator[Tile]]
    # keyword arguments for ``cached_tiles``, e.g. the tile name template
    # of a product that keeps its tiles in subfolders
    cached_tiles_kwargs: NotRequired[dict[str, Any]]
    # prepare the tile for GDAL, downloading it or reading the window of the
    # chunked source, next to the spool file to remove once it is cached
    prepare_tile: Callable[..., tuple[str, Path | None]]
    # keyword arguments for ``prepare_tile``: the datasource URL and the path
    # of the variable in the store, the source extension, the archive the
    # provider serves it in, the chunk size
    prepare_tile_kwargs: dict[str, Any]
    tile_gdal_options: NotRequired[str]


MAPZEN_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_download_uncompress,
    "prepare_tile_kwargs": {
        "datasource_url": "https://s3.amazonaws.com/elevation-tiles-prod/skadi",
        "tile_ext": ".hgt",
        "compressed_ext": ".hgt.gz",
    },
    "cached_tiles": dted_l2_tiles,
    "cached_tiles_kwargs": {"tile_name_template": "{slat}/{slat}{slon}.tif"},
}

SRTM1_GEOID_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_download_uncompress,
    "prepare_tile_kwargs": {
        "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm",
    },
    "cached_tiles": dted_l2_tiles,
}

SRTM1_ELLIP_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_download_uncompress,
    "prepare_tile_kwargs": {
        "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm",
    },
    "cached_tiles": srtm_ellip_tiles,
}

SRTM3_SPEC: DatasourceSpec = {
    "prepare_tile_kwargs": {
        "datasource_url": "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF",
        "compressed_ext": ".zip",
    },
    "cached_tiles": cgiar_l1_tiles,
    "prepare_tile": prepare_tile_download_uncompress,
}

GLO_30_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_zarr,
    "prepare_tile_kwargs": {
        "datasource_url": "https://data.earthdatahub.destine.eu/copernicus-dem/GLO-30-v1.zarr",
        "variable_path": "/dsm",
        "chunks": (3600, 1800),
    },
    "tile_gdal_options": spatial.FLOAT_TILE_GDAL_OPTIONS,
    "cached_tiles": zarr_tiles,
    "cached_tiles_kwargs": {"transform": EDH_L2_CHUNK_INDECES_TRANSFORM},
}

GLO_90_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_zarr,
    "prepare_tile_kwargs": {
        "datasource_url": "https://data.earthdatahub.destine.eu/copernicus-dem/GLO-90-v1.zarr",
        "variable_path": "/dsm",
        "chunks": (2400, 2400),
    },
    "tile_gdal_options": spatial.FLOAT_TILE_GDAL_OPTIONS,
    "cached_tiles": zarr_tiles,
    "cached_tiles_kwargs": {"transform": EDH_L1_CHUNK_INDECES_TRANSFORM},
}

PRODUCTS_SPECS: dict[str, DatasourceSpec] = {
    "MAPZEN": MAPZEN_SPEC,
    "GLO-30": GLO_30_SPEC,
    "GLO-90": GLO_90_SPEC,
    "SRTM1_GEOID": SRTM1_GEOID_SPEC,
    "SRTM1_ELLIP": SRTM1_ELLIP_SPEC,
    "SRTM3": SRTM3_SPEC,
}

PRODUCTS = list(PRODUCTS_SPECS)
DEFAULT_PRODUCT = PRODUCTS[0]


class ProductRetiredError(KeyError):
    """Raised when a product label retired in elevation 2.0 is requested.

    Subclasses ``KeyError``, like an unknown product label, but renders the migration
    message without the ``repr`` quoting that ``KeyError`` adds.
    """

    def __str__(self) -> str:
        return str(self.args[0])


RETIRED_PRODUCTS: dict[str, str] = {
    "SRTM1": (
        "The 'SRTM1' product was renamed in elevation 2.0: the global terrain tiles "
        "mosaic it used to download is now the 'MAPZEN' product (the default) and "
        "the OpenTopography SRTM GL1 product is now 'SRTM1_GEOID'. See "
        "https://elevation.bopen.eu/migration.html"
    ),
}


def tile_source(
    datasource_url: str,
    tile_name: str,
    tile_ext: str = ".tif",
    compressed_ext: str | None = None,
) -> tuple[str, str, str | None]:
    """Return the ``(url, spool_name, member)`` of the tile for *tile_name*.

    *tile_name* is the cache tile name, always a ``.tif``; the spool name is the
    same tile with the source extension (``tile_ext``) and the remote name adds
    the ``compressed_ext`` when the source is compressed. The member is the file
    to read inside a ``.zip`` archive and ``None`` otherwise.
    """
    stem = tile_name.removesuffix(CACHE_EXT)
    spool_name = f"{stem}{tile_ext}"
    remote = spool_name if compressed_ext is None else f"{stem}{compressed_ext}"
    member = Path(spool_name).name if compressed_ext == ".zip" else None
    return f"{datasource_url}/{remote}", spool_name, member


def fetch_tile(source: str, destination: Path, *, member: str | None = None) -> None:
    """Fetch *source* and write it uncompressed to *destination*.

    A ``.gz`` source is gunzipped, a ``.zip`` source is read at *member*, any
    other source is copied as it is. The tile is written through a ``.temp``
    sibling and moved in place, so a failed download never leaves a half written
    tile behind.

    :param source: Any fsspec URL, e.g. ``https://...`` or ``s3://...``.
    :param destination: Path of the uncompressed tile, parent folders are created.
    :param member: Name of the file to extract from a ``.zip`` source.
    """
    # imported here to keep ``import elevation`` and ``eio`` free of the fsspec cost
    import fsspec

    destination.parent.mkdir(parents=True, exist_ok=True)
    if member is None:
        stream = fsspec.open(source, "rb", compression="infer")
    else:
        stream = fsspec.open(f"zip://{member}::{source}", "rb")
    temporary = destination.with_name(f"{destination.name}.temp")
    try:
        with stream as remote, temporary.open("wb") as local:
            shutil.copyfileobj(remote, local)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_tiles(
    root: Path,
    tiles: Sequence[Tile],
    prepare_tile: Callable[..., tuple[str, Path | None]],
    gdal_options: str = spatial.INT_TILE_GDAL_OPTIONS,
    **kwargs: Any,
) -> None:
    """Fetch and cache *tiles*, skipping the tiles already in the cache.

    A tile is a ``(name, window)`` pair: a tile with a window is read in place
    from ``datasource_url``, a tile without one is downloaded whole from its own
    URL and goes through the spool.
    """
    for (ilon, ilat), tile_name in tiles:
        cached = root / "cache" / tile_name
        if cached.exists() and cached.stat().st_size > 0:
            continue

        # prepare the data if GDAL cannot download it / read it as it is
        source, spooled = prepare_tile(
            tile_name=tile_name, spool=root / "spool", ilat=ilat, ilon=ilon, **kwargs
        )

        # convert the data to the internal cache format
        ready = root / "spool/ready" / tile_name
        spatial.call_gdal_translate(source, ready, options=gdal_options)
        if spooled is not None:
            spooled.unlink(missing_ok=True)

        # finally move the data inside the cache. The move is atomic in most cases
        cached.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(ready, cached)


def build_vrt(root: Path, product: str) -> list[str]:
    """Build the ``<product>.vrt`` mosaic over the non empty cache tiles."""
    tiles = []
    for tile in (root / "cache").rglob("*.tif"):
        if tile.stat().st_size > 0:
            tiles.append(str(tile))
    options = "-q -overwrite"
    cmd = spatial.call_gdalbuildvrt(sorted(tiles), root / f"{product}.vrt", options)
    return cmd


def ensure_setup(
    cache_dir: str | Path | None, product: str
) -> tuple[Path, DatasourceSpec]:
    if product in RETIRED_PRODUCTS:
        raise ProductRetiredError(RETIRED_PRODUCTS[product])
    datasource_root = resolve_cache_dir(cache_dir) / product
    spec = PRODUCTS_SPECS[product]
    cache.ensure_setup(datasource_root)
    return datasource_root, spec


def do_clip(
    path: Path,
    bounds: tuple[float, float, float, float],
    output: Path,
    product: str,
    gdal_options: str = DEFAULT_GDAL_OPTIONS,
) -> list[str]:
    left, bottom, right, top = bounds
    options = f"-q {gdal_options} -projwin {left} {top} {right} {bottom}"
    source = str(path / f"{product}.vrt")
    with cache.lock_vrt(path, product):
        cmd = spatial.call_gdal_translate(source, output, options=options)
    return cmd


def seed(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    bounds: tuple[float, float, float, float] | None = None,
    max_download_tiles: int = 9,
) -> Path:
    """Seed the DEM to given bounds.

    A remote product is not downloaded whole: only the chunks of the store that
    cover the bounds are read in place and cached.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param bounds: Output bounds in 'left bottom right top' order.
    :param max_download_tiles: Maximum number of tiles to process.
    """
    if bounds is None:
        raise TypeError("bounds must be supplied")
    datasource_root, spec = ensure_setup(cache_dir, product)
    cached_tiles = spec["cached_tiles"]
    cached_tiles_kwargs = spec.get("cached_tiles_kwargs", {})
    tiles = list(cached_tiles(*bounds, **cached_tiles_kwargs))
    # FIXME: emergency hack to enforce the no-bulk-download policy
    if len(tiles) > max_download_tiles:
        raise RuntimeError(
            f"Too many tiles: {len(tiles)}. Please consult the "
            "providers' websites for how to bulk download tiles."
        )

    prepare_tile = spec["prepare_tile"]
    prepare_tile_kwargs = spec.get("prepare_tile_kwargs", {})
    with cache.lock_tiles(datasource_root, [name for _, name in tiles]):
        ensure_tiles(
            datasource_root,
            tiles,
            prepare_tile=prepare_tile,
            gdal_options=spec.get("tile_gdal_options", spatial.INT_TILE_GDAL_OPTIONS),
            **prepare_tile_kwargs,
        )

    with cache.lock_vrt(datasource_root, product):
        build_vrt(datasource_root, product)

    return datasource_root


def build_bounds(
    bounds: tuple[float, float, float, float], margin: str = MARGIN
) -> tuple[float, float, float, float]:
    left, bottom, right, top = bounds
    if margin.endswith("%"):
        margin_percent = float(margin[:-1])
        margin_lon = (right - left) * margin_percent / 100
        margin_lat = (top - bottom) * margin_percent / 100
    else:
        margin_lon = margin_lat = float(margin)
    bounds = (
        left - margin_lon,
        bottom - margin_lat,
        right + margin_lon,
        top + margin_lat,
    )
    return bounds


def clip(
    bounds: tuple[float, float, float, float],
    output: str | Path = DEFAULT_OUTPUT,
    margin: str = MARGIN,
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    gdal_options: str = DEFAULT_GDAL_OPTIONS,
) -> None:
    """Clip the DEM to given bounds.

    :param bounds: Output bounds in 'left bottom right top' order.
    :param output: Path to output file. Existing files will be overwritten.
    :param margin: Decimal degree margin added to the bounds. Use '%' for percent margin.
    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param gdal_options: GDAL creation options of the output file.
    """
    output = Path(output).resolve()
    bounds = build_bounds(bounds, margin=margin)
    datasource_root = seed(cache_dir=cache_dir, product=product, bounds=bounds)
    do_clip(datasource_root, bounds, output, product=product, gdal_options=gdal_options)


def dataset(dataset: str | None = None) -> str:
    """Show the STAC metadata of the datasets.

    :param dataset: Dataset choice, all the products if not given.
    :return: The dataset STAC files, in PRODUCTS order, as a stream of YAML documents.
    """
    if dataset is not None and dataset not in PRODUCTS:
        raise KeyError(dataset)
    names = PRODUCTS if dataset is None else [dataset]
    folder = resources.files("elevation") / "datasets"
    # the files are newline terminated, so the separator ends up alone on its line,
    # preceded by a blank line, and the result is a valid stream of YAML documents
    documents = [
        (folder / f"{name}.yaml").read_text(encoding="utf-8") for name in names
    ]
    return "\n---\n".join(documents)


def info(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
) -> str:
    """Show info about the product cache.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :return: The product cache report.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    tiles = sorted((datasource_root / "cache").rglob("*.tif"))
    size = sum(
        path.stat().st_size for path in datasource_root.rglob("*") if path.is_file()
    )
    report = "\n".join(
        (
            f"Product folder: {datasource_root}",
            f"Tiles count: {len(tiles)}",
            f"Cache size: {size / 1024**2:,.1f} MiB",
        )
    )
    return report


def clean(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
) -> None:
    """Clean up the product cache from temporary files.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    for tile in (datasource_root / "cache").rglob("*.tif"):
        if tile.stat().st_size == 0:
            tile.unlink()
    for vrt in datasource_root.glob(f"{product}.*.vrt"):
        vrt.unlink()
    shutil.rmtree(datasource_root / "spool", ignore_errors=True)


def distclean(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
) -> None:
    """Remove the product cache entirely.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    clean(cache_dir=cache_dir, product=product)
    shutil.rmtree(datasource_root / "cache", ignore_errors=True)
    (datasource_root / f"{product}.vrt").unlink(missing_ok=True)
