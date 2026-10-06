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
DEFAULT_GDAL_OPTIONS = "-q"
TILE_GDAL_OPTIONS = (
    DEFAULT_GDAL_OPTIONS + " -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9"
)
INT_TILE_GDAL_OPTIONS = TILE_GDAL_OPTIONS + " -co PREDICTOR=2"
FLOAT_TILE_GDAL_OPTIONS = TILE_GDAL_OPTIONS + " -co PREDICTOR=3"
VRT_GDAL_OPTIONS = DEFAULT_GDAL_OPTIONS + " -overwrite"
TOOLS: list[tuple[str, str]] = [
    ("gdal_translate", "gdal_translate --version"),
    ("gdalbuildvrt", "gdalbuildvrt --version"),
    ("gdalinfo", "gdalinfo --version"),
    ("ogrinfo", "ogrinfo --version"),
]


def selfcheck(
    tools: dict[str, str] | list[tuple[str, str]] = TOOLS,
    verbose: bool = False,
) -> str:
    """Audit the system for issues.

    :param tools: Tools description, defaults to TOOLS.
    :param verbose: Report each tool as it is tested.
    """
    report = []
    issues = []
    for tool_name, check_cli in dict(tools).items():
        if verbose:
            report.append(f"Checking {tool_name!r} ...")
        try:
            subprocess.check_output(check_cli, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            issues.append(f"{tool_name!r} not found or not usable.")
    report.append("\n".join(issues) if issues else "Your system is ready.")
    result = "\n".join(report)
    return result


def gdal_json(cmd: str, destination: str) -> Any:
    """Run the *cmd* GDAL command on *destination* and return its JSON report."""
    output = subprocess.check_output([*cmd.split(), destination])
    return json.loads(output)


def call_gdal_translate(
    source: str,
    destination: Path,
    options: str = DEFAULT_GDAL_OPTIONS,
) -> list[str]:
    """Write *source* to *destination* calling the gdal_translate binary.

    :param source: Any GDAL readable raster, local or remote, may include selection options.
    :param destination: Path of the destination, parent folders are created.
    :param options: GDAL creation options, the default is good for caching tiles.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "gdal_translate",
        *options.split(),
        *source.split(),
        str(destination),
    ]
    subprocess.check_call(cmd)
    return cmd


def call_gdalbuildvrt(
    sources: list[str],
    destination: Path,
    options: str = VRT_GDAL_OPTIONS,
) -> list[str]:
    """Build the *destination* ``.vrt`` mosaic over *sources*.

    :param sources: Paths of the raster tiles to mosaic.
    :param destination: Path of the destination, parent folders are created.
    :param options: GDAL options placed before the destination.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "gdalbuildvrt",
        *options.split(),
        str(destination),
        *sources,
    ]
    subprocess.check_call(cmd)
    return cmd


def raster_bounds(reference: str) -> tuple[float, float, float, float]:
    """Return the bounds of the raster *reference*, ``None`` if it is not a raster."""
    report = gdal_json("gdalinfo -json -nomd -norat -noct", reference)
    if not isinstance(report, dict) or "cornerCoordinates" not in report:
        raise TypeError("'cornerCoordinates' not found")
    corners = report["cornerCoordinates"]
    # all four corners make the bounds of a rotated raster exact
    xs = [corners[key][0] for key in CORNERS]
    ys = [corners[key][1] for key in CORNERS]
    return min(xs), min(ys), max(xs), max(ys)


def vector_bounds(reference: str) -> tuple[float, float, float, float]:
    """Return the bounds of the vector *reference*, ``None`` if it is not a vector."""
    report = gdal_json("ogrinfo -json -al -so", reference)
    if not isinstance(report, dict) or not report.get("layers"):
        raise TypeError("'layers' not found")
    layer = report["layers"][0]
    fields = layer.get("geometryFields") or [{}]
    # GDAL >= 3.6 reports the extent of each geometry field as a list, the older
    # versions report a single extent of the layer as an object
    extent = fields[0].get("extent") or layer.get("extent")
    if extent is None:
        raise TypeError("'extent' not found")
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
    try:
        bounds = raster_bounds(reference)
    except subprocess.CalledProcessError:
        try:
            bounds = vector_bounds(reference)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Reference datasource error {reference!r}") from None
    return bounds
