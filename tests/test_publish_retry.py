"""Tests for retrying monitor values after MQTT publish failures."""
# pylint: disable=missing-function-docstring

from types import SimpleNamespace
from unittest import mock

import paho.mqtt.client as mqtt

from lnxlink.__main__ import LNXlink
from lnxlink.mqtt import MQTT, DirectMQTTClient, HomeAssistantApiClient


def _lnxlink_with_publish_result(rc):
    lnxlink = LNXlink.__new__(LNXlink)
    lnxlink.config = {
        "pref_topic": "lnxlink/test-host",
        "update_on_change": True,
    }
    lnxlink.prev_publish = {}
    lnxlink.prev_publish_transport = {}
    lnxlink.monitor_topics = {}
    lnxlink.saved_publish = {}
    lnxlink.update_change_interval = 900
    lnxlink.mqtt = mock.Mock()
    lnxlink.mqtt.publish.return_value = SimpleNamespace(rc=rc)
    lnxlink.mqtt.publish_accepted.side_effect = lambda result: result.rc == 0
    lnxlink.mqtt.delivery_token = object()
    return lnxlink


def test_failed_publish_retries_unchanged_value():
    lnxlink = _lnxlink_with_publish_result(rc=1)

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.publish_monitor_data("CPU", 42)

    assert lnxlink.mqtt.publish.call_count == 2
    assert "lnxlink/test-host/monitor_controls/cpu" not in lnxlink.prev_publish
    assert lnxlink.saved_publish["cpu"] == 42


def test_successful_publish_deduplicates_unchanged_value():
    lnxlink = _lnxlink_with_publish_result(rc=0)

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.publish_monitor_data("CPU", 42)

    lnxlink.mqtt.publish.assert_called_once_with(
        "lnxlink/test-host/monitor_controls/cpu", 42, True
    )
    assert lnxlink.prev_publish["lnxlink/test-host/monitor_controls/cpu"] == 42


def test_failed_forced_publish_invalidates_previous_success():
    lnxlink = _lnxlink_with_publish_result(rc=0)
    topic = "lnxlink/test-host/monitor_controls/cpu"

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.mqtt.publish.return_value.rc = 1
    lnxlink.publish_monitor_data("CPU", 42, force_publish=True)
    lnxlink.publish_monitor_data("CPU", 42)

    assert lnxlink.mqtt.publish.call_count == 3
    assert topic not in lnxlink.prev_publish
    assert lnxlink.monitor_topics[topic] == 42


def test_clear_on_off_keeps_last_accepted_topic_after_failed_update():
    lnxlink = _lnxlink_with_publish_result(rc=0)
    topic = "lnxlink/test-host/monitor_controls/cpu"
    lnxlink.config["mqtt"] = {"clear_on_off": True}
    lnxlink.mqtt.client = object()
    lnxlink.mqtt.send_lwt = mock.Mock()

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.mqtt.publish.return_value.rc = 1
    lnxlink.publish_monitor_data("CPU", 43)
    lnxlink.mqtt.publish.reset_mock()

    lnxlink.temp_connection_callback(True)

    lnxlink.mqtt.publish.assert_called_once_with(topic, None)


def test_clear_on_off_tracks_a_failed_first_attempt():
    lnxlink = _lnxlink_with_publish_result(rc=1)
    topic = "lnxlink/test-host/monitor_controls/cpu"
    lnxlink.config["mqtt"] = {"clear_on_off": True}
    lnxlink.mqtt.client = object()
    lnxlink.mqtt.send_lwt = mock.Mock()

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.mqtt.publish.reset_mock()

    lnxlink.temp_connection_callback(True)

    lnxlink.mqtt.publish.assert_called_once_with(topic, None)


def test_direct_qos_publish_queued_during_disconnect_is_not_retried():
    lnxlink = _lnxlink_with_publish_result(rc=mqtt.MQTT_ERR_NO_CONN)
    transport = MQTT.__new__(MQTT)
    transport.config = {"mqtt": {"lwt": {"qos": 1}}}
    transport.transport = "mqtt"
    transport.client = DirectMQTTClient.__new__(DirectMQTTClient)
    lnxlink.mqtt.publish_accepted.side_effect = transport.publish_accepted

    lnxlink.publish_monitor_data("CPU", 42)
    lnxlink.publish_monitor_data("CPU", 42)

    lnxlink.mqtt.publish.assert_called_once()


def test_auto_transport_retries_publish_queued_on_abandoned_direct_client():
    transport = MQTT.__new__(MQTT)
    transport.config = {"mqtt": {"lwt": {"qos": 1}}}
    transport.transport = "auto"
    transport.client = DirectMQTTClient.__new__(DirectMQTTClient)

    assert not transport.publish_accepted(SimpleNamespace(rc=mqtt.MQTT_ERR_NO_CONN))


def test_auto_failover_invalidates_successfully_queued_direct_publishes():
    lnxlink = _lnxlink_with_publish_result(rc=mqtt.MQTT_ERR_SUCCESS)
    topic = "lnxlink/test-host/monitor_controls/cpu"
    lnxlink.publish_monitor_data("CPU", 42)
    assert lnxlink.prev_publish[topic] == 42

    transport = MQTT.__new__(MQTT)
    transport.config = {"mqtt": {"lwt": {"qos": 1}}}
    transport.transport = "auto"
    transport.client = mock.create_autospec(DirectMQTTClient, instance=True)
    transport.client.connect.return_value = True
    assert transport.setup_mqtt(
        mock.Mock(), mock.Mock(), lnxlink.invalidate_publish_cache
    )

    with mock.patch.object(
        HomeAssistantApiClient, "connect", autospec=True, return_value=True
    ):
        assert transport.switch_to_homeassistant_api()

    assert topic not in lnxlink.prev_publish
    lnxlink.publish_monitor_data("CPU", 42)
    assert lnxlink.mqtt.publish.call_count == 2


def test_stale_direct_publish_cannot_restore_cache_after_failover():
    lnxlink = _lnxlink_with_publish_result(rc=mqtt.MQTT_ERR_SUCCESS)
    old_transport = lnxlink.mqtt.delivery_token
    new_transport = object()
    attempts = 0

    def finish_stale_publish(*_args):
        nonlocal attempts
        if attempts == 0:
            lnxlink.invalidate_publish_cache()
            lnxlink.mqtt.delivery_token = new_transport
        attempts += 1
        return SimpleNamespace(rc=mqtt.MQTT_ERR_SUCCESS)

    lnxlink.mqtt.publish.side_effect = finish_stale_publish

    lnxlink.publish_monitor_data("CPU", 42)
    assert (
        lnxlink.prev_publish_transport["lnxlink/test-host/monitor_controls/cpu"]
        is old_transport
    )

    lnxlink.publish_monitor_data("CPU", 42)

    assert lnxlink.mqtt.publish.call_count == 2
    assert (
        lnxlink.prev_publish_transport["lnxlink/test-host/monitor_controls/cpu"]
        is new_transport
    )


def test_non_retained_publish_is_not_registered_for_shutdown_cleanup():
    lnxlink = _lnxlink_with_publish_result(rc=0)
    topic = "lnxlink/test-host/monitor_controls/ir_remote/event"

    lnxlink.publish_monitor_data("IR Remote/Event", {"code": 42}, retain=False)

    assert topic not in lnxlink.monitor_topics
