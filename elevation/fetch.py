#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

"""Download the DEM source tiles into the spool folder.

This module is not imported by ``elevation/__init__.py`` on purpose, to keep
``import elevation`` free of the ``fsspec`` import cost; the callers import it
lazily where the download actually happens.
"""

import shutil
from pathlib import Path

import fsspec


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
