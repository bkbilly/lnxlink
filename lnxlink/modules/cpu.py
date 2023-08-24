"""Gets CPU usage information"""
import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "CPU Usage"

    def get_info(self):
        """Gather information from the system"""
        return psutil.cpu_percent()

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "CPU Usage": {
                "type": "sensor",
                "icon": "mdi:speedometer",
                "unit": "%",
                "state_class": "measurement",
            },
        }
