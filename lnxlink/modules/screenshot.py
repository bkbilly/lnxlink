"""Shows an image of the desktop as a camera entity"""
import base64
from threading import Thread
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.lnxlink = lnxlink
        self.name = "Screenshot"
        self.run = False
        self._requirements()
        self.read_thr = None

    def _requirements(self):
        self.lib = {
            "cv2": import_install_package("opencv-python", ">=4.7.0.68", "cv2"),
            "mss": import_install_package("mss", ">=7.0.1"),
            "np": import_install_package("numpy", "==1.26.4"),
        }

    def get_camera_frame(self):
        """Convert screen image to Base64 text"""
        if self.run:
            with self.lib["mss"].mss() as sct:
                while True:
                    if not self.run:
                        break
                    sct_img = sct.grab(sct.monitors[1])
                    frame = self.lib["np"].array(sct_img)
                    _, buffer = self.lib["cv2"].imencode(".jpg", frame)
                    frame = base64.b64encode(buffer)
                    self.lnxlink.run_module(f"{self.name}/Screenshot feed", frame)

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
                "encoding": "b64",
                "subtopic": True,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.run = False
            if self.read_thr is not None:
                self.read_thr.join()
                self.read_thr = None
        elif data.lower() == "on":
            self.run = True
            if self.read_thr is None:
                self.read_thr = Thread(target=self.get_camera_frame, daemon=True)
                self.read_thr.start()
