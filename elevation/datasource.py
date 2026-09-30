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
import pkgutil
import uuid
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, TypedDict

import appdirs

from . import util

# declare public all API functions and constants
__all__ = [
    "CACHE_DIR",
    "DEFAULT_OUTPUT",
    "DEFAULT_PRODUCT",
    "MARGIN",
    "PRODUCTS",
    "RETIRED_PRODUCTS",
    "ProductRetiredError",
    "clean",
    "clip",
    "distclean",
    "info",
    "resolve_cache_dir",
    "seed",
]

CACHE_DIR: str = appdirs.user_cache_dir("elevation", "bopen")
DEFAULT_OUTPUT = "out.tif"
MARGIN = "0"


def resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    """Return the DEM cache folder to use, as an absolute path.

    The ``cache_dir`` argument takes precedence over the ``EIO_CACHE_DIR`` environment
    variable, that takes precedence over the ``CACHE_DIR`` default.
    """
    if cache_dir is None:
        cache_dir = os.environ.get("EIO_CACHE_DIR") or CACHE_DIR
    return Path(cache_dir).resolve()


def srtm1_tile_ilonlat(lon: float, lat: float) -> tuple[int, int]:
    return math.floor(lon), math.floor(lat)


def srtm3_tile_ilonlat(lon: float, lat: float) -> tuple[int, int]:
    ilon, ilat = srtm1_tile_ilonlat(lon, lat)
    return (ilon + 180) // 5 + 1, (64 - ilat) // 5


def srtm1_tiles_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_name_template: str = "{slat}{slon}.tif",
) -> Iterator[str]:
    ileft, itop = srtm1_tile_ilonlat(left, top)
    iright, ibottom = srtm1_tile_ilonlat(right, bottom)
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


def srtm3_tiles_names(
    left: float,
    bottom: float,
    right: float,
    top: float,
    tile_template: str = "srtm_{ilon:02d}_{ilat:02d}.tif",
) -> Iterator[str]:
    ileft, itop = srtm3_tile_ilonlat(left, top)
    iright, ibottom = srtm3_tile_ilonlat(right, bottom)
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
    ileft, itop = srtm1_tile_ilonlat(left, top)
    iright, ibottom = srtm1_tile_ilonlat(right, bottom)

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


def terrain_tiles_names(
    left: float, bottom: float, right: float, top: float
) -> Iterator[str]:
    yield from srtm1_tiles_names(left, bottom, right, top, "{slat}/{slat}{slon}.tif")


class DatasourceSpec(TypedDict):
    folders: tuple[str, ...]
    file_templates: dict[str, str]
    datasource_url: str
    tile_ext: str
    compressed_pre_ext: str
    compressed_ext: str
    tile_names: Callable[..., Iterator[str]]


_datasource_makefile = pkgutil.get_data("elevation", "datasource.mk")
assert _datasource_makefile is not None
DATASOURCE_MAKEFILE = _datasource_makefile.decode("utf-8")

TERRAIN_TILES_SPEC: DatasourceSpec = {
    "folders": ("spool", "cache"),
    "file_templates": {"Makefile": DATASOURCE_MAKEFILE},
    "datasource_url": "https://s3.amazonaws.com/elevation-tiles-prod/skadi",
    "tile_ext": ".hgt",
    "compressed_pre_ext": ".hgt",
    "compressed_ext": ".hgt.gz",
    "tile_names": terrain_tiles_names,
}

SRTM1_GEOID_SPEC: DatasourceSpec = {
    "folders": ("spool", "cache"),
    "file_templates": {"Makefile": DATASOURCE_MAKEFILE},
    "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm",
    "tile_ext": ".tif",
    "compressed_pre_ext": "",
    "compressed_ext": "",
    "tile_names": srtm1_tiles_names,
}

SRTM1_ELLIP_SPEC: DatasourceSpec = {
    "folders": ("spool", "cache"),
    "file_templates": {"Makefile": DATASOURCE_MAKEFILE},
    "datasource_url": "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm",
    "tile_ext": ".tif",
    "compressed_pre_ext": "",
    "compressed_ext": "",
    "tile_names": srtm_ellip_tiles_names,
}

SRTM3_SPEC: DatasourceSpec = {
    "folders": ("spool", "cache"),
    "file_templates": {"Makefile": DATASOURCE_MAKEFILE},
    "datasource_url": "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF",
    "tile_ext": ".tif",
    "compressed_pre_ext": "",
    "compressed_ext": ".zip",
    "tile_names": srtm3_tiles_names,
}

PRODUCTS_SPECS: dict[str, DatasourceSpec] = {
    "TERRAIN_TILES": TERRAIN_TILES_SPEC,
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
        "mosaic it used to download is now the 'TERRAIN_TILES' product (the default) and "
        "the OpenTopography SRTM GL1 product is now 'SRTM1_GEOID'. See "
        "https://elevation.bopen.eu/migration.html"
    ),
}


def ensure_tiles(
    path: Path, ensure_tiles_names: Sequence[str] = (), **kwargs: Any
) -> list[str]:
    ensure_tiles = " ".join(ensure_tiles_names)
    variables_items = [("ensure_tiles", ensure_tiles)]
    return util.check_call_make(
        path, targets=["download"], variables=variables_items, **kwargs
    )


# FIXME: force=True is an emergency hack to ensure that the file always contains the intended body
def ensure_setup(
    cache_dir: str | Path | None, product: str, force: bool = True
) -> tuple[Path, DatasourceSpec]:
    if product in RETIRED_PRODUCTS:
        raise ProductRetiredError(RETIRED_PRODUCTS[product])
    datasource_root = resolve_cache_dir(cache_dir) / product
    spec = PRODUCTS_SPECS[product]
    util.ensure_setup(datasource_root, product=product, force=force, **spec)
    return datasource_root, spec


def do_clip(
    path: Path,
    bounds: tuple[float, float, float, float],
    output: Path,
    product: str,
    **kwargs: Any,
) -> list[str]:
    run_id = uuid.uuid4().hex
    with util.lock_vrt(path, product):
        util.check_call_make(
            path, targets=["copy_vrt"], variables=[("run_id", run_id)], **kwargs
        )
    left, bottom, right, top = bounds
    projwin = f"{left} {top} {right} {bottom}"
    variables_items = [
        ("output", str(output)),
        ("projwin", projwin),
        ("run_id", run_id),
    ]
    return util.check_call_make(
        path, targets=["clip"], variables=variables_items, **kwargs
    )


def seed(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    bounds: tuple[float, float, float, float] | None = None,
    max_download_tiles: int = 9,
    **kwargs: Any,
) -> Path:
    """Seed the DEM to given bounds.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param bounds: Output bounds in 'left bottom right top' order.
    :param max_download_tiles: Maximum number of tiles to process.
    :param kwargs: Pass additional kwargs to check_call_make.
    """
    if bounds is None:
        raise TypeError("bounds must be supplied")
    datasource_root, spec = ensure_setup(cache_dir, product)
    ensure_tiles_names = list(spec["tile_names"](*bounds))
    # FIXME: emergency hack to enforce the no-bulk-download policy
    if len(ensure_tiles_names) > max_download_tiles:
        raise RuntimeError(
            f"Too many tiles: {len(ensure_tiles_names)}. Please consult the "
            "providers' websites for how to bulk download tiles."
        )

    with util.lock_tiles(datasource_root, ensure_tiles_names):
        ensure_tiles(datasource_root, ensure_tiles_names, **kwargs)

    with util.lock_vrt(datasource_root, product):
        util.check_call_make(datasource_root, targets=["all"], **kwargs)
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
    **kwargs: Any,
) -> None:
    """Clip the DEM to given bounds.

    :param bounds: Output bounds in 'left bottom right top' order.
    :param output: Path to output file. Existing files will be overwritten.
    :param margin: Decimal degree margin added to the bounds. Use '%' for percent margin.
    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param kwargs: Pass additional kwargs to check_call_make.
    """
    output = Path(output).resolve()
    bounds = build_bounds(bounds, margin=margin)
    datasource_root = seed(
        cache_dir=cache_dir, product=product, bounds=bounds, **kwargs
    )
    do_clip(datasource_root, bounds, output, product=product, **kwargs)


def info(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    **kwargs: Any,
) -> None:
    """Show info about the product cache.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param kwargs: Pass additional kwargs to check_call_make.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    util.check_call_make(datasource_root, targets=["info"], **kwargs)


def clean(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    **kwargs: Any,
) -> None:
    """Clean up the product cache from temporary files.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param kwargs: Pass additional kwargs to check_call_make.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    util.check_call_make(datasource_root, targets=["clean"], **kwargs)


def distclean(
    cache_dir: str | Path | None = None,
    product: str = DEFAULT_PRODUCT,
    **kwargs: Any,
) -> None:
    """Remove the product cache entirely.

    :param cache_dir: Root of the DEM cache folder.
    :param product: DEM product choice.
    :param kwargs: Pass additional kwargs to check_call_make.
    """
    datasource_root, _ = ensure_setup(cache_dir, product)
    util.check_call_make(datasource_root, targets=["distclean"], **kwargs)
