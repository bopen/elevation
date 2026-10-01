#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest

from elevation import spatial

pytest.importorskip("rasterio")

REFERENCE = Path(__file__).parent / "data" / "reference.tif"
BOUNDS = (10.0, 40.0, 11.0, 41.0)


def test_import_bounds_raster() -> None:
    assert spatial.import_bounds(REFERENCE) == BOUNDS


def test_import_bounds_invalid() -> None:
    with pytest.raises(RuntimeError, match="could not be opened"):
        spatial.import_bounds(REFERENCE.with_suffix(".bad"))
