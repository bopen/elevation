# Migrating from 1.x to 2.0

This guide describes the backward-incompatible changes in elevation 2.0 and the steps
needed to migrate an existing 1.x setup.
New features and the current usage are documented in the README.

## Datasets

The default 1.x dataset was the Terrain Tiles mosaic, erroneously called `SRTM1`: it is
still the default dataset but is now called `TERRAIN_TILES`, a more fitting name. A plain
`eio clip` keeps downloading the same data as in 1.x.

The `SRTM1` name is retired: requesting it raises `elevation.ProductRetiredError`, a
subclass of `KeyError`, from the Python API and an `Invalid value for --product` usage
error from the `eio` command line, in both cases with a pointer to this page.

Correspondence between the 1.x and 2.0 datasets:

| elevation 1.x | elevation 2.0 | Data |
| --- | --- | --- |
| `SRTM1` | `TERRAIN_TILES` (default) | Terrain Tiles global 30m v1, the mosaic of 30m DEMs assembled by Mapzen |
| — | `SRTM1_GEOID` | SRTM global 30m v3 hosted on OpenTopography, 30m heights on the EGM96 geoid |
| `SRTM1_ELLIP` | `SRTM1_ELLIP` | SRTM global 30m v3 ellipsoidal, 30m heights on the WGS84 ellipsoid |
| `SRTM3` | `SRTM3` | SRTM global 90m v4.1, CGIAR-CSI |

## Cache

The DEM tiles downloaded from the data providers are kept in the elevation cache folder,
in a sub-folder named after the dataset, for example `~/Library/Caches/elevation` on macOS.
Run `eio info` to print the folder of the current dataset (the cache folder is its parent).

A 1.x installation keeps the Terrain Tiles data in the old `SRTM1` sub-folder, so to avoid
downloading it again move the tiles into the new folder:

```text
mv <cache_folder>/SRTM1/cache/* <cache_folder>/TERRAIN_TILES/cache/
```

The `SRTM3` and `SRTM1_ELLIP` datasets are reused as they are.

## Packaging

- elevation 2.0 requires Python 3.11 or later.
