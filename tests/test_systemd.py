"""Regression tests for the systemd module."""
# pylint: disable=missing-function-docstring,protected-access

import unittest
from unittest import mock

from lnxlink.modules.systemd import Addon


class SystemdControlTests(unittest.TestCase):
    """Verify command topics map back to configured services."""

    def test_user_service_name_with_hyphen_matches_discovery_topic(self):
        addon = Addon.__new__(Addon)
        service = {"name": "llama-cpp.service", "user": True}
        addon.services = [service]
        addon._control = mock.Mock()

        addon.start_control(["systemd", "systemd_user_llama-cpp"], "ON")

        addon._control.assert_called_once_with(service, turn_on=True)


if __name__ == "__main__":
    unittest.main()
