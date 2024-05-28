"""Shows an image from the webcamera"""
import base64
from threading import Thread
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.lnxlink = lnxlink
        self.name = "Webcam"
        self.vid = None
        self._requirements()
        self.read_thr = None

    def _requirements(self):
        self.lib = {
            "cv2": import_install_package("opencv-python", ">=4.7.0.68", "cv2"),
        }

    def get_camera_frame(self):
        """Convert camera feed to Base64 text"""
        if self.vid is not None:
            while True:
                _, frame = self.vid.read()
                _, buffer = self.lib["cv2"].imencode(".jpg", frame)
                frame = base64.b64encode(buffer)
                self.lnxlink.run_module(f"{self.name}/Webcam feed", frame)

    def get_info(self):
        """Gather information from the system"""
        if self.vid is not None:
            return True
        return False

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Webcam": {
                "type": "switch",
                "icon": "mdi:webcam",
                "entity_category": "config",
            },
            "Webcam feed": {
                "type": "camera",
                "encoding": "b64",
                "subtopic": True,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.vid.release()
            self.vid = None
            if self.read_thr is not None:
                self.read_thr.join()
                self.read_thr = None
        elif data.lower() == "on":
            self.vid = self.lib["cv2"].VideoCapture(0)
            if self.read_thr is None:
                self.read_thr = Thread(target=self.get_camera_frame, daemon=True)
                self.read_thr.start()
