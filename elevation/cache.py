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

import os
import shutil
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import appdirs
import fasteners

from . import spatial

CACHE_DIR: str = appdirs.user_cache_dir("elevation", "bopen")
FOLDER_LOCKFILE_NAME = ".folder_lock"
Tile = tuple[tuple[int, int], str]


def resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    """Return the DEM cache folder to use, as an absolute path.

    The ``cache_dir`` argument takes precedence over the ``EIO_CACHE_DIR`` environment
    variable, that takes precedence over the ``CACHE_DIR`` default.
    """
    if cache_dir is None:
        cache_dir = os.environ.get("EIO_CACHE_DIR") or CACHE_DIR
    return Path(cache_dir).resolve()


def ensure_setup(root: Path) -> None:
    """Create the product folder and its ``cache`` subfolder.

    The ``spool`` folder is created on demand by the cache write.
    """
    with fasteners.InterProcessLock(root / FOLDER_LOCKFILE_NAME):
        for path in (root, root / "cache"):
            path.mkdir(parents=True, exist_ok=True)


@contextmanager
def lock_tiles(datasource_root: Path, tile_names: list[str]) -> Generator[None]:
    locks = []
    for tile_name in tile_names:
        lockfile = datasource_root / "cache" / f"{tile_name}.lock"
        locks.append(fasteners.InterProcessLock(lockfile))

    for lock in locks:
        lock.acquire(blocking=True)

    yield

    for lock in locks:
        lock.release()


def is_cached(root: Path, tile_name: str) -> bool:
    """Return whether *tile_name* is cached, i.e. present and not empty."""
    cached = root / "cache" / tile_name
    return cached.exists() and cached.stat().st_size > 0


def ensure_tiles(
    root: Path,
    tiles: list[Tile],
    prepare_tile: Callable[..., str],
    gdal_options: str = spatial.INT_TILE_GDAL_OPTIONS,
    **kwargs: Any,
) -> None:
    """Fetch and cache *tiles*, skipping the tiles already in the cache.

    ``prepare_tile`` returns the GDAL source of the tile, that is read in place
    and written to the cache as a GeoTIFF.
    """
    for (ilon, ilat), tile_name in tiles:
        if is_cached(root, tile_name):
            continue

        cached = root / "cache" / tile_name
        source = prepare_tile(tile_name=tile_name, ilat=ilat, ilon=ilon, **kwargs)

        # convert the data to the internal cache format
        spool = root / "spool" / tile_name
        spatial.call_gdal_translate(source, spool, options=gdal_options)

        # finally move the data inside the cache. The move is atomic in most cases
        cached.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(spool, cached)


@contextmanager
def lock_vrt(datasource_root: Path, product: str) -> Generator[None]:
    with fasteners.InterProcessLock(datasource_root / f"{product}.vrt.lock"):
        yield


def build_vrt(root: Path, product: str) -> list[str]:
    """Build the ``<product>.vrt`` mosaic over the non empty cache tiles."""
    tiles = []
    for tile in (root / "cache").rglob("*.tif"):
        if tile.stat().st_size > 0:
            tiles.append(str(tile))
    options = "-q -overwrite"
    cmd = spatial.call_gdalbuildvrt(sorted(tiles), root / f"{product}.vrt", options)
    return cmd
