"""Gets Inference Time information"""
import time


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Inference Time"
        self.prev_time = time.time()

    def get_info(self):
        """Gather information from the system"""
        inf_time = time.time() - self.prev_time
        self.prev_time = time.time()
        return round(inf_time, 2)

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Inference Time": {
                "type": "sensor",
                "icon": "mdi:timelapse",
                "unit": "s",
                "entity_category": "diagnostic",
                "state_class": "measurement",
            },
        }
