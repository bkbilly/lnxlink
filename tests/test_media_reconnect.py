"""Tests for republishing MQTT media-player state after connection loss."""
# pylint: disable=missing-function-docstring

from types import SimpleNamespace
from unittest import mock

from lnxlink.__main__ import LNXlink
from lnxlink.modules.media import Addon


def _media_addon():
    lnxlink = SimpleNamespace(run_module=mock.Mock())
    addon = Addon.__new__(Addon)
    addon.name = "Media Info"
    addon.lnxlink = lnxlink
    addon.playmedia_thread = None
    addon.process = None
    addon.players = []
    addon.prev_info = {}
    addon.audio_system = None
    addon.mediavolume = "OFF"
    return addon, lnxlink


def test_unchanged_media_state_is_queued_once_until_cache_invalidation():
    addon, lnxlink = _media_addon()

    addon.get_info()
    addon.get_info()
    addon.invalidate_cache()
    addon.get_info()

    state_calls = [
        call
        for call in lnxlink.run_module.call_args_list
        if call.args[0] == "Media Info/state"
    ]
    assert state_calls == [
        mock.call("Media Info/state", "off"),
        mock.call("Media Info/state", "off"),
    ]


def _lnxlink_with_cached_state():
    lnxlink = LNXlink.__new__(LNXlink)
    lnxlink.prev_publish = {"lnxlink/test/monitor_controls/media_info/state": "off"}
    lnxlink.prev_publish_transport = {
        "lnxlink/test/monitor_controls/media_info/state": object()
    }
    addon = mock.Mock()
    lnxlink.addons = {"media": addon}
    lnxlink.kill = True
    lnxlink.mqtt = mock.Mock()
    lnxlink.mqtt.get_rcode_name.return_value = "Success"
    return lnxlink


def test_mqtt_reconnect_makes_unchanged_state_publishable_again():
    lnxlink = _lnxlink_with_cached_state()
    lnxlink.config = {
        "pref_topic": "lnxlink/test",
        "mqtt": {"discovery": {"enabled": False}},
    }
    client = mock.Mock()

    lnxlink.on_connect(client, None, None, 0)

    assert not lnxlink.prev_publish
    assert not lnxlink.prev_publish_transport
    lnxlink.addons["media"].invalidate_cache.assert_called_once_with()
    assert lnxlink.kill is False


def test_resume_makes_unchanged_state_publishable_again():
    lnxlink = _lnxlink_with_cached_state()
    lnxlink.config = {"mqtt": {"clear_on_off": False}}
    lnxlink.mqtt.client = object()

    lnxlink.temp_connection_callback(False)

    assert not lnxlink.prev_publish
    assert not lnxlink.prev_publish_transport
    lnxlink.addons["media"].invalidate_cache.assert_called_once_with()
    assert lnxlink.kill is False
