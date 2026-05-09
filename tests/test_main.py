"""Tests for the lnxlink command-line entry point."""

# pylint: disable=missing-function-docstring

import sys
import unittest
from unittest import mock

from lnxlink import __main__ as lnxlink_main


class MainTests(unittest.TestCase):
    """Tests for CLI startup behavior."""

    def test_failed_mqtt_start_exits_nonzero(self):
        with (
            mock.patch.object(sys, "argv", ["lnxlink", "--ignore-systemd"]),
            mock.patch.object(lnxlink_main.files_setup, "setup_logger"),
            mock.patch.object(lnxlink_main.config_setup, "setup_config"),
            mock.patch.object(
                lnxlink_main.files_setup,
                "read_config",
                return_value={"config_path": "config.yaml"},
            ),
            mock.patch.object(lnxlink_main, "MonitorSuspend") as monitor_suspend,
            mock.patch.object(lnxlink_main, "GracefulKiller"),
            mock.patch.object(lnxlink_main, "LNXlink") as lnxlink_class,
        ):
            lnxlink_class.return_value.start.return_value = False

            with self.assertRaises(SystemExit) as raised:
                lnxlink_main.main()

        self.assertEqual(raised.exception.code, 1)
        monitor_suspend.return_value.stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
