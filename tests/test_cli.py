# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path
from typing import Any

import click.testing
from pytest_mock import MockerFixture

import elevation
from elevation import cli


def test_eio_selfcheck(mocker: MockerFixture) -> None:
    runner = click.testing.CliRunner()
    mock_check_output = mocker.patch("subprocess.check_output")
    result = runner.invoke(cli.selfcheck)
    assert not result.exception
    assert mock_check_output.call_count == len(elevation.TOOLS)


def test_click_merge_parent_params() -> None:
    runner = click.testing.CliRunner()

    @cli.eio.command("return_kwargs")
    @cli.click_merge_parent_params
    def return_kwargs(**kwargs: Any) -> None:
        print(kwargs)

    result = runner.invoke(cli.eio, "return_kwargs".split())
    assert not result.exception
    assert "product" in result.output and "cache_dir" in result.output

    result = runner.invoke(return_kwargs)
    assert not result.exception
    assert result.output == "{}\n"


def test_eio_info(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s info" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio_seed(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s seed --bounds 12.5 42 12.5 42" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 2


def test_eio_clip(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s clip --bounds 12.5 42 12.5 42" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 4

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, ["clip"])
    assert result.exception
    assert mock_check_call.call_count == 0

    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, "clip --reference .".split())
    assert result.exception
    assert mock_check_call.call_count == 0


def test_eio_clean(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s clean" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio_distclean(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s distclean" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 1


def test_eio(mocker: MockerFixture, tmp_path: Path) -> None:
    root = tmp_path / "root"
    runner = click.testing.CliRunner()
    options = "--cache_dir %s seed --bounds 12.5 42 12.5 42" % str(root)
    mock_check_call = mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert mock_check_call.call_count == 2
