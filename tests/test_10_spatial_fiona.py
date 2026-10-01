#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest

from elevation import spatial

pytest.importorskip("fiona")

REFERENCE = Path(__file__).parent / "data" / "reference.geojson"
BOUNDS = (10.0, 40.0, 11.0, 41.0)


def test_import_bounds_vector() -> None:
    assert spatial.import_bounds(REFERENCE) == BOUNDS
