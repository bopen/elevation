#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest
import typer.testing
from pytest_mock import MockerFixture

import elevation
from elevation import __main__


def test_eio_version() -> None:
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["--version"])
    assert not result.exception
    assert "eio, version" in result.output


def test_eio_selfcheck(mocker: MockerFixture) -> None:
    runner = typer.testing.CliRunner()
    mock_check_output = mocker.patch("subprocess.check_output")
    result = runner.invoke(__main__.app, ["selfcheck"])
    assert not result.exception
    assert mock_check_output.call_count == len(elevation.TOOLS)


def test_eio_selfcheck_verbose(mocker: MockerFixture) -> None:
    runner = typer.testing.CliRunner()
    mock_check_output = mocker.patch("subprocess.check_output")
    result = runner.invoke(__main__.app, ["selfcheck", "--verbose"])
    assert not result.exception
    assert mock_check_output.call_count == len(elevation.TOOLS)
    for tool_name, _ in elevation.TOOLS:
        assert f"Checking {tool_name!r} ..." in result.output


def test_eio_dataset() -> None:
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["dataset"])
    assert not result.exception
    for dataset in elevation.PRODUCTS:
        assert f"id: {dataset}\n" in result.output


def test_eio_dataset_one() -> None:
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["dataset", "SRTM3"])
    assert not result.exception
    assert result.output.count("id: ") == 1
    assert "id: SRTM3\n" in result.output


def test_eio_dataset_invalid() -> None:
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["dataset", "BOGUS"])
    assert result.exit_code == 2


def test_parent_params_reach_subcommand(tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    result = runner.invoke(
        __main__.app, ["--product", "SRTM3", "--cache_dir", str(root), "info"]
    )
    assert not result.exception
    assert f"Product folder: {root / 'SRTM3'}" in result.output


def test_invalid_product() -> None:
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["--product", "BOGUS", "info"])
    assert result.exit_code == 2


def test_retired_product(tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    result = runner.invoke(
        __main__.app, ["--product", "SRTM1", "--cache_dir", str(root), "info"]
    )
    assert result.exit_code == 2
    assert not root.exists()


def test_eio_info(tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, f"--cache_dir {root!s} info".split())
    assert not result.exception
    assert f"Product folder: {root / 'MAPZEN'}" in result.output


def test_eio_seed(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} seed --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    mocker.patch("elevation.datasource.fetch_tile")
    mocker.patch("elevation.spatial.call_gdal_translate")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1
    assert mock_check_call.call_args[0][0][0] == "gdalbuildvrt"


def test_eio_seed_margin(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    mock_seed = mocker.patch("elevation.seed")
    result = runner.invoke(
        __main__.app,
        f"--cache_dir {root!s} seed --bounds 12.5 42 12.5 42 -m 1".split(),
    )
    assert not result.exception
    assert mock_seed.call_args.kwargs["margin"] == "1"


def test_eio_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} clip --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    mocker.patch("elevation.datasource.fetch_tile")
    mock_translate = mocker.patch("elevation.spatial.call_gdal_translate")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1
    assert mock_translate.call_count == 1

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, ["clip"])
    assert result.exception
    assert mock_check_call.call_count == 0

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, ["clip", "--reference", "."])
    assert result.exception
    assert mock_check_call.call_count == 0


def test_eio_clip_gdal_options(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    mocker.patch("subprocess.check_call")
    mocker.patch("elevation.datasource.fetch_tile")
    mock_translate = mocker.patch("elevation.spatial.call_gdal_translate")

    result = runner.invoke(
        __main__.app,
        [
            "--cache_dir",
            str(root),
            "clip",
            "--bounds",
            "12.5",
            "42",
            "12.5",
            "42",
            "--gdal-options",
            "-co COMPRESS=LZW",
        ],
    )

    assert not result.exception
    assert "COMPRESS=LZW" in mock_translate.call_args.kwargs["options"]


def test_eio_clean(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "MAPZEN" / "spool").mkdir(parents=True)
    (root / "MAPZEN" / "spool" / "stale.hgt").write_text("stale")
    runner = typer.testing.CliRunner()

    result = runner.invoke(__main__.app, f"--cache_dir {root!s} clean".split())

    assert not result.exception
    assert not (root / "MAPZEN" / "spool").exists()


def test_eio_distclean(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "MAPZEN" / "cache").mkdir(parents=True)
    (root / "MAPZEN" / "cache" / "tile.tif").write_bytes(b"data")
    runner = typer.testing.CliRunner()

    result = runner.invoke(__main__.app, f"--cache_dir {root!s} distclean".split())

    assert not result.exception
    assert not (root / "MAPZEN" / "cache").exists()


def test_eio(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} seed --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    mocker.patch("elevation.datasource.fetch_tile")
    mocker.patch("elevation.spatial.call_gdal_translate")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio_cache_dir_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "root"
    monkeypatch.setenv("EIO_CACHE_DIR", str(root))
    runner = typer.testing.CliRunner()
    result = runner.invoke(__main__.app, ["info"])
    assert not result.exception
    assert f"Product folder: {root / 'MAPZEN'}" in result.output
