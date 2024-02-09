"""Gets temperatures"""
import logging

import psutil

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Temperature"
        self.lnxlink = lnxlink
        self.temperatures = self._get_temperatures()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for key, value in self.temperatures.items():
            discovery_info[f"Temperature {value['name']}"] = {
                "type": "sensor",
                "entity_category": "diagnostic",
                "state_class": "measurement",
                "device_class": "temperature",
                "unit": "°C",
                "value_template": f"{{{{ value_json.get('{key}') }}}}",
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        temperatures = self._get_temperatures()
        temperatures = {key: value["value"] for key, value in temperatures.items()}
        return temperatures

    def _get_temperatures(self):
        """Get a list of all temperatures"""
        temperatures = {}
        for item, values in psutil.sensors_temperatures().items():
            for value in values:
                name = f"{item} {value.label}"
                key = name.replace(" ", "_").lower()
                temperatures[key] = {
                    "name": name,
                    "value": value.current,
                }
        return temperatures
