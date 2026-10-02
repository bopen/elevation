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

import json
import subprocess
from pathlib import Path
from typing import Any

CORNERS = ("upperLeft", "lowerLeft", "upperRight", "lowerRight")


def gdal_report(cmd: list[str]) -> Any:
    """Run the *cmd* GDAL command and return its JSON report, or ``None``."""
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(output)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def raster_bounds(reference: str) -> tuple[float, float, float, float] | None:
    """Return the bounds of the raster *reference*, ``None`` if it is not a raster."""
    report = gdal_report(["gdalinfo", "-json", "-nomd", "-norat", "-noct", reference])
    if not isinstance(report, dict) or "cornerCoordinates" not in report:
        return None
    corners = report["cornerCoordinates"]
    # all four corners make the bounds of a rotated raster exact
    xs = [corners[key][0] for key in CORNERS]
    ys = [corners[key][1] for key in CORNERS]
    return min(xs), min(ys), max(xs), max(ys)


def vector_bounds(reference: str) -> tuple[float, float, float, float] | None:
    """Return the bounds of the vector *reference*, ``None`` if it is not a vector."""
    report = gdal_report(["ogrinfo", "-json", "-al", "-so", reference])
    if not isinstance(report, dict) or not report.get("layers"):
        return None
    layer = report["layers"][0]
    fields = layer.get("geometryFields") or [{}]
    # GDAL >= 3.6 reports the extent of each geometry field as a list, the older
    # versions report a single extent of the layer as an object
    extent = fields[0].get("extent") or layer.get("extent")
    if extent is None:
        return None
    if isinstance(extent, dict):
        return extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"]
    left, bottom, right, top = extent
    return left, bottom, right, top


def import_bounds(reference: str | Path) -> tuple[float, float, float, float]:
    """Return the bounds of *reference*, a raster or vector data source.

    The bounds are read with the GDAL command line tools, from the first data
    source that can open *reference*, in the crs of the data source.

    :param reference: Path or connection string of a GDAL or OGR data source.
    :return: Bounds in 'left bottom right top' order.
    :raises RuntimeError: If *reference* cannot be opened.
    """
    # ASSUMPTION: the bounds are given in geodetic WGS84 crs
    reference = str(reference)
    bounds = raster_bounds(reference) or vector_bounds(reference)
    if bounds is None:
        raise RuntimeError(f"Reference datasource could not be opened {reference!r}.")
    return bounds
