#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

import pytest
import typer.testing
from pytest_mock import MockerFixture

import elevation
from elevation import __main__


def test_eio_selfcheck(mocker: MockerFixture) -> None:
    runner = typer.testing.CliRunner()
    mock_check_output = mocker.patch("subprocess.check_output")
    result = runner.invoke(__main__.app, ["selfcheck"])
    assert not result.exception
    assert mock_check_output.call_count == len(elevation.TOOLS)


def test_parent_params_reach_subcommand(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(
        __main__.app, ["--product", "SRTM3", "--cache_dir", str(root), "info"]
    )
    assert not result.exception
    assert mock_check_call.call_count == 1
    expected_cmd = ["make", "-C", str(root / "SRTM3"), "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd


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


def test_eio_info(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} info"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio_seed(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} seed --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 2


def test_eio_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} clip --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 4

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, ["clip"])
    assert result.exception
    assert mock_check_call.call_count == 0

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, ["clip", "--reference", "."])
    assert result.exception
    assert mock_check_call.call_count == 0


def test_eio_clean(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} clean"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio_distclean(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} distclean"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    options = f"--cache_dir {root!s} seed --bounds 12.5 42 12.5 42"
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 2


def test_eio_cache_dir_env(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    monkeypatch.setenv("EIO_CACHE_DIR", str(root))
    runner = typer.testing.CliRunner()
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(__main__.app, ["info"])
    assert not result.exception
    expected_cmd = ["make", "-C", str(root / "TERRAIN_TILES"), "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd


def test_eio_make_options(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = typer.testing.CliRunner()
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(
        __main__.app, ["--cache_dir", str(root), "--make_options=-s", "info"]
    )
    assert not result.exception
    expected_cmd = ["make", "-C", str(root / "TERRAIN_TILES"), "-s", "info"]
    assert mock_check_call.call_args[0][0] == expected_cmd
