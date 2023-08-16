"""Shows an image of the desktop as a camera entity"""
from mss import mss
import numpy as np
import cv2


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screenshot"
        self.sensor_type = "camera"
        self.sct = None

    def get_old_info(self):
        """Gather information from the system"""
        if self.sct is not None:
            sct_img = self.sct.grab(self.sct.monitors[1])
            frame = np.array(sct_img)
            _, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            return frame
        return None

    def get_info(self):
        """Gather information from the system"""
        if self.sct is not None:
            return True
        return False

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Screenshot": {
                "type": "switch",
                "icon": "mdi:monitor-screenshot",
                "entity_category": "config",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.sct = None
        elif data.lower() == "on":
            self.sct = mss()
