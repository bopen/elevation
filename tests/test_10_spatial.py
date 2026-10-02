#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest

from elevation import spatial

DATA_DIR = Path(__file__).parent / "data"
RASTER = DATA_DIR / "reference.tif"
VECTOR = DATA_DIR / "reference.geojson"
BOUNDS = (10.0, 40.0, 11.0, 41.0)


def test_import_bounds_raster() -> None:
    assert spatial.import_bounds(RASTER) == BOUNDS


def test_import_bounds_vector() -> None:
    assert spatial.import_bounds(VECTOR) == BOUNDS


def test_import_bounds_invalid() -> None:
    with pytest.raises(RuntimeError, match="could not be opened"):
        spatial.import_bounds(RASTER.with_suffix(".bad"))
