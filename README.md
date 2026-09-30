# elevation

Global geographic elevation data made easy.
Elevation provides easy download, cache and access of the global datasets:

- `TERRAIN_TILES`: [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/)
  hosted on [Amazon S3](https://aws.amazon.com/public-data-sets/terrain),
  global 1 arc second (30m) DEMs in the SRTM HGT format
  assembled by Mapzen from several open data providers,
  including NASA/NGA SRTM, USGS 3DEP, EUDEM, ArcticDEM, GMTED2010 and ETOPO1.
- `SRTM1`: [SRTM 30m Global 1 arc second V003](https://lpdaac.usgs.gov/products/srtmgl1nv003/)
  produced by NASA and NGA hosted on [OpenTopography](https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1).
- `SRTM3`: [SRTM 90m Digital Elevation Database v4.1](https://bigdata.cgiar.org/srtm-90m-digital-elevation-database/)
  produced by CGIAR-CSI.
- `SRTM1_ELLIP`: [SRTM GL1 Ellipsoidal (30m heights on the WGS84 ellipsoid)](https://portal.opentopography.org/raster?opentopoID=OTSRTM.082016.4326.1)
  hosted on OpenTopography.

Note that any download policies and attribution requirements of the respective providers apply.

This Open Source project is sponsored by B-Open - <https://www.bopen.eu>.

## Installation

Install the [latest version of Elevation](https://pypi.org/project/elevation)
from the Python Package Index:

```console
$ pip install elevation
```

The following dependencies need to be installed and working:

- [GNU make](https://www.gnu.org/software/make/)
- [curl](https://curl.haxx.se/)
- unzip
- [gunzip](https://www.gzip.org/)
- [GDAL command line tools](https://www.gdal.org/)

The following command runs some basic checks and reports common issues:

```console
$ eio selfcheck
Your system is ready.
```

GNU make, curl and unzip come pre-installed with most operating systems.
The best way to install GDAL command line tools varies across operating systems
and distributions, please refer to the
[GDAL install documentation](https://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries).

Note that *elevation* v2.0 requires Python 3.11 or later.

## Command line usage

Identify the geographic bounds of the area of interest and fetch the DEM with the `eio` command.
For example to clip the 30m DEM of Rome, around 41.9N 12.5E, to the `Rome-TERRAIN_TILES-DEM.tif` file
using the default `TERRAIN_TILES` product:

```console
$ eio clip -o Rome-TERRAIN_TILES-DEM.tif --bounds 12.35 41.8 12.65 42
```

For the SRTM 30m DEM use:

```console
$ eio --product SRTM1 clip -o Rome-SRTM1-DEM.tif --bounds 12.35 41.8 12.65 42
```

For the SRTM 90m DEM use:

```console
$ eio --product SRTM3 clip -o Rome-SRTM3-DEM.tif --bounds 12.35 41.8 12.65 42
```

The `--bounds` option accepts latitude and longitude coordinates
(more precisely in geodetic coordinates in the WGS84 reference system EPSG:4326 for those who care)
given as `left bottom right top` similarly to the `rio` command form `rasterio`.

If you have installed the optional `reference` dependencies `rasterio` and `fiona`
(`pip install "elevation[reference]"`)
you can clip a DEM on the same extent of any other geospatial data source supported by GDAL and OGR,
for example if you have a georeferenced image `MyImage.tif` you can clip the corresponding DEM with:

```console
$ eio clip -o MyImage-DEM.tif --reference MyImage.tif  # enable with: $ pip install rasterio
```

The `--reference` option can also take vector data as input:

```console
$ eio clip -o MyShapefile-DEM.tif --reference MyShapefile.shp  # enable with: $ pip install fiona
```

The first time an area is accessed Elevation downloads the data tiles from
the AWS S3, CGIAR-CSI or OpenTopography servers and
caches them in GeoTIFF compressed formats,
subsequent accesses to the same and nearby areas are much faster.

The `clip` sub-command doesn't allow automatic download of a large amount of DEM tiles,
please refer to the upstream providers' websites to learn the preferred procedures for bulk download.

To clean up stale temporary files and fix the cache in the event of a server error use:

```console
$ eio clean
```

## Command line reference

The `eio` command has the following sub-commands and options:

```text
$ eio --help

 Usage: eio [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --version                                        Show the version and exit.  │
│                                                  [env var: EIO_VERSION]      │
│ --product             [TERRAIN_TILES|SRTM1|SRTM  DEM product choice.         │
│                       3|SRTM1_ELLIP]             [env var: EIO_PRODUCT]      │
│                                                  [default: TERRAIN_TILES]    │
│ --cache_dir           <directory>                Root of the DEM cache       │
│                                                  folder.                     │
│                                                  [env var: EIO_CACHE_DIR]    │
│                                                  [default:                   │
│                                                  /Users/amici/Library/Cache… │
│ --make_options        <str>                      Options passed through to   │
│                                                  every GNU make invocation.  │
│                                                  [env var: EIO_MAKE_OPTIONS] │
│ --help                                           Show this message and exit. │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ selfcheck  Audit the system for common issues.                               │
│ info       Show info about the product cache.                                │
│ seed       Seed the DEM to given bounds.                                     │
│ clip       Clip the DEM to given bounds.                                     │
│ clean      Clean up the product cache from temporary files.                  │
│ distclean  Remove the product cache entirely.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

The `clip` sub-command:

```text
$ eio clip --help

 Usage: eio clip [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --output     -o      <file>                      Path to output file.        │
│                                                  Existing files will be      │
│                                                  overwritten.                │
│                                                  [env var: EIO_CLIP_OUTPUT]  │
│                                                  [default: out.tif]          │
│ --bounds             <float float float          Output bounds in 'left      │
│                      float>...                   bottom right top' order.    │
│                                                  [env var: EIO_CLIP_BOUNDS]  │
│ --margin     -m      <str>                       Decimal degree margin added │
│                                                  to the bounds. Use '%' for  │
│                                                  percent margin.             │
│                                                  [env var: EIO_CLIP_MARGIN]  │
│                                                  [default: 0]                │
│ --reference  -r      <path>                      Use the extent of a         │
│                                                  reference GDAL/OGR data     │
│                                                  source as output bounds.    │
│                                                  [env var:                   │
│                                                  EIO_CLIP_REFERENCE]         │
│ --help                                           Show this message and exit. │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Defaults can be defined by setting environment variables prefixed with `EIO`,
e.g. `EIO_PRODUCT=SRTM3`, `EIO_CLIP_MARGIN=10%` and `EIO_CACHE_DIR=/tmp/elevation2`.
`EIO_CACHE_DIR` selects the DEM cache folder and is honoured by the Python API as well.
`EIO_MAKE_OPTIONS` is passed through to every `make` invocation, e.g. `EIO_MAKE_OPTIONS=-s`
silences make; the Python API takes the same value as the `make_options` keyword argument.

## Python API

Every command has a corresponding API function in the `elevation` module:

```python
>>> import elevation
>>> # clip the SRTM1 30m DEM of Rome and save it to Rome-DEM.tif
>>> elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output="Rome-DEM.tif")
>>> # clean up stale temporary files and fix the cache in the event of a server error
>>> elevation.clean()

```

## Project resources

| Resource | Link |
| --- | --- |
| Documentation | <https://elevation.bopen.eu> |
| Support | <https://stackoverflow.com/search?q=python+elevation> |
| Development | <https://github.com/bopen/elevation> |
| Download | <https://pypi.org/project/elevation> |
| Code quality | [![Coverage status on Codecov](https://codecov.io/gh/bopen/elevation/branch/main/graph/badge.svg)](https://codecov.io/gh/bopen/elevation) |

## Contributing

The main repository is hosted on GitHub.
Testing, bug reports and contributions are highly welcomed and appreciated:

https://github.com/bopen/elevation

Lead developer:

- [Alessandro Amici](https://github.com/alexamici) - [B-Open](https://bopen.eu)

See also the list of [contributors](https://github.com/bopen/elevation/contributors) who participated in this project.

## Sponsoring

[B-Open](https://bopen.eu) commits to maintain the project long term and we are
happy to accept sponsorships to develop new features.

## License

```
Copyright 2016-2026 B-Open Solutions srl

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
