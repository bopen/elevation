#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest

from elevation import spatial

REFERENCE = Path(__file__).parent / "data" / "reference.tif"


def test_import_bounds_without_optional_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(spatial, "SUPPORT_RASTER_DATA", False)
    monkeypatch.setattr(spatial, "SUPPORT_VECTOR_DATA", False)
    with pytest.raises(RuntimeError, match="could not be opened"):
        spatial.import_bounds(REFERENCE)
