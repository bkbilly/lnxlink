"""Shows an image from the webcamera"""
import cv2
import base64


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Webcam"
        self.vid = None

    def get_camera_frame(self):
        """Convert camera feed to Base64 text"""
        if self.vid is not None:
            _, frame = self.vid.read()
            _, buffer = cv2.imencode(".jpg", frame)
            frame = base64.b64encode(buffer)
            return frame
        return None

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
                "method": self.get_camera_frame,
                "encoding": "b64",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.vid.release()
            self.vid = None
        elif data.lower() == "on":
            self.vid = cv2.VideoCapture(0)
