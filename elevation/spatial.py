# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - http://bopen.eu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import rasterio

    SUPPORT_RASTER_DATA = True
except ImportError:
    SUPPORT_RASTER_DATA = False
try:
    import fiona

    SUPPORT_VECTOR_DATA = True
except ImportError:
    SUPPORT_VECTOR_DATA = False


def import_bounds(reference: str) -> tuple[float, float, float, float]:
    # ASSUMPTION: rasterio and fiona bounds are given in geodetic WGS84 crs
    if SUPPORT_RASTER_DATA:
        try:
            with rasterio.open(reference) as datasource:
                left, bottom, right, top = datasource.bounds
                return left, bottom, right, top
        except rasterio.errors.RasterioIOError:
            pass
    if SUPPORT_VECTOR_DATA:
        try:
            with fiona.open(reference) as datasource:
                left, bottom, right, top = datasource.bounds
                return left, bottom, right, top
        except fiona.errors.FionaValueError:
            pass
    raise RuntimeError("Reference datasource could not be opened %r." % reference)
