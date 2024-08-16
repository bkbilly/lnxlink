"""Gets WiFi information"""
import os
import re
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "WiFi"
        if not os.path.exists("/proc/net/wireless"):
            raise SystemError("No WiFi found.")
        self.run_method = self.command_get_info
        if which("iwgetid") is None:
            self._requirements()
            self.lib["dbus_nd"].DBUSNetworkDevices().get_network_devices()
            self.run_method = self.dbus_get_info

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
        return self.run_method()

    def command_get_info(self):
        """Get WiFi data from system commands"""
        logger.debug("Using iwgetid command")
        interface = ""
        ssid = ""
        mac = ""
        signal = None
        if os.path.exists("/proc/net/wireless"):
            wireless_info, _, _ = syscommand("cat /proc/net/wireless")
            match = re.findall(r"\s+(\S+):\s\S+\s+\S+\s+(\S+)", wireless_info)
            if match:
                interface = match[0][0]
                rssi = float(match[0][1])
                signal = min(2 * (100 + rssi), 100)
                ssid, _, _ = syscommand("iwgetid -r")
                mac, _, _ = syscommand("iwgetid -ra")

        return {
            "signal": signal,
            "attributes": {
                "Interface": interface,
                "SSID": ssid,
                "MAC": mac,
            },
        }

    def dbus_get_info(self):
        """Get WiFi data from DBUS"""
        logger.debug("Using DBUS")
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
