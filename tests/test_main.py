"""Tests for the LNXlink command-line entry point."""
# pylint: disable=missing-function-docstring

import sys
import unittest
from contextlib import ExitStack
from unittest import mock

from lnxlink import __main__ as lnxlink_main


class MainTests(unittest.TestCase):
    """Verify process exit behavior."""

    def test_failed_mqtt_start_exits_nonzero(self):
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    sys, "argv", ["lnxlink", "--ignore-systemd", "-c", "config.yaml"]
                )
            )
            stack.enter_context(mock.patch.object(lnxlink_main, "_run_setup_wizard"))
            stack.enter_context(
                mock.patch.object(
                    lnxlink_main.config_setup,
                    "read_config",
                    return_value={"config_path": "config.yaml"},
                )
            )
            monitor_suspend = stack.enter_context(
                mock.patch.object(lnxlink_main, "MonitorSuspend")
            )
            stack.enter_context(mock.patch.object(lnxlink_main, "GracefulKiller"))
            lnxlink_class = stack.enter_context(
                mock.patch.object(lnxlink_main, "LNXlink")
            )
            lnxlink_class.return_value.start.return_value = False

            with self.assertRaises(SystemExit) as raised:
                lnxlink_main.main()

        self.assertEqual(raised.exception.code, 1)
        monitor_suspend.return_value.stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
