"""Tests for Home Assistant discovery registry accounting."""
# pylint: disable=missing-function-docstring

import unittest
from types import SimpleNamespace

from lnxlink.discovery_registry import DiscoveryRegistry


class FakeMQTT:
    """Return configured MQTT result codes and retain published calls."""

    def __init__(self, return_codes=()):
        self.return_codes = iter(return_codes)
        self.calls = []

    def publish(self, topic, payload, retain=True):
        self.calls.append((topic, payload, retain))
        return SimpleNamespace(rc=next(self.return_codes, 0))


class DiscoveryRegistryTest(unittest.TestCase):
    """Verify that registry state follows accepted MQTT publishes."""

    def setUp(self):
        self.registry = DiscoveryRegistry({})
        self.registry.file_enabled = False

    def test_failed_stale_clear_remains_retryable(self):
        topic = "homeassistant/sensor/lnxlink/old/config"
        self.registry.registry = {
            "disk_usage": {"topics": [topic], "stale_topics": [topic]}
        }

        self.registry.sync("disk_usage", set(), True, FakeMQTT([1]))

        self.assertEqual(
            self.registry.registry["disk_usage"],
            {"topics": [topic], "stale_topics": [topic]},
        )

        self.registry.sync("disk_usage", set(), True, FakeMQTT([0]))

        self.assertEqual(
            self.registry.registry["disk_usage"],
            {"topics": [], "stale_topics": []},
        )

    def test_excluded_cleanup_keeps_only_failed_topics(self):
        first = "homeassistant/sensor/lnxlink/first/config"
        second = "homeassistant/sensor/lnxlink/second/config"
        self.registry.registry = {
            "battery": {
                "topics": [first, second],
                "stale_topics": [second],
            }
        }

        self.registry.clear_excluded({"battery"}, FakeMQTT([0, 1]))

        self.assertEqual(
            self.registry.registry["battery"],
            {"topics": [second], "stale_topics": [second]},
        )

        self.registry.clear_excluded({"battery"}, FakeMQTT([0]))

        self.assertNotIn("battery", self.registry.registry)

    def test_non_pruning_module_keeps_topics_for_later_exclusion(self):
        first = "homeassistant/sensor/lnxlink/first/config"
        second = "homeassistant/sensor/lnxlink/second/config"
        mqtt = FakeMQTT()

        self.registry.sync("battery", {first}, False, mqtt)
        self.registry.sync("battery", {second}, False, mqtt)

        self.assertEqual(
            self.registry.registry["battery"],
            {"topics": [first, second], "stale_topics": []},
        )

        self.registry.clear_excluded({"battery"}, mqtt)

        self.assertEqual(
            mqtt.calls,
            [(first, "", True), (second, "", True)],
        )
        self.assertNotIn("battery", self.registry.registry)

    def test_successful_pruning_keeps_one_run_grace_period(self):
        topic = "homeassistant/sensor/lnxlink/old/config"
        mqtt = FakeMQTT()

        self.registry.sync("disk_usage", {topic}, True, mqtt)
        self.registry.sync("disk_usage", set(), True, mqtt)

        self.assertEqual(mqtt.calls, [])
        self.assertEqual(
            self.registry.registry["disk_usage"],
            {"topics": [topic], "stale_topics": [topic]},
        )

        self.registry.sync("disk_usage", set(), True, mqtt)

        self.assertEqual(mqtt.calls, [(topic, "", True)])
        self.assertEqual(
            self.registry.registry["disk_usage"],
            {"topics": [], "stale_topics": []},
        )


if __name__ == "__main__":
    unittest.main()
