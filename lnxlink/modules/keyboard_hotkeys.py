"""Assign hotkeys to run commands"""
import logging
from datetime import datetime
from lnxlink.modules.scripts.helpers import import_install_package


logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Keyboard Hotkeys"
        self.lnxlink = lnxlink
        self.started = False
        self.lib = {}
        self._requirements()
        self.lnxlink.add_settings("hotkeys", [])
        if len(self.lnxlink.config["settings"]["hotkeys"] == 0):
            logger.warning("No hotkeys configured for Keyboard Hotkeys module")
            logger.warning("  Please add hotkeys in the settings like so:")
            logger.warning("  - key: <ctrl>+<alt>+a")

    def exposed_controls(self):
        """Exposes to home assistant"""
        use_sensor = any(
            "type" not in v for v in self.lnxlink.config["settings"]["hotkeys"]
        )
        discovery_info = {}
        if use_sensor:
            discovery_info = {
                "Keyboard Hotkey": {
                    "type": "sensor",
                    "device_class": "timestamp",
                    "value_template": "{{ value_json.timevalue }}",
                    "attributes_template": "{{ value_json.attributes | tojson }}",
                },
            }
        return discovery_info

    def _requirements(self):
        self.lib = {
            "xlib_hotkeys": import_install_package(
                "xlib-hotkeys", ">=2024.3.0", "xlib_hotkeys"
            ),
        }

    def get_info(self):
        """Gather information from the system"""
        if not self.started and self.lnxlink.display is not None:
            hm = self.lib["xlib_hotkeys"].HotKeysManager(self.lnxlink.display)
            actions = self.lnxlink.config["settings"]["hotkeys"]
            for action in actions:
                action_key = action.get("key")
                hm.hotkeys[action_key] = lambda action=action: self._activate(action)
            hm.start()
            self.started = True

    def _activate(self, act):
        action = act.copy()
        key = action.pop("key")
        data_send = {
            "timevalue": datetime.now().astimezone().isoformat(),
            "attributes": {
                "key": key,
            },
        }
        self.lnxlink.run_module(self.name, data_send)
