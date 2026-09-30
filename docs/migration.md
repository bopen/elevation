# Migrating from 1.x to 2.0

## Datasets

| elevation 1.x | elevation 2.0 | Data |
| --- | --- | --- |
| `SRTM1` | `TERRAIN_TILES` (default) | Terrain Tiles, the global mosaic of 30m DEMs assembled by Mapzen |
| — | `SRTM1_GEOID` | SRTM GL1 hosted on OpenTopography, 30m heights on the EGM96 geoid |
| `SRTM1_ELLIP` | `SRTM1_ELLIP` | SRTM GL1, 30m heights on the WGS84 ellipsoid |
| `SRTM3` | `SRTM3` | SRTM 90m, CGIAR-CSI |

The 1.x `SRTM1` product was the Terrain Tiles mosaic and is now called `TERRAIN_TILES`.

The `SRTM1` name is retired: requesting it raises `elevation.ProductRetiredError`, a
subclass of `KeyError`, from the Python API and an `Invalid value for --product` usage
error from the `eio` command line, in both cases with a pointer to this page.

`TERRAIN_TILES` is the default product, so a plain `eio clip` keeps downloading the same
data that `eio --product SRTM1 clip` downloaded in 1.x.

## Cache

The DEM cache is back in the `elevation` user cache folder, for example
`~/Library/Caches/elevation` on macOS, and only the products whose data changed need a new
download:

- the 1.x `SRTM1` folder holds exactly the `TERRAIN_TILES` data, so it can be renamed
  instead of downloaded again:

```text
mv <cache>/SRTM1 <cache>/TERRAIN_TILES
```

- `SRTM3` and `SRTM1_ELLIP` are reused as they are;
- `SRTM1_GEOID` is a new product and is downloaded from scratch.

## Python API

- `elevation.CACHE_DIR` is a `str` and points to the user cache folder.
- `elevation.PRODUCTS` is `["TERRAIN_TILES", "SRTM1_GEOID", "SRTM1_ELLIP", "SRTM3"]`.
- Path-valued arguments accept `str` or `Path`, and relative paths are resolved against the
  current working directory; `elevation.seed()` returns a `Path`.
- `elevation.TOOLS` is a list of `(name, command)` pairs and `elevation.selfcheck()` accepts
  a mapping or a list of pairs.

## Command line

- `--product` takes the new product names and `--reference` must point to an existing
  file.
- `--make_options`, and the `EIO_MAKE_OPTIONS` environment variable, pass options through
  to every `make` invocation.
- The other `EIO_*` environment variables are unchanged.

## Packaging

- elevation 2.0 requires Python 3.11 or later; the `eio` command line entry point is
  unchanged.
