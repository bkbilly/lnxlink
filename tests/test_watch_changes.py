"""Tests for replacing the watched configuration file."""
# pylint: disable=missing-class-docstring,missing-function-docstring

import os
import tempfile
import time
from unittest.mock import patch

from lnxlink.modules import watch_changes


class FakeLnxlink:
    def __init__(self, path):
        self.config_path = path
        self.restart_calls = 0

    def restart_script(self):
        self.restart_calls += 1


def test_missing_config_does_not_crash_and_recreated_file_triggers_restart():
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "wb") as handler:
            handler.write(b"alpha")

        lnxlink = FakeLnxlink(path)
        addon = watch_changes.Addon(lnxlink)

        addon.get_info()
        assert lnxlink.restart_calls == 0

        os.remove(path)
        addon.get_info()
        assert lnxlink.restart_calls == 0

        time.sleep(1.1)
        with open(path, "wb") as handler:
            handler.write(b"bravo")
        os.utime(path, None)

        addon.get_info()
        assert lnxlink.restart_calls == 1
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_replacement_appearing_during_setup_is_not_adopted_without_mtime():
    lnxlink = FakeLnxlink("/tmp/lnxlink.yaml")

    with patch.object(
        watch_changes.Addon, "_get_file_mtime", side_effect=[None, 123]
    ), patch.object(
        watch_changes.Addon, "_get_file_hash", return_value="replacement"
    ) as get_hash:
        addon = watch_changes.Addon(lnxlink)
        assert addon.last_hash is None
        get_hash.assert_not_called()

        addon.get_info()

    assert lnxlink.restart_calls == 1


def test_replacement_with_preserved_mtime_is_hashed_after_disappearance():
    lnxlink = FakeLnxlink("/tmp/lnxlink.yaml")
    hashes = iter(["original", "replacement"])

    with patch.object(
        watch_changes.Addon, "_get_file_mtime", side_effect=[123, None, 123]
    ), patch.object(
        watch_changes.Addon, "_get_file_hash", side_effect=lambda _path: next(hashes)
    ):
        addon = watch_changes.Addon(lnxlink)
        addon.get_info()
        addon.get_info()

    assert lnxlink.restart_calls == 1


def test_replacement_with_preserved_mtime_is_hashed_after_stat_read_race():
    lnxlink = FakeLnxlink("/tmp/lnxlink.yaml")

    with patch.object(
        watch_changes.Addon, "_get_file_mtime", side_effect=[123, 456, 123]
    ), patch.object(
        watch_changes.Addon,
        "_get_file_hash",
        side_effect=["original", None, "replacement"],
    ):
        addon = watch_changes.Addon(lnxlink)
        addon.get_info()
        addon.get_info()

    assert lnxlink.restart_calls == 1
