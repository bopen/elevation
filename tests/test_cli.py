# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - http://bopen.eu
#

import subprocess

import click.testing

from elevation import cli


def test_eio_selfcheck(mocker):
    runner = click.testing.CliRunner()
    mocker.patch("subprocess.check_output")
    result = runner.invoke(cli.selfcheck)
    assert not result.exception
    assert subprocess.check_output.call_count == len(cli.elevation.TOOLS)


def test_click_merge_parent_params():
    runner = click.testing.CliRunner()

    @cli.eio.command("return_kwargs")
    @cli.click_merge_parent_params
    def return_kwargs(**kwargs):
        print(kwargs)

    result = runner.invoke(cli.eio, "return_kwargs".split())
    assert not result.exception
    assert "product" in result.output and "cache_dir" in result.output

    result = runner.invoke(return_kwargs)
    assert not result.exception
    assert result.output == "{}\n"


def test_eio_info(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s info" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 1


def test_eio_seed(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s seed --bounds 12.5 42 12.5 42" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 2


def test_eio_clip(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s clip --bounds 12.5 42 12.5 42" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 4

    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, ["clip"])
    assert result.exception
    assert subprocess.check_call.call_count == 0

    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, "clip --reference .".split())
    assert result.exception
    assert subprocess.check_call.call_count == 0


def test_eio_clean(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s clean" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 1


def test_eio_distclean(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s distclean" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 1


def test_eio(mocker, tmpdir):
    root = tmpdir.join("root")
    runner = click.testing.CliRunner()
    options = "--cache_dir %s seed --bounds 12.5 42 12.5 42" % str(root)
    mocker.patch("subprocess.check_call")
    result = runner.invoke(cli.eio, options.split())
    assert not result.exception
    assert subprocess.check_call.call_count == 2
