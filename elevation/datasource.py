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
import shutil
from collections.abc import Callable, Iterator
from importlib import resources
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from . import cache, spatial

DEFAULT_OUTPUT = "out.tif"
DEFAULT_GDAL_OPTIONS = (
    "-co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co NUM_THREADS=ALL_CPUS"
)
MARGIN = "0"
MAX_DOWNLOAD_TILES = 25

# NOTE:
#   0.0001388888889 == 0.5" is half pixel for DEMs with 1" spacing (DTED L2)
#   0.0004166666667 == 1.5" is half pixel for DEMs with 3" spacing (DTED L1)
EDH_L2_CHUNK_INDECES_TRANSFORM = (-180.0001388888889, 1.0, 90.00013888888888, -0.5)
EDH_L1_CHUNK_INDECES_TRANSFORM = (-180.00041666666667, 2.0, 90.00041666666667, -2.0)
DTED_L2_TILE_INDECES_TRANSFORM = (-0.0001388888889, 1.0, -0.0001388888889, 1.0)
CGIAR_L1_TILE_INDECES_TRANSFORM = (-185.0004166666667, 5.0, 65.0004166666667, -5.0)


def latlon_to_indeces(
    transform: tuple[float, float, float, float], lon: float, lat: float
) -> tuple[int, int]:
    lon_start, lon_step, lat_start, lat_step = transform
    ilon = math.floor((lon - lon_start) / lon_step)
    ilat = math.floor((lat - lat_start) / lat_step)
    return ilon, ilat


def dted_l2_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}",
) -> Iterator[cache.Tile]:
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
    tile_template: str = "srtm_{ilon:02d}_{ilat:02d}",
) -> Iterator[cache.Tile]:
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
    tile_name_template: str = "{slat}{slon}_wgs84",
) -> Iterator[cache.Tile]:
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


def zarr_tiles(
    left: float,
    bottom: float,
    right: float,
    top: float,
    transform: tuple[float, float, float, float],
) -> Iterator[cache.Tile]:
    ileft, itop = latlon_to_indeces(transform, left, top)
    iright, ibottom = latlon_to_indeces(transform, right, bottom)
    for ilon in range(ileft, iright + 1):
        for ilat in range(itop, ibottom + 1):
            if ilon >= 0 and ilat >= 0:
                yield (ilon, ilat), f"{ilat}/{ilon}"


def prepare_tile(
    gdal_source: str,
    tile_name: str,
    remote_ext: str = ".tif",
    **kwargs: Any,
) -> str:
    return f"{gdal_source}/{tile_name}{remote_ext}"


def prepare_tile_zarr(
    gdal_source: str,
    ilat: int,
    ilon: int,
    chunks: tuple[int, int],
    **kwargs: Any,
) -> str:
    srcwin = [ilon * chunks[0], ilat * chunks[1], chunks[0], chunks[1]]
    return f"vrt://{gdal_source}?srcwin={','.join(map(str, srcwin))}"


def prepare_tile_member(
    gdal_source: str,
    tile_name: str,
    remote_ext: str = ".zip",
    member_template: str = "{tile_name}.tif",
    **kwargs: Any,
) -> str:
    member = member_template.format(tile_name=tile_name)
    member = Path(member).name
    return f"{gdal_source}/{tile_name}{remote_ext}/{member}"


class DatasourceSpec(TypedDict):
    """How a DEM product lists, prepares and caches its tiles."""

    cached_tiles: Callable[..., Iterator[cache.Tile]]
    cached_tiles_kwargs: NotRequired[dict[str, Any]]
    prepare_tile: Callable[..., str]
    prepare_tile_kwargs: dict[str, Any]
    tile_gdal_options: NotRequired[str]
    empty_on_notfound: NotRequired[bool]


MAPZEN_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile,
    "prepare_tile_kwargs": {
        "remote_ext": ".hgt.gz",
        "gdal_source": "/vsigzip//vsicurl/https://s3.amazonaws.com/elevation-tiles-prod/skadi",
    },
    "cached_tiles": dted_l2_tiles,
    "cached_tiles_kwargs": {"tile_name_template": "{slat}/{slat}{slon}"},
}

SRTM1_GEOID_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile,
    "prepare_tile_kwargs": {
        "gdal_source": "/vsicurl/https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm",
    },
    "cached_tiles": dted_l2_tiles,
}

SRTM1_ELLIP_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile,
    "prepare_tile_kwargs": {
        "gdal_source": "/vsicurl/https://opentopography.s3.sdsc.edu/raster/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm",
    },
    "cached_tiles": srtm_ellip_tiles,
}

SRTM3_SPEC: DatasourceSpec = {
    "prepare_tile_kwargs": {
        "gdal_source": "/vsizip//vsicurl/https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF",
    },
    "cached_tiles": cgiar_l1_tiles,
    "prepare_tile": prepare_tile_member,
}

GLO_30_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_zarr,
    "prepare_tile_kwargs": {
        "gdal_source": 'ZARR:"/vsicurl/https://data.earthdatahub.destine.eu/copernicus-dem/GLO-30-v1.zarr":/dsm',
        "chunks": (3600, 1800),
    },
    "tile_gdal_options": spatial.FLOAT_TILE_GDAL_OPTIONS,
    "empty_on_notfound": False,
    "cached_tiles": zarr_tiles,
    "cached_tiles_kwargs": {"transform": EDH_L2_CHUNK_INDECES_TRANSFORM},
}

GLO_90_SPEC: DatasourceSpec = {
    "prepare_tile": prepare_tile_zarr,
    "prepare_tile_kwargs": {
        "gdal_source": 'ZARR:"/vsicurl/https://data.earthdatahub.destine.eu/copernicus-dem/GLO-90-v1.zarr":/dsm',
        "chunks": (2400, 2400),
    },
    "tile_gdal_options": spatial.FLOAT_TILE_GDAL_OPTIONS,
    "empty_on_notfound": False,
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


def ensure_setup(
    cache_dir: str | Path | None, product: str
) -> tuple[Path, DatasourceSpec]:
    if product in RETIRED_PRODUCTS:
        raise ProductRetiredError(RETIRED_PRODUCTS[product])
    datasource_root = cache.resolve_cache_dir(cache_dir) / product
    spec = PRODUCTS_SPECS[product]
    cache.ensure_setup(datasource_root)
    return datasource_root, spec


def seed(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    bounds: tuple[float, float, float, float] | None = None,
    max_download_tiles: int = MAX_DOWNLOAD_TILES,
    *,
    margin: str = MARGIN,
) -> tuple[Path, tuple[float, float, float, float]]:
    """Seed the DEM to given bounds.

    A remote product is not downloaded whole: only the chunks of the store that
    cover the bounds are read in place and cached.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param bounds: Output bounds in 'left bottom right top' order.
    :param max_download_tiles: Maximum number of tiles to download.
    :param margin: Decimal degree margin added to the bounds. Use '%' for percent margin.
    :return: The datasource root and the bounds with the margin applied.
    """
    if bounds is None:
        raise TypeError("bounds must be supplied")
    bounds = build_bounds(bounds, margin=margin)
    datasource_root, spec = ensure_setup(cache_dir, product)
    cached_tiles = spec["cached_tiles"]
    cached_tiles_kwargs = spec.get("cached_tiles_kwargs", {})
    tiles = list(cached_tiles(*bounds, **cached_tiles_kwargs))
    downloads = [
        tile for tile in tiles if not cache.is_cached(datasource_root, tile[1])
    ]
    # FIXME: emergency hack to enforce the no-bulk-download policy
    if len(downloads) > max_download_tiles:
        raise RuntimeError(
            f"Too many tiles to download: {len(downloads)}. Please consult the "
            "providers' websites for how to bulk download tiles."
        )

    prepare_tile = spec["prepare_tile"]
    prepare_tile_kwargs = spec.get("prepare_tile_kwargs", {})
    with cache.lock_tiles(datasource_root, [name for _, name in downloads]):
        cache.ensure_tiles(
            datasource_root,
            downloads,
            prepare_tile=prepare_tile,
            gdal_options=spec.get("tile_gdal_options", spatial.INT_TILE_GDAL_OPTIONS),
            empty_on_notfound=spec.get("empty_on_notfound", True),
            **prepare_tile_kwargs,
        )

    with cache.lock_vrt(datasource_root, product):
        cache.build_vrt(datasource_root, product)

    return datasource_root, bounds


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
    product: str = DEFAULT_PRODUCT,
    *,
    cache_dir: str | Path | None = None,
    gdal_options: str = DEFAULT_GDAL_OPTIONS,
    max_download_tiles: int = MAX_DOWNLOAD_TILES,
) -> None:
    """Clip the DEM to given bounds.

    :param bounds: Output bounds in 'left bottom right top' order.
    :param output: Path to output file. Existing files will be overwritten.
    :param margin: Decimal degree margin added to the bounds. Use '%' for percent margin.
    :param product: DEM product choice.
    :param cache_dir: Root of the DEM cache folder.
    :param gdal_options: GDAL creation options of the output file, e.g. '-co COMPRESS=LZW'.
    :param max_download_tiles: Maximum number of tiles to download.
    """
    output = Path(output).resolve()
    datasource_root, bounds = seed(
        cache_dir=cache_dir,
        product=product,
        bounds=bounds,
        margin=margin,
        max_download_tiles=max_download_tiles,
    )
    left, bottom, right, top = bounds
    options = f"-q {gdal_options} -projwin {left} {top} {right} {bottom}"
    source = str(datasource_root / f"{product}.vrt")
    with cache.lock_vrt(datasource_root, product):
        spatial.call_gdal_translate(source, output, options=options)


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
