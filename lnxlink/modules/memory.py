"""Gets memory usage information"""
import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Memory Usage"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Memory Usage": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "%",
                "state_class": "measurement",
                "value_template": "{{ value_json.percent }}",
            },
            "Memory Used": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.used }}",
                "enabled": False,
            },
            "Memory Available": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.available }}",
                "enabled": False,
            },
        }

    def get_info(self):
        """Gather information from the system"""
        vmem = psutil.virtual_memory()
        return {
            "percent": round(vmem.percent, 0),
            "used": round(vmem.used / 1024**2, 0),
            "available": round(vmem.available / 1024**2, 0),
        }
