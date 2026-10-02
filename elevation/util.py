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

import subprocess
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path

import fasteners

FOLDER_LOCKFILE_NAME = ".folder_lock"
TOOLS: list[tuple[str, str]] = [
    ("gdal_translate", "gdal_translate --version"),
    ("gdalbuildvrt", "gdalbuildvrt --version"),
]


def selfcheck(tools: dict[str, str] | Iterable[tuple[str, str]] = TOOLS) -> str:
    """Audit the system for issues.

    :param tools: Tools description, defaults to TOOLS.
    """
    msg = []
    for tool_name, check_cli in dict(tools).items():
        try:
            subprocess.check_output(check_cli, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            msg.append(f"{tool_name!r} not found or not usable.")
    return "\n".join(msg) if msg else "Your system is ready."


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


def ensure_setup(root: Path, folders: Iterable[str] = ()) -> list[Path]:
    """Create *root* and the *folders* in it, returning the created folders."""
    with fasteners.InterProcessLock(root / FOLDER_LOCKFILE_NAME):
        created_folders = []
        for path in [root] + [root / p for p in folders]:
            if not path.exists():
                path.mkdir(parents=True)
                created_folders.append(path)
    return created_folders
