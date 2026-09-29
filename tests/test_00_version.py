#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#

import elevation


def test_version() -> None:
    assert elevation.__version__ != "999"
