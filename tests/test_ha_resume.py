"""Tests for MQTT transport state across suspend and resume."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from types import SimpleNamespace
from unittest import mock

from lnxlink.__main__ import LNXlink


def _lnxlink_with_client(client):
    lnxlink = LNXlink.__new__(LNXlink)
    lnxlink.kill = False
    lnxlink.config = {"mqtt": {"clear_on_off": False}}
    lnxlink.prev_publish = {}
    lnxlink.mqtt = mock.Mock()
    lnxlink.mqtt.client = client
    return lnxlink


def test_resume_restores_home_assistant_publish_timeout_state():
    client = SimpleNamespace(is_disconnecting=False)
    lnxlink = _lnxlink_with_client(client)

    lnxlink.temp_connection_callback(True)
    assert lnxlink.mqtt.is_disconnecting is True
    assert client.is_disconnecting is True

    lnxlink.temp_connection_callback(False)

    assert lnxlink.kill is False
    assert lnxlink.mqtt.is_disconnecting is False
    assert client.is_disconnecting is False
    assert lnxlink.mqtt.send_lwt.call_args_list == [mock.call("OFF"), mock.call("ON")]


def test_resume_does_not_add_transport_state_to_direct_mqtt_client():
    class DirectClient:
        pass

    client = DirectClient()
    lnxlink = _lnxlink_with_client(client)
    lnxlink.kill = True
    lnxlink.mqtt.is_disconnecting = True

    lnxlink.temp_connection_callback(False)

    assert lnxlink.mqtt.is_disconnecting is False
    assert not hasattr(client, "is_disconnecting")
    lnxlink.mqtt.send_lwt.assert_called_once_with("ON")
