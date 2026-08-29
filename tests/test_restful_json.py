"""Tests for RESTful JSON response types and monitor snapshots."""
# pylint: disable=missing-class-docstring,missing-function-docstring,protected-access

import json
import types

import flask
import flask.views as flask_views

from lnxlink.__main__ import LNXlink
from lnxlink.modules import restful


class CaptureFlask(flask.Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._captured = True


class DummyAddon:
    def __init__(self, value):
        self.value = value

    def start_control(self, topic, message):
        return self.value


class FailingAddon:
    def start_control(self, topic, message):
        raise RuntimeError("control failed")


class ReadOnlyAddon:
    pass


class FakeLnxlink:
    def __init__(self):
        self.saved_publish = {
            "interfaces": {"eth0": {"ipv4": "1.2.3.4"}},
            "cpu": 1,
            "image": b"YWJj",
            "clipboard": "true",
        }
        self.addons = {
            "dummy": DummyAddon({"ok": True}),
            "failing": FailingAddon(),
            "readonly": ReadOnlyAddon(),
        }
        self.config = {"settings": {"restful": {"port": 8112}}}

    def add_settings(self, *_args, **_kwargs):
        return None


def fake_import(name, *_args, **_kwargs):
    if name == "waitress":
        return types.SimpleNamespace(serve=lambda *args, **kwargs: None)
    module_name = _args[1] if len(_args) > 1 else ""
    if module_name == "flask.views":
        return types.SimpleNamespace(views=flask_views)
    return flask


def fake_publish_lnxlink():
    """Build the minimum current publish state without starting LNXlink."""
    lnxlink = LNXlink.__new__(LNXlink)
    lnxlink.config = {"pref_topic": "lnxlink/host", "update_on_change": False}
    lnxlink.prev_publish = {}
    lnxlink.prev_publish_transport = {}
    lnxlink.monitor_topics = {}
    lnxlink.saved_publish = {}
    lnxlink.update_change_interval = 900
    lnxlink.mqtt = types.SimpleNamespace(
        delivery_token=object(),
        publish=lambda *_args, **_kwargs: types.SimpleNamespace(rc=0),
        publish_accepted=lambda info: info.rc == 0,
    )
    return lnxlink


def test_restful_info_returns_json_for_dict_and_scalar():
    captured = {}
    original_flask = flask.Flask
    original_import = restful.import_install_package
    original_serve = restful.Addon._serve

    class TestFlask(CaptureFlask):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            captured["app"] = self

    try:
        flask.Flask = TestFlask
        restful.import_install_package = fake_import
        restful.Addon._serve = lambda *_args: None
        restful.Addon(FakeLnxlink())
        client = captured["app"].test_client()

        dict_response = client.get("/info/interfaces")
        scalar_response = client.get("/info/cpu")
        bytes_response = client.get("/info/image")
        string_response = client.get("/info/clipboard")

        assert dict_response.status_code == 200
        assert dict_response.mimetype == "application/json"
        assert json.loads(dict_response.data) == {"eth0": {"ipv4": "1.2.3.4"}}

        assert scalar_response.status_code == 200
        assert scalar_response.mimetype == "application/json"
        assert json.loads(scalar_response.data) == 1

        assert bytes_response.status_code == 200
        assert bytes_response.mimetype == "application/json"
        assert json.loads(bytes_response.data) == "YWJj"
        assert json.loads(string_response.data) == "true"
    finally:
        flask.Flask = original_flask
        restful.import_install_package = original_import
        restful.Addon._serve = original_serve


def test_restful_control_list_and_result_are_json():
    captured = {}
    original_flask = flask.Flask
    original_import = restful.import_install_package
    original_serve = restful.Addon._serve

    class TestFlask(CaptureFlask):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            captured["app"] = self

    try:
        flask.Flask = TestFlask
        restful.import_install_package = fake_import
        restful.Addon._serve = lambda *_args: None
        restful.Addon(FakeLnxlink())
        client = captured["app"].test_client()

        control_list = client.get("/control")
        control_result = client.post(
            "/control/dummy",
            data={"topic": "power", "message": "on"},
        )

        assert json.loads(control_list.data) == ["dummy", "failing"]
        assert json.loads(control_result.data) == {"ok": True}
    finally:
        flask.Flask = original_flask
        restful.import_install_package = original_import
        restful.Addon._serve = original_serve


def test_restful_control_failures_are_json():
    captured = {}
    original_flask = flask.Flask
    original_import = restful.import_install_package
    original_serve = restful.Addon._serve

    class TestFlask(CaptureFlask):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            captured["app"] = self

    try:
        flask.Flask = TestFlask
        restful.import_install_package = fake_import
        restful.Addon._serve = lambda *_args: None
        restful.Addon(FakeLnxlink())
        client = captured["app"].test_client()

        responses = {
            client.post("/control/missing"): "Module not found",
            client.post("/control/readonly"): "No control support available",
            client.post("/control/failing"): "Error: control failed",
        }

        for response, expected in responses.items():
            assert response.mimetype == "application/json"
            assert json.loads(response.data) == expected
    finally:
        flask.Flask = original_flask
        restful.import_install_package = original_import
        restful.Addon._serve = original_serve


def test_saved_monitor_data_is_a_published_snapshot():
    """Later module mutations must not alter the REST snapshot."""
    lnxlink = fake_publish_lnxlink()
    value = {"state": "before"}

    lnxlink.publish_monitor_data("Mutable", value)
    value["state"] = "after"

    assert lnxlink.saved_publish["mutable"] == {"state": "before"}


def test_saved_boolean_remains_native_json_data():
    lnxlink = fake_publish_lnxlink()

    lnxlink.publish_monitor_data("Webcam", True)

    assert lnxlink.saved_publish["webcam"] is True
