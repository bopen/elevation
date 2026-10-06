# elevation

Global geographic elevation data made easy.
Elevation provides easy download, cache and access of the global datasets:

- `MAPZEN`: [Terrain Tiles global 30m v1](https://registry.opendata.aws/terrain-tiles/)
  assembled by Mapzen from several open data providers and hosted on [Amazon](https://aws.amazon.com/public-data-sets/terrain),
  with 30m heights on the EGM96 geoid,
  includes data from NASA/NGA SRTM, USGS 3DEP, EUDEM, ArcticDEM, GMTED2010 and ETOPO1.
- `GLO-30`: [Copernicus DEM global 30m (2021)](https://doi.org/10.5270/ESA-c5d3d65)
  produced by ESA and the European Union and hosted on [Earth Data Hub](https://earthdatahub.destine.eu/collections/copernicus-dem), with 30m heights on the EGM2008 geoid.
- `GLO-90`: [Copernicus DEM global 90m (2021)](https://doi.org/10.5270/ESA-c5d3d65)
  the 90m companion of `GLO-30`.
- `SRTM1_GEOID`: [SRTM global 30m v3](https://lpdaac.usgs.gov/products/srtmgl1nv003/)
  produced by NASA and NGA hosted on [OpenTopography](https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1),
  with 30m heights on the EGM96 geoid.
- `SRTM1_ELLIP`: [SRTM global 30m v3 ellipsoidal](https://portal.opentopography.org/raster?opentopoID=OTSRTM.082016.4326.1)
  the companion of `SRTM1_GEOID`, with 30m heights on the WGS84 ellipsoid.
- `SRTM3`: [SRTM global 90m v4.1](https://bigdata.cgiar.org/srtm-90m-digital-elevation-database/)
  produced and hosted by CGIAR-CSI, with 90m heights on the EGM96 geoid.

Note that any download policies and attribution requirements of the respective providers apply.

This Open Source project is sponsored by B-Open - <https://bopen.eu>.

## Installation

Install the [latest version of Elevation](https://pypi.org/project/elevation)
from the Python Package Index:

```console
$ pip install elevation
```

The following dependencies need to be installed and working:

- [GDAL](https://www.gdal.org/) command line tools, i.e. `gdal_translate`, `gdalbuildvrt`,
  `gdalinfo` and `ogrinfo`

The following command runs some basic checks and reports common issues:

```console
$ eio selfcheck --verbose
Checking 'gdal_translate' ...
Checking 'gdalbuildvrt' ...
Checking 'gdalinfo' ...
Checking 'ogrinfo' ...
Your system is ready.
```

The best way to install GDAL command line tools varies across operating systems
and distributions, please refer to the
[GDAL install documentation](https://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries).

Note that *elevation* v2.0 requires Python 3.11 or later.

## Command line usage

Identify the geographic bounds of the area of interest and fetch the DEM with the `eio` command.
For example to clip the 30m DEM of Rome, around 41.9N 12.5E, to the `Rome-MAPZEN-DEM.tif` file
using the default `MAPZEN` product:

```console
$ eio clip -o Rome-MAPZEN-DEM.tif --bounds 12.35 41.8 12.65 42
```

For the Copernicus DEM global 30m or 90m DEMs use:

```console
$ eio --product GLO-30 clip -o Rome-GLO-30-DEM.tif --bounds 12.35 41.8 12.65 42
$ eio --product GLO-90 clip -o Rome-GLO-90-DEM.tif --bounds 12.35 41.8 12.65 42
```

The `GLO-30` and `GLO-90` products are distributed by the Earth Data Hub as a
single cloud-hosted Zarr store that is read in place and cached one chunk at a
time instead of downloading whole tiles, and the credentials of the account
stored in `~/.netrc` are used to access it:

```console
machine data.earthdatahub.destine.eu
    password <your EDH API key>
```

See the Earth Data Hub [Getting started](https://earthdatahub.destine.eu/getting-started)
page to create an account and set up the credentials.

Reading the store needs GDAL 3.8 or later.

For the SRTM global 30m v3 geoid or ellipsoidal DEMs use:

```console
$ eio --product SRTM1_GEOID clip -o Rome-SRTM1_GEOID-DEM.tif --bounds 12.35 41.8 12.65 42
$ eio --product SRTM1_ELLIP clip -o Rome-SRTM1_ELLIP-DEM.tif --bounds 12.35 41.8 12.65 42
```

For the SRTM global 90m v4.1 DEM use:

```console
$ eio --product SRTM3 clip -o Rome-SRTM3-DEM.tif --bounds 12.35 41.8 12.65 42
```

The `--bounds` option accepts latitude and longitude coordinates
(more precisely in geodetic coordinates in the WGS84 reference system EPSG:4326 for those who care)
given as `left bottom right top` similarly to the `rio` command form `rasterio`.

The `--reference` option clips a DEM on the same extent of any other geospatial data source
supported by GDAL and OGR, for example if you have a georeferenced image `MyImage.tif`
you can clip the corresponding DEM with:

```console
$ eio clip -o MyImage-DEM.tif --reference MyImage.tif
```

The `--reference` option can also take vector data as input:

```console
$ eio clip -o MyShapefile-DEM.tif --reference MyShapefile.shp
```

The first time an area is accessed Elevation downloads the data tiles from
the AWS S3, CGIAR-CSI or OpenTopography servers and
caches them in GeoTIFF compressed formats,
subsequent accesses to the same and nearby areas are much faster.
The `GLO-30` and `GLO-90` products are the exception: they are read in place
from the Earth Data Hub and cached one Zarr chunk at a time.

The `seed` and `clip` sub-commands refuse to download more than `--max_download_tiles`
(`25` by default) tiles at a time to prevent bulk downloads,
please refer to the upstream providers' websites to learn the preferred procedures for bulk download.

To show the STAC metadata of the datasets use:

```console
$ eio dataset
```

The optional argument selects a single dataset by id, e.g. `eio dataset SRTM3`.

To show info about the product cache use:

```console
$ eio info
```

To clean up the product cache from temporary files use:

```console
$ eio clean
```

To remove the product cache entirely use:

```console
$ eio distclean
```

## Command line reference

The `eio` command has the following sub-commands and options:

```text
$ eio --help

 Usage: eio [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --version                                                 Show the version and exit.             │
│                                                           [env var: EIO_VERSION]                 │
│ --product          [MAPZEN|GLO-30|GLO-90|SRTM1_GEOID|SRT  DEM product choice.                    │
│                    M1_ELLIP|SRTM3]                        [env var: EIO_PRODUCT]                 │
│                                                           [default: MAPZEN]                      │
│ --cache_dir        <directory>                            Root of the DEM cache folder.          │
│                                                           [env var: EIO_CACHE_DIR]               │
│                                                           [default: <user cache folder>]         │
│ --help                                                    Show this message and exit.            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ selfcheck  Audit the system for common issues.                                                   │
│ info       Show info about the product cache.                                                    │
│ dataset    Show the STAC metadata of the datasets.                                               │
│ seed       Seed the DEM to given bounds.                                                         │
│ clip       Clip the DEM to given bounds.                                                         │
│ clean      Clean up the product cache from temporary files.                                      │
│ distclean  Remove the product cache entirely.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

The `clip` sub-command:

```text
$ eio clip --help

 Usage: eio clip [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --output              -o      <file>                        Path to output file. Existing files  │
│                                                             will be overwritten.                 │
│                                                             [env var: EIO_CLIP_OUTPUT]           │
│                                                             [default: out.tif]                   │
│ --bounds                      <float float float float>...  Output bounds in 'left bottom right  │
│                                                             top' order.                          │
│                                                             [env var: EIO_CLIP_BOUNDS]           │
│ --margin              -m      <str>                         Decimal degree margin added to the   │
│                                                             bounds. Use '%' for percent margin.  │
│                                                             [env var: EIO_CLIP_MARGIN]           │
│                                                             [default: 0]                         │
│ --reference           -r      <path>                        Use the extent of a reference        │
│                                                             GDAL/OGR data source as output       │
│                                                             bounds.                              │
│                                                             [env var: EIO_CLIP_REFERENCE]        │
│ --gdal-options                <str>                         GDAL creation options of the output  │
│                                                             file, e.g. '-co COMPRESS=LZW'.       │
│                                                             [env var: EIO_CLIP_GDAL_OPTIONS]     │
│                                                             [default: -co TILED=YES -co          │
│                                                             COMPRESS=DEFLATE -co ZLEVEL=9 -co    │
│                                                             PREDICTOR=2]                         │
│ --max_download_tiles          <int>                         Maximum number of tiles to download. │
│                                                             [env var:                            │
│                                                             EIO_CLIP_MAX_DOWNLOAD_TILES]         │
│                                                             [default: 25]                        │
│ --help                                                      Show this message and exit.          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

The `seed` sub-command downloads and caches the tiles that cover the bounds
without producing any output file:

```text
$ eio seed --help

 Usage: eio seed [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --bounds                      <float float float float>...  Output bounds in 'left bottom right  │
│                                                             top' order.                          │
│                                                             [env var: EIO_SEED_BOUNDS]           │
│ --margin              -m      <str>                         Decimal degree margin added to the   │
│                                                             bounds. Use '%' for percent margin.  │
│                                                             [env var: EIO_SEED_MARGIN]           │
│                                                             [default: 0]                         │
│ --max_download_tiles          <int>                         Maximum number of tiles to download. │
│                                                             [env var:                            │
│                                                             EIO_SEED_MAX_DOWNLOAD_TILES]         │
│                                                             [default: 25]                        │
│ --help                                                      Show this message and exit.          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Defaults can be defined by setting environment variables prefixed with `EIO`,
e.g. `EIO_PRODUCT=SRTM3`, `EIO_CLIP_MARGIN=10%` and `EIO_CACHE_DIR=/tmp/elevation`.
`EIO_CACHE_DIR` selects the DEM cache folder and is honoured by the Python API as well.
The default is the `elevation` folder of the operating system user cache directory.

## Python API

Every command has a corresponding API function in the `elevation` module:

```python
>>> import elevation
>>> # clip the 30m DEM of Rome and save it to Rome-DEM.tif
>>> elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output="Rome-DEM.tif")
>>> # clean up the product cache from temporary files
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
