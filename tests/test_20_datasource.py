#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

import elevation
from elevation import datasource, spatial

DATA_DIR = Path(__file__).parent / "data"
REFERENCE = DATA_DIR / "reference.tif"


def write_ready_tile(source: str | Path, ready: Path, **kwargs: Any) -> None:
    """Stand in for the mocked cache write: leave a tile for the cache move."""
    ready.parent.mkdir(parents=True, exist_ok=True)
    ready.write_bytes(b"tile")


def test_latlon_to_indeces_CGIAR_L1_TILE_INDECES_TRANSFORM() -> None:
    transform = datasource.CGIAR_L1_TILE_INDECES_TRANSFORM
    # values from https://srtm.csi.cgiar.org/SELECTION/inputCoord.asp
    assert datasource.latlon_to_indeces(transform, -177.5, 52.5) == (1, 2)
    assert datasource.latlon_to_indeces(transform, 177.5, -47.5) == (72, 22)
    assert datasource.latlon_to_indeces(transform, 10.1, 44.9) == (39, 4)
    assert datasource.latlon_to_indeces(transform, 14.9, 44.9) == (39, 4)
    assert datasource.latlon_to_indeces(transform, 10.1, 40.1) == (39, 4)
    assert datasource.latlon_to_indeces(transform, 14.9, 40.1) == (39, 4)


def test_latlon_to_indeces_DTED_L2_TILE_INDECES_TRANSFORM() -> None:
    transform = datasource.DTED_L2_TILE_INDECES_TRANSFORM
    # the 1 degree tiles of the SRTM1 products, e.g. N44E010 covers 10E-11E
    assert datasource.latlon_to_indeces(transform, 10.1, 44.9) == (10, 44)
    assert datasource.latlon_to_indeces(transform, -73.99, 7.056) == (-74, 7)
    assert datasource.latlon_to_indeces(transform, 15.931, -19.194) == (15, -20)
    # a whole degree is a tile node, shared by the two tiles that meet there,
    # and the half pixel makes it belong to the one that starts at the node
    assert datasource.latlon_to_indeces(transform, 10.0, 44.0) == (10, 44)


def test_latlon_to_indeces_EDH_L2_CHUNK_INDECES_TRANSFORM() -> None:
    transform = datasource.EDH_L2_CHUNK_INDECES_TRANSFORM
    # the chunks of the Copernicus store are 1 by 0.5 degrees and 192_96 is
    # the Rome region of the integration tests
    assert datasource.latlon_to_indeces(transform, 12.4, 41.9) == (192, 96)
    assert datasource.latlon_to_indeces(transform, 12.4, 41.4) == (192, 97)
    # the chunks at the north west and the south east corner of the store
    assert datasource.latlon_to_indeces(transform, -180.0, 90.0) == (0, 0)
    assert datasource.latlon_to_indeces(transform, 179.9, -89.9) == (359, 359)
    # the chunk boundaries are half a pixel outside the whole degrees, so a
    # bound on a whole degree falls in the chunk that starts there
    assert datasource.latlon_to_indeces(transform, 13.0, 41.5) == (193, 97)


def test_latlon_to_indeces_EDH_L1_CHUNK_INDECES_TRANSFORM() -> None:
    transform = datasource.EDH_L1_CHUNK_INDECES_TRANSFORM
    # the chunks of the Copernicus store are 2 by 2 degrees at 3 arc seconds,
    # 96_24 is the Rome region of the integration tests
    assert datasource.latlon_to_indeces(transform, 12.4, 41.9) == (96, 24)
    assert datasource.latlon_to_indeces(transform, 15.0, 39.9) == (97, 25)
    # the chunks at the north west and the south east corner of the store
    assert datasource.latlon_to_indeces(transform, -180.0, 90.0) == (0, 0)
    assert datasource.latlon_to_indeces(transform, 179.9, -89.9) == (179, 89)
    # an even degree is a chunk boundary, half a pixel west of it, so a bound
    # that lands on one, like 14.0, reaches the chunk that starts there
    assert datasource.latlon_to_indeces(transform, 14.0, 41.9) == (97, 24)


def test_dted_l2_tiles() -> None:
    assert list(datasource.dted_l2_tiles(10.1, 44.9, 10.1, 44.9)) == [
        ((10, 44), "N44E010.tif")
    ]
    # NOTE this also tests int (not float) input
    assert list(datasource.dted_l2_tiles(10, 44, 11, 45)) == [((10, 44), "N44E010.tif")]


def test_mapzen_tiles() -> None:
    # MAPZEN is the DTED L2 lattice with a subfolder in the tile name
    spec = datasource.MAPZEN_SPEC
    tiles = spec["cached_tiles"]
    kwargs = spec["cached_tiles_kwargs"]

    assert list(tiles(10.1, 44.9, 10.1, 44.9, **kwargs)) == [
        ((10, 44), "N44/N44E010.tif")
    ]
    # NOTE this also tests int (not float) input
    assert list(tiles(10, 44, 11, 45, **kwargs)) == [((10, 44), "N44/N44E010.tif")]


def test_cgiar_l1_tiles() -> None:
    assert next(datasource.cgiar_l1_tiles(10.1, 44.9, 10.1, 44.9)) == (
        (39, 4),
        "srtm_39_04.tif",
    )
    assert next(datasource.cgiar_l1_tiles(25.50, 58.40, 27.67, 60.06)) == (
        (42, 1),
        "srtm_42_01.tif",
    )
    assert len(list(datasource.cgiar_l1_tiles(9.9, 39.1, 15.1, 45.1))) == 9


def test_srtm_ellip_tiles() -> None:
    ds1 = [((10, 44), "North/North_30_60/N44E010_wgs84.tif")]
    ds2 = [((-74, 7), "North/North_0_29/N07W074_wgs84.tif")]
    ds3 = [((15, -20), "South/S20E015_wgs84.tif")]
    assert list(datasource.srtm_ellip_tiles(10.1, 44.9, 10.1, 44.9)) == ds1
    assert list(datasource.srtm_ellip_tiles(-73.99, 7.056, -73.90, 7.660)) == ds2
    assert list(datasource.srtm_ellip_tiles(15.931, -19.194, 15.329, -19.961)) == ds3
    # the tiles share their edge row and column, so a bound on a whole degree
    # does not reach the tiles that start there
    assert list(datasource.srtm_ellip_tiles(10.1, 44.1, 12.0, 46.0)) == [
        ((10, 44), "North/North_30_60/N44E010_wgs84.tif"),
        ((10, 45), "North/North_30_60/N45E010_wgs84.tif"),
        ((11, 44), "North/North_30_60/N44E011_wgs84.tif"),
        ((11, 45), "North/North_30_60/N45E011_wgs84.tif"),
    ]


def test_tile_source() -> None:
    # a product that serves plain tiles declares only its datasource URL
    spec = datasource.SRTM1_GEOID_SPEC
    kwargs = dict(spec["prepare_tile_kwargs"])
    datasource_url = kwargs.pop("datasource_url")
    assert kwargs == {}
    url, spooled, member = datasource.tile_source(
        datasource_url, "N41E012.tif", **kwargs
    )
    assert url == f"{datasource_url}/N41E012.tif"
    assert spooled == "N41E012.tif"
    assert member is None

    # MAPZEN serves the DTED tiles gunzipped, so the spool name drops the .gz
    spec = datasource.MAPZEN_SPEC
    kwargs = dict(spec["prepare_tile_kwargs"])
    datasource_url = kwargs.pop("datasource_url")
    assert kwargs == {"tile_ext": ".hgt", "compressed_ext": ".hgt.gz"}
    url, spooled, member = datasource.tile_source(
        datasource_url, "N41/N41E012.tif", **kwargs
    )
    assert url == f"{datasource_url}/N41/N41E012.hgt.gz"
    assert spooled == "N41/N41E012.hgt"
    assert member is None

    # the SRTM3 tiles are served inside a .zip, that the spec has to declare or
    # seed asks for a plain .tif that the provider does not have
    spec = datasource.SRTM3_SPEC
    kwargs = dict(spec["prepare_tile_kwargs"])
    datasource_url = kwargs.pop("datasource_url")
    assert kwargs == {"compressed_ext": ".zip"}
    url, spooled, member = datasource.tile_source(
        datasource_url, "srtm_39_04.tif", **kwargs
    )
    assert url == f"{datasource_url}/srtm_39_04.zip"
    assert spooled == "srtm_39_04.tif"
    assert member == "srtm_39_04.tif"

    # the SRTM1 ellipsoidal tiles keep the name and the subfolder of the cache
    spec = datasource.SRTM1_ELLIP_SPEC
    kwargs = dict(spec["prepare_tile_kwargs"])
    datasource_url = kwargs.pop("datasource_url")
    url, spooled, member = datasource.tile_source(
        datasource_url, "North/North_30_60/N44E010_wgs84.tif"
    )
    assert url == f"{datasource_url}/North/North_30_60/N44E010_wgs84.tif"
    assert spooled == "North/North_30_60/N44E010_wgs84.tif"
    assert member is None


def test_ensure_tiles(mocker: MockerFixture, tmp_path: Path) -> None:
    spec = datasource.SRTM1_GEOID_SPEC
    mock_fetch = mocker.patch("elevation.datasource.fetch_tile")
    mock_write = mocker.patch(
        "elevation.spatial.call_gdal_translate", side_effect=write_ready_tile
    )

    datasource.ensure_tiles(
        tmp_path,
        [((12, 41), "N41E012.tif")],
        prepare_tile=spec["prepare_tile"],
        **spec["prepare_tile_kwargs"],
    )

    mock_fetch.assert_called_once_with(
        f"{spec['prepare_tile_kwargs']['datasource_url']}/N41E012.tif",
        tmp_path / "spool" / "N41E012.tif",
        member=None,
    )
    mock_write.assert_called_once_with(
        str(tmp_path / "spool" / "N41E012.tif"),
        tmp_path / "spool" / "ready" / "N41E012.tif",
        options=spatial.INT_TILE_GDAL_OPTIONS,
    )
    # the tile reaches the cache only once it has been written in the spool
    assert (tmp_path / "cache" / "N41E012.tif").read_bytes() == b"tile"


def test_ensure_tiles_skips_cached(mocker: MockerFixture, tmp_path: Path) -> None:
    spec = datasource.SRTM1_GEOID_SPEC
    cached = tmp_path / "cache" / "N41E012.tif"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"cached")
    mock_fetch = mocker.patch("elevation.datasource.fetch_tile")
    mock_write = mocker.patch("elevation.spatial.call_gdal_translate")

    datasource.ensure_tiles(
        tmp_path,
        [((12, 41), "N41E012.tif")],
        prepare_tile=spec["prepare_tile"],
        **spec["prepare_tile_kwargs"],
    )

    mock_fetch.assert_not_called()
    mock_write.assert_not_called()
    assert cached.read_bytes() == b"cached"


def test_ensure_tiles_remote(mocker: MockerFixture, tmp_path: Path) -> None:
    spec = datasource.GLO_90_SPEC
    mock_fetch = mocker.patch("elevation.datasource.fetch_tile")
    mock_write = mocker.patch(
        "elevation.spatial.call_gdal_translate", side_effect=write_ready_tile
    )
    # the chunk the Rome bounds of the integration tests fall in
    tiles = list(
        spec["cached_tiles"](12.4, 41.8, 12.4, 41.8, **spec["cached_tiles_kwargs"])
    )
    assert tiles == [((96, 24), "24/96.tif")]

    datasource.ensure_tiles(
        tmp_path,
        tiles,
        prepare_tile=spec["prepare_tile"],
        gdal_options=spec["tile_gdal_options"],
        **spec["prepare_tile_kwargs"],
    )

    # a store is read in place: no download, one window per chunk, and the
    # connection string keeps the CRS in the store, so no ``:/dsm`` suffix
    mock_fetch.assert_not_called()
    mock_write.assert_called_once_with(
        "-srcwin 230400 57600 2400 2400 "
        'ZARR:"/vsicurl/https://data.earthdatahub.destine.eu'
        '/copernicus-dem/GLO-90-v1.zarr":/dsm',
        tmp_path / "spool" / "ready" / "24/96.tif",
        options=spatial.FLOAT_TILE_GDAL_OPTIONS,
    )
    assert (tmp_path / "cache" / "24/96.tif").read_bytes() == b"tile"


def test_fetch_tile(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    datasource.fetch_tile(REFERENCE.as_uri(), destination)

    assert destination.read_bytes() == REFERENCE.read_bytes()


def test_fetch_tile_gzip(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    datasource.fetch_tile((DATA_DIR / "reference.tif.gz").as_uri(), destination)

    assert destination.read_bytes() == REFERENCE.read_bytes()


def test_fetch_tile_zip(tmp_path: Path) -> None:
    destination = tmp_path / "spool" / "tile.tif"

    datasource.fetch_tile(
        (DATA_DIR / "reference.zip").as_uri(), destination, member="reference.tif"
    )

    assert destination.read_bytes() == REFERENCE.read_bytes()


def test_do_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    bounds = (13.1, 43.1, 14.9, 44.9)
    mock_check_call = mocker.patch("subprocess.check_call")

    cmd = datasource.do_clip(
        path=tmp_path, bounds=bounds, output=Path("/out.tif"), product="SRTM3"
    )

    expected_cmd = [
        "gdal_translate",
        "-q",
        *datasource.DEFAULT_GDAL_OPTIONS.split(),
        "-projwin",
        "13.1",
        "44.9",
        "14.9",
        "43.1",
        str(tmp_path / "SRTM3.vrt"),
        "/out.tif",
    ]
    assert cmd == expected_cmd
    mock_check_call.assert_called_once_with(cmd)


def test_do_clip_gdal_options(mocker: MockerFixture, tmp_path: Path) -> None:
    mock_check_call = mocker.patch("subprocess.check_call")

    cmd = datasource.do_clip(
        path=tmp_path,
        bounds=(1.0, 2.0, 3.0, 4.0),
        output=Path("/out.tif"),
        product="SRTM3",
        gdal_options="-co COMPRESS=LZW",
    )

    expected_cmd = [
        "gdal_translate",
        "-q",
        "-co",
        "COMPRESS=LZW",
        "-projwin",
        "1.0",
        "4.0",
        "3.0",
        "2.0",
        str(tmp_path / "SRTM3.vrt"),
        "/out.tif",
    ]
    assert cmd == expected_cmd
    mock_check_call.assert_called_once_with(cmd)


def test_seed(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    bounds = (13.1, 43.1, 13.9, 43.9)
    spec = datasource.SRTM1_GEOID_SPEC
    mock_check_call = mocker.patch("subprocess.check_call")
    mock_fetch = mocker.patch("elevation.datasource.fetch_tile")
    mock_write = mocker.patch(
        "elevation.spatial.call_gdal_translate", side_effect=write_ready_tile
    )

    datasource_root = datasource.seed(
        cache_dir=root, product="SRTM1_GEOID", bounds=bounds
    )

    assert datasource_root == root / "SRTM1_GEOID"
    mock_fetch.assert_called_once_with(
        f"{spec['prepare_tile_kwargs']['datasource_url']}/N43E013.tif",
        datasource_root / "spool" / "N43E013.tif",
        member=None,
    )
    mock_write.assert_called_once_with(
        str(datasource_root / "spool" / "N43E013.tif"),
        datasource_root / "spool" / "ready" / "N43E013.tif",
        options=spatial.INT_TILE_GDAL_OPTIONS,
    )
    assert mock_check_call.call_args[0][0][0] == "gdalbuildvrt"

    with pytest.raises(RuntimeError):
        datasource.seed(cache_dir=root, bounds=(-180, -90, 180, 90))

    with pytest.raises(TypeError, match="bounds must be supplied"):
        datasource.seed(cache_dir=root)


def test_seed_remote(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    mock_check_call = mocker.patch("subprocess.check_call")
    mock_fetch = mocker.patch("elevation.datasource.fetch_tile")
    mock_write = mocker.patch(
        "elevation.spatial.call_gdal_translate", side_effect=write_ready_tile
    )

    datasource_root = datasource.seed(
        cache_dir=root,
        product="GLO-30",
        bounds=(12.4, 41.8, 12.4 + 100 / 3600, 41.8 + 100 / 3600),
    )

    assert datasource_root == root / "GLO-30"
    # the store is read in place, one window per chunk of the 1 by 0.5 degrees
    # grid, and the tile name mirrors the chunk layout
    mock_fetch.assert_not_called()
    mock_write.assert_called_once_with(
        "-srcwin 691200 172800 3600 1800 "
        'ZARR:"/vsicurl/https://data.earthdatahub.destine.eu'
        '/copernicus-dem/GLO-30-v1.zarr":/dsm',
        datasource_root / "spool" / "ready" / "96/192.tif",
        options=spatial.FLOAT_TILE_GDAL_OPTIONS,
    )
    assert (datasource_root / "cache" / "96/192.tif").read_bytes() == b"tile"
    assert mock_check_call.call_args[0][0][0] == "gdalbuildvrt"

    with pytest.raises(RuntimeError):
        datasource.seed(
            cache_dir=root, product="GLO-30", bounds=(0.0, -100.0, 100.0, 0.0)
        )


def test_build_bounds() -> None:
    raw_bounds = (13.1, 43.1, 13.9, 43.9)
    assert datasource.build_bounds(raw_bounds, margin="0") == raw_bounds

    assert datasource.build_bounds(raw_bounds, margin="0.08") == (
        13.02,
        43.02,
        13.98,
        43.98,
    )
    assert datasource.build_bounds(raw_bounds, margin="10%") == (
        13.02,
        43.02,
        13.98,
        43.98,
    )


def test_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    bounds = (13.1, 43.1, 14.9, 44.9)
    output = tmp_path / "out.tif"
    mocker.patch("subprocess.check_call")
    mocker.patch("elevation.datasource.fetch_tile")
    mock_translate = mocker.patch(
        "elevation.spatial.call_gdal_translate", side_effect=write_ready_tile
    )

    datasource.clip(cache_dir=root, bounds=bounds, output=output)

    datasource_root = root / "MAPZEN"
    # the clip is the last call, after the one call per cached tile
    source, destination = mock_translate.call_args.args
    assert source == str(datasource_root / "MAPZEN.vrt")
    assert destination == output
    assert mock_translate.call_args.kwargs["options"] == (
        f"-q {datasource.DEFAULT_GDAL_OPTIONS} -projwin 13.1 44.9 14.9 43.1"
    )


def test_clean(tmp_path: Path) -> None:
    cache_dir = tmp_path / "root"
    root = cache_dir / "MAPZEN"
    (root / "cache" / "N41").mkdir(parents=True)
    (root / "cache" / "N41" / "empty.tif").write_bytes(b"")
    (root / "cache" / "N41" / "full.tif").write_bytes(b"data")
    (root / "MAPZEN.deadbeef.vrt").write_text("vrt")
    (root / "spool").mkdir()
    (root / "spool" / "N41E012.hgt").write_text("tile")

    datasource.clean(cache_dir=cache_dir)

    assert not (root / "cache" / "N41" / "empty.tif").exists()
    assert (root / "cache" / "N41" / "full.tif").exists()
    assert not (root / "MAPZEN.deadbeef.vrt").exists()
    assert not (root / "spool").exists()


def test_retired_product() -> None:
    assert issubclass(elevation.ProductRetiredError, KeyError)
    with pytest.raises(elevation.ProductRetiredError) as excinfo:
        datasource.info(product="SRTM1")
    assert str(excinfo.value) == elevation.RETIRED_PRODUCTS["SRTM1"]


def test_cache_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    default = tmp_path / "default"
    override = tmp_path / "override"
    argument = tmp_path / "argument"
    monkeypatch.setattr(datasource, "CACHE_DIR", default)

    assert f"Product folder: {default.resolve() / 'MAPZEN'}" in datasource.info()

    monkeypatch.setenv("EIO_CACHE_DIR", str(override))
    assert f"Product folder: {override.resolve() / 'MAPZEN'}" in datasource.info()

    report = datasource.info(cache_dir=argument)
    assert f"Product folder: {argument.resolve() / 'MAPZEN'}" in report


def test_info(tmp_path: Path) -> None:
    cache_dir = tmp_path / "root"
    (cache_dir / "MAPZEN" / "cache" / "N41").mkdir(parents=True)
    (cache_dir / "MAPZEN" / "cache" / "N41" / "tile.tif").write_bytes(b"data")

    report = datasource.info(cache_dir=cache_dir)

    assert report.startswith("Product folder: ")
    assert "Tiles count: 1" in report
    assert "\nCache size: " in report


def test_dataset() -> None:
    assert "id: SRTM3\n" in elevation.dataset("SRTM3")
    assert "id: GLO-30\n" in elevation.dataset("GLO-30")
    text = elevation.dataset()
    assert text.count("id: ") == len(elevation.PRODUCTS)
    assert text.endswith("\n")
    assert text.count("\n---\n") == len(elevation.PRODUCTS) - 1
    assert "\n\n---\nid: SRTM1_GEOID\n" in text
    with pytest.raises(KeyError):
        elevation.dataset("BOGUS")
