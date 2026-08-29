"""Tests for publishing Home Assistant discovery configurations."""
# pylint: disable=missing-function-docstring

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from lnxlink.__main__ import LNXlink
from lnxlink.mqtt import MQTT


class MQTTDiscoveryTest(unittest.TestCase):
    """Verify that only transport-accepted discovery publishes are returned."""

    def setUp(self):
        self.mqtt = MQTT.__new__(MQTT)
        self.mqtt.config = {
            "mqtt": {
                "clientId": "host",
                "discovery": {"prefix": "homeassistant"},
            },
            "pref_topic": "lnxlink/host",
            "version": "test",
        }
        self.addon = SimpleNamespace(name="CPU")

    def test_failed_discovery_publish_raises(self):
        self.mqtt.publish = lambda *args, **kwargs: SimpleNamespace(rc=1)

        with self.assertRaisesRegex(RuntimeError, "MQTT RC 1"):
            self.mqtt.setup_discovery_entities(
                self.addon, "cpu", "CPU Usage", {"type": "sensor"}
            )

    def test_successful_discovery_publish_returns_topic(self):
        self.mqtt.publish = lambda *args, **kwargs: SimpleNamespace(rc=0)

        topic = self.mqtt.setup_discovery_entities(
            self.addon, "cpu", "CPU Usage", {"type": "sensor"}
        )

        self.assertEqual(
            topic,
            "homeassistant/sensor/lnxlink/host_cpu_usage/config",
        )

    def test_partial_batch_registers_success_without_pruning(self):
        lnxlink = LNXlink.__new__(LNXlink)
        addon = SimpleNamespace(
            prune_stale_discovery=True,
            exposed_controls=lambda: {
                "First": {"type": "sensor"},
                "Second": {"type": "sensor"},
            },
        )
        lnxlink.addons = {"cpu": addon}
        lnxlink.excluded_modules = set()
        lnxlink.mqtt = Mock()
        lnxlink.mqtt.setup_discovery_entities.side_effect = [
            "homeassistant/sensor/lnxlink/first/config",
            RuntimeError("MQTT RC 1"),
        ]
        lnxlink.discovery_registry = Mock()

        lnxlink.setup_discovery()

        lnxlink.discovery_registry.sync.assert_called_once_with(
            "cpu",
            {"homeassistant/sensor/lnxlink/first/config"},
            False,
            lnxlink.mqtt,
        )


if __name__ == "__main__":
    unittest.main()
