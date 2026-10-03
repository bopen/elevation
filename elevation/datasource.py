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
import subprocess
from collections.abc import Callable, Iterator, Sequence
from importlib import resources
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import appdirs

from . import util

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
# the VRT mosaic reads the cache tiles whole, the options only trade size for speed
TILE_GDAL_OPTIONS = "-co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2"
# the float products, e.g. the Copernicus DEM stores, need the float predictor
FLOAT_TILE_GDAL_OPTIONS = (
    "-co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=3"
)
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


def dted_l2_tiles_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}.tif",
) -> Iterator[str]:
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
            yield tile_name_template.format(**locals())


def cgiar_l1_tiles_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_template: str = "srtm_{ilon:02d}_{ilat:02d}.tif",
) -> Iterator[str]:
    ileft, itop = latlon_to_indeces(CGIAR_L1_TILE_INDECES_TRANSFORM, left, top)
    iright, ibottom = latlon_to_indeces(CGIAR_L1_TILE_INDECES_TRANSFORM, right, bottom)
    for ilon in range(ileft, iright + 1):
        for ilat in range(itop, ibottom + 1):
            if ilon > 0 and ilat > 0:
                yield tile_template.format(**locals())


def srtm_ellip_tiles_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}_wgs84.tif",
) -> Iterator[str]:
    ileft, itop = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, left, top)
    iright, ibottom = latlon_to_indeces(DTED_L2_TILE_INDECES_TRANSFORM, right, bottom)

    for ilon in range(ileft, iright + 1):
        slon = f"{'E' if ilon >= 0 else 'W'}{abs(ilon):03d}"
        for ilat in range(ibottom, itop + 1):
            slat = f"{'N' if ilat >= 0 else 'S'}{abs(ilat):02d}"
            subdir = "North" if ilat >= 0 else "South"
            north_subdir = "North_30_60" if ilat >= 30 else "North_0_29"
            fname = tile_name_template.format(**locals())

            if ilat >= 0:
                yield f"{subdir}/{north_subdir}/{fname}"
            else:
                yield f"{subdir}/{fname}"


def zarr_tile_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    transform: tuple[float, float, float, float],
) -> Iterator[str]:
    ileft, itop = latlon_to_indeces(transform, left, top)
    iright, ibottom = latlon_to_indeces(transform, right, bottom)
    for ilon in range(ileft, iright + 1):
        for ilat in range(itop, ibottom + 1):
            if ilon >= 0 and ilat >= 0:
                yield f"{ilat}/{ilon}.tif"


# a cache tile is its name plus the source window, ``None`` for a whole download
Tile = tuple[str, tuple[int, int, int, int] | None]


def zarr_source(url: str) -> str:
    """Return the GDAL connection string that reads the Zarr array at *url*.

    The array path must be given to the driver as the tag suffix. Addressing the
    array as ``ZARR:"/vsicurl/<array>"`` reads the same raster but without any
    CRS: the store keeps it in a separate ``spatial_ref`` variable, that GDAL
    only reads through the store itself.
    """
    store, _, array = url.rpartition("/")
    source = f'ZARR:"/vsicurl/{store}":/{array}'
    return source


class StoreGrid(TypedDict):
    """The georeferencing and the chunk layout of a remote Zarr store.

    The geometry of the stores we read is fixed data, like the tile names of the
    other products: it does not need to be probed at run time.
    """

    # as reported by ``gdalinfo``, i.e. ``(x0, pixel_x, 0, y0, 0, pixel_y)``
    geotransform: tuple[float, float, float, float, float, float]
    # the size of the array, as ``(xsize, ysize)``
    size: tuple[int, int]
    # the shape of the chunks, as ``(xsize, ysize)``; it is NOT what ``gdalinfo``
    # reports as ``block``, that is a read buffer that shrinks with the cache
    chunk_size: tuple[int, int]


def zarr_chunks(
    grid: StoreGrid, left: float, bottom: float, right: float, top: float
) -> Iterator[Tile]:
    """Yield the cache tile and the source window of the chunks covering the bounds.

    The tiles are named after the chunk indices of the store, so the cache
    folder shows which chunks have been read. The bounds are rounded outward to
    whole chunks, like ``gdal_translate -projwin`` rounds to whole pixels.
    """
    x0, pixel_x, _, y0, _, pixel_y = grid["geotransform"]
    width, height = grid["size"]
    chunk_xsize, chunk_ysize = grid["chunk_size"]
    # the store is north-up, so pixel_y is negative and the top row is the first
    xoff = max(math.floor((left - x0) / pixel_x), 0)
    xend = min(math.ceil((right - x0) / pixel_x), width)
    yoff = max(math.floor((y0 - top) / -pixel_y), 0)
    yend = min(math.ceil((y0 - bottom) / -pixel_y), height)
    for ix in range(xoff // chunk_xsize, (xend - 1) // chunk_xsize + 1):
        for iy in range(yoff // chunk_ysize, (yend - 1) // chunk_ysize + 1):
            window = (
                ix * chunk_xsize,
                iy * chunk_ysize,
                min(chunk_xsize, width - ix * chunk_xsize),
                min(chunk_ysize, height - iy * chunk_ysize),
            )
            yield f"{ix}_{iy}{CACHE_EXT}", window


class DatasourceSpec(TypedDict):
    datasource_url: str
    # a local product has one URL per tile (``tile_names``), a remote one is a
    # single chunked source (``grid``): the key tells the two apart
    cached_tile_names: NotRequired[Callable[..., Iterator[str]]]
    # keyword arguments for ``cached_tile_names``, e.g. the tile name template
    # of a product that keeps its tiles in subfolders
    cached_tile_names_kwargs: NotRequired[dict[str, Any]]
    grid: NotRequired[StoreGrid]
    tile_ext: NotRequired[str]
    # only set when the provider serves the tile compressed
    compressed_ext: NotRequired[str]
    tile_gdal_options: NotRequired[str]


MAPZEN_SPEC: DatasourceSpec = {
    "datasource_url": "https://s3.amazonaws.com/elevation-tiles-prod/skadi",
    "tile_ext": ".hgt",
    "compressed_ext": ".hgt.gz",
    "cached_tile_names": dted_l2_tiles_names,
    "cached_tile_names_kwargs": {"tile_name_template": "{slat}/{slat}{slon}.tif"},
}

SRTM1_GEOID_SPEC: DatasourceSpec = {
    "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm",
    "tile_ext": ".tif",
    "cached_tile_names": dted_l2_tiles_names,
}

SRTM1_ELLIP_SPEC: DatasourceSpec = {
    "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm",
    "tile_ext": ".tif",
    "cached_tile_names": srtm_ellip_tiles_names,
}

SRTM3_SPEC: DatasourceSpec = {
    "datasource_url": "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF",
    "tile_ext": ".tif",
    "compressed_ext": ".zip",
    "cached_tile_names": cgiar_l1_tiles_names,
}

# The Copernicus DEM products are distributed by the Earth Data Hub as a single
# north-up Zarr v3 store that is read in place and cached one chunk at a time.
# The URL is the ``dsm`` array inside the store, see
# https://gdal.org/en/stable/drivers/raster/zarr.html
#
# The geometry of the store is recorded here instead of being probed at run
# time, like the tile names of the other products: ``geotransform`` and ``size``
# are what ``gdalinfo`` reports and ``chunk_size`` is what the Zarr metadata
# declares. Both stores are the global grid at 1 and 3 arc seconds, with the
# origin half a pixel outside the ``[-180, 180] x [-90, 90]`` extent, and the
# integration tests pin the geometry against the reference datasets.
GLO_30_GRID: StoreGrid = {
    "geotransform": (
        -180.0001388888889,
        0.0002777777777778,
        0.0,
        90.00013888888888,
        0.0,
        -0.0002777777777778,
    ),
    "size": (1296000, 648000),
    # 1 degree of longitude by 0.5 degrees of latitude
    "chunk_size": (3600, 1800),
}

GLO_90_GRID: StoreGrid = {
    "geotransform": (
        -180.00041666666667,
        0.0008333333333333,
        0.0,
        90.00041666666667,
        0.0,
        -0.0008333333333333,
    ),
    "size": (432000, 216000),
    # 2 degrees by 2 degrees
    "chunk_size": (2400, 2400),
}

GLO_30_SPEC: DatasourceSpec = {
    "datasource_url": (
        "https://data.earthdatahub.destine.eu/copernicus-dem/GLO-30-v1.zarr/dsm"
    ),
    "grid": GLO_30_GRID,
    "tile_gdal_options": FLOAT_TILE_GDAL_OPTIONS,
    "cached_tile_names": zarr_tile_names,
    "cached_tile_names_kwargs": {"transform": EDH_L2_CHUNK_INDECES_TRANSFORM},
}

GLO_90_SPEC: DatasourceSpec = {
    "datasource_url": (
        "https://data.earthdatahub.destine.eu/copernicus-dem/GLO-90-v1.zarr/dsm"
    ),
    "grid": GLO_90_GRID,
    "tile_gdal_options": FLOAT_TILE_GDAL_OPTIONS,
    "cached_tile_names": zarr_tile_names,
    "cached_tile_names_kwargs": {"transform": EDH_L1_CHUNK_INDECES_TRANSFORM},
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


def tile_source(spec: DatasourceSpec, tile_name: str) -> tuple[str, str, str | None]:
    """Return the ``(url, spool_name, member)`` of the tile for *tile_name*.

    *tile_name* is the cache tile name, always a ``.tif``; the spool name is the
    same tile with the source extension (``tile_ext``) and the remote name adds
    the ``compressed_ext`` when the source is compressed. The member is the file
    to read inside a ``.zip`` archive and ``None`` otherwise.
    """
    stem = tile_name.removesuffix(CACHE_EXT)
    spool_name = f"{stem}{spec['tile_ext']}"
    compressed_ext = spec.get("compressed_ext")
    remote = spool_name if compressed_ext is None else f"{stem}{compressed_ext}"
    member = Path(spool_name).name if compressed_ext == ".zip" else None
    return f"{spec['datasource_url']}/{remote}", spool_name, member


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


def ensure_tiles(root: Path, spec: DatasourceSpec, tiles: Sequence[Tile]) -> None:
    """Fetch and cache *tiles*, skipping the tiles already in the cache.

    A tile is a ``(name, window)`` pair: a tile with a window is read in place
    from ``datasource_url``, a tile without one is downloaded whole from its own
    URL and goes through the spool.
    """
    gdal_options = spec.get("tile_gdal_options", TILE_GDAL_OPTIONS)
    for tile_name, srcwin in tiles:
        cached = root / "cache" / tile_name
        if cached.exists() and cached.stat().st_size > 0:
            continue
        if srcwin is None:
            source, spool_name, member = tile_source(spec, tile_name)
            spooled = root / "spool" / spool_name
            fetch_tile(source, spooled, member=member)
            write_cache_tile(spooled, cached)
            spooled.unlink(missing_ok=True)
        else:
            write_cache_tile(
                zarr_source(spec["datasource_url"]),
                cached,
                srcwin=srcwin,
                gdal_options=gdal_options,
            )


def build_vrt(root: Path, product: str) -> list[str]:
    """Build the ``<product>.vrt`` mosaic over the non empty cache tiles."""
    tiles = sorted(
        tile for tile in (root / "cache").rglob("*.tif") if tile.stat().st_size > 0
    )
    cmd = [
        "gdalbuildvrt",
        "-q",
        "-overwrite",
        str(root / f"{product}.vrt"),
        *map(str, tiles),
    ]
    subprocess.check_call(cmd)
    return cmd


def ensure_setup(
    cache_dir: str | Path | None, product: str
) -> tuple[Path, DatasourceSpec]:
    if product in RETIRED_PRODUCTS:
        raise ProductRetiredError(RETIRED_PRODUCTS[product])
    datasource_root = resolve_cache_dir(cache_dir) / product
    spec = PRODUCTS_SPECS[product]
    util.ensure_setup(datasource_root)
    return datasource_root, spec


def do_clip(
    path: Path,
    bounds: tuple[float, float, float, float],
    output: Path,
    product: str,
    gdal_options: str = DEFAULT_GDAL_OPTIONS,
) -> list[str]:
    left, bottom, right, top = bounds
    options = f"gdal_translate -q {gdal_options} -projwin {left} {top} {right} {bottom}"
    cmd = [*options.split(), str(path / f"{product}.vrt"), str(output)]
    with util.lock_vrt(path, product):
        subprocess.check_call(cmd)
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
    grid = spec.get("grid")
    tiles: list[Tile]
    if grid is None:
        cached_tile_names = spec["cached_tile_names"]
        cached_tile_names_kwargs = spec.get("cached_tile_names_kwargs", {})
        tiles = [
            (tile_name, None)
            for tile_name in cached_tile_names(*bounds, **cached_tile_names_kwargs)
        ]
    else:
        tiles = list(zarr_chunks(grid, *bounds))
    # FIXME: emergency hack to enforce the no-bulk-download policy
    if len(tiles) > max_download_tiles:
        raise RuntimeError(
            f"Too many tiles: {len(tiles)}. Please consult the "
            "providers' websites for how to bulk download tiles."
        )

    with util.lock_tiles(datasource_root, [tile_name for tile_name, _ in tiles]):
        ensure_tiles(datasource_root, spec, tiles)

    with util.lock_vrt(datasource_root, product):
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
    return (
        left - margin_lon,
        bottom - margin_lat,
        right + margin_lon,
        top + margin_lat,
    )


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
