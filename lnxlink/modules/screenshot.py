"""Shows an image of the desktop as a camera entity"""
import base64
from .scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screenshot"
        self.run = False
        self._requirements()

    def _requirements(self):
        self.lib = {
            "cv2": import_install_package("opencv-python", ">=4.7.0.68", "cv2"),
            "mss": import_install_package("mss", ">=7.0.1"),
            "np": import_install_package("numpy", ">=1.24.0"),
        }

    def get_camera_frame(self):
        """Convert screen image to Base64 text"""
        if self.run:
            with self.lib["mss"].mss() as sct:
                sct_img = sct.grab(sct.monitors[1])
                frame = self.lib["np"].array(sct_img)
            _, buffer = self.lib["cv2"].imencode(".jpg", frame)
            frame = base64.b64encode(buffer)
            return frame
        return None

    def get_info(self):
        """Gather information from the system"""
        return self.run

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Screenshot": {
                "type": "switch",
                "icon": "mdi:monitor-screenshot",
                "entity_category": "config",
            },
            "Screenshot feed": {
                "type": "camera",
                "method": self.get_camera_frame,
                "encoding": "b64",
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.run = False
        elif data.lower() == "on":
            self.run = True
