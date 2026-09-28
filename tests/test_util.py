#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

from pathlib import Path

from pytest_mock import MockerFixture

from elevation import util


def test_selfcheck() -> None:
    assert "NAME" not in util.selfcheck({"NAME": "true"})
    assert "NAME" in util.selfcheck({"NAME": "false"})


def test_lock_tiles(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with util.lock_tiles(root, ["a.tiff"]):
        assert (root / "cache" / "a.tiff.lock").exists()


def test_lock_vrt(tmp_path: Path) -> None:
    root = tmp_path / "root"

    with util.lock_vrt(root, "SRTM1"):
        assert (root / "SRTM1.vrt.lock").exists()


def test_ensure_setup(tmp_path: Path) -> None:
    root = tmp_path / "root"
    created_folders, _ = util.ensure_setup(root)
    assert len(created_folders) == 0
    assert len(list(tmp_path.iterdir())) == 1

    folders = ["etc", "lib"]
    created_folders, _ = util.ensure_setup(root, folders=folders)
    assert len(created_folders) == 2
    assert created_folders[0].name == "etc"
    assert created_folders[1].name == "lib"
    assert len(list(root.iterdir())) == 3

    file_templates = {"Makefile": "all: {target}"}
    created_folders, created_files = util.ensure_setup(
        root, folders=folders, file_templates=file_templates, target="file.txt"
    )
    assert len(created_folders) == 0
    assert len(created_files) == 1
    assert len(list(root.iterdir())) == 4
    assert (root / "Makefile").read_text() == "all: file.txt"

    created_folders, created_files = util.ensure_setup(
        root, folders=folders, file_templates=file_templates, target="wrong"
    )
    assert len(created_folders) == 0
    assert len(created_files) == 0
    assert len(list(root.iterdir())) == 4
    assert (root / "Makefile").read_text() == "all: file.txt"


def test_check_call_make(mocker: MockerFixture) -> None:
    mock_check_call = mocker.patch("subprocess.check_call")
    cmd = util.check_call_make(Path("/tmp"))
    assert cmd.strip() == "make -C /tmp"
    mock_check_call.assert_called_once_with(cmd, shell=True)
