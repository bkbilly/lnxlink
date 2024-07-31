"""Gets WiFi information"""
import os
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "WiFi"
        if not os.path.exists("/proc/net/wireless"):
            raise SystemError("No WiFi found.")
        self._requirements()

    def _requirements(self):
        self.lib = {
            "dbus_nd": import_install_package(
                "dbus-networkdevices", ">=2024.0.7", "dbus_networkdevices"
            ),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "WiFi": {
                "type": "sensor",
                "icon": "mdi:wifi",
                "unit": "%",
                "entity_category": "diagnostic",
                "state_class": "measurement",
                "value_template": "{{ value_json.signal }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        interface = ""
        ssid = ""
        mac = ""
        signal = None
        devices = self.lib["dbus_nd"].DBUSNetworkDevices().get_network_devices()
        for device in devices:
            if "wifi" in device:
                interface = device["interface"]
                signal = device["wifi"]["strength"]
                ssid = device["wifi"]["ssid"]
                mac = device["wifi"]["mac"]

        return {
            "signal": signal,
            "attributes": {
                "Interface": interface,
                "SSID": ssid,
                "MAC": mac,
            },
        }
