"""Gets the battery information of connected devices"""
import jc
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Battery"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Battery": {
                "type": "sensor",
                "icon": "mdi:battery",
                "unit": "%",
                "device_class": "battery",
                "value_template": "{{ value_json.status }}",
                "enabled": False,
            },
        }

    def get_info(self):
        """Gather information from the system"""
        stdout, _, _ = syscommand("upower --dump")
        upower_json = jc.parse("upower", stdout)

        devices = {"status": None}
        for device in upower_json:
            if "detail" in device:
                if "percentage" in device["detail"]:
                    name = "".join(
                        [
                            device.get("vendor", ""),
                            device.get("model", ""),
                        ]
                    ).strip()
                    if name != "":
                        devices[name] = device["detail"]["percentage"]
                        if devices["status"] is None:
                            devices["status"] = device["detail"]["percentage"]
        return devices
