"""Shows an image from the webcamera"""
import cv2


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Webcam"
        self.sensor_type = "camera"
        self.vid = None

    def get_old_info(self):
        """Gather information from the system"""
        if self.vid is not None:
            _, frame = self.vid.read()
            _, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
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
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            self.vid.release()
            self.vid = None
        elif data.lower() == "on":
            self.vid = cv2.VideoCapture(0)
