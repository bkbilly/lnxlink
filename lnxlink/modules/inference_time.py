"""Gets Inference Time information"""


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Inference Time"
        self.lnxlink = lnxlink

    def get_info(self):
        """Gather information from the system"""
        return {
            "modules": self.lnxlink.inference_times,
            "sum": round(sum(self.lnxlink.inference_times.values()), 2),
            "max": max(
                self.lnxlink.inference_times,
                key=self.lnxlink.inference_times.get,
                default=None,
            ),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Inference Time": {
                "type": "sensor",
                "icon": "mdi:timelapse",
                "unit": "s",
                "entity_category": "diagnostic",
                "state_class": "measurement",
                "value_template": "{{ value_json.sum }}",
                "attributes_template": "{{ value_json.modules | tojson }}",
            },
            "Inference Time Highest": {
                "type": "sensor",
                "icon": "mdi:timelapse",
                "entity_category": "diagnostic",
                "value_template": "{{ value_json.max }}",
                "enabled": False,
            },
        }
