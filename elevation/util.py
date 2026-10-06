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

from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path

import fasteners

FOLDER_LOCKFILE_NAME = ".folder_lock"


@contextmanager
def lock_tiles(datasource_root: Path, tile_names: Iterable[str]) -> Generator[None]:
    locks = []
    for tile_name in tile_names:
        lockfile = datasource_root / "cache" / f"{tile_name}.lock"
        locks.append(fasteners.InterProcessLock(lockfile))

    for lock in locks:
        lock.acquire(blocking=True)

    yield

    for lock in locks:
        lock.release()


@contextmanager
def lock_vrt(datasource_root: Path, product: str) -> Generator[None]:
    with fasteners.InterProcessLock(datasource_root / f"{product}.vrt.lock"):
        yield


def ensure_setup(root: Path) -> None:
    """Create the product folder and its ``cache`` subfolder.

    The ``spool`` folder is created on demand by the tile download.
    """
    with fasteners.InterProcessLock(root / FOLDER_LOCKFILE_NAME):
        for path in (root, root / "cache"):
            path.mkdir(parents=True, exist_ok=True)
