import cv2


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Webcam'
        self.sensor_type = 'camera'
        self.vid = None

    def getInfo(self):
        if self.vid is not None:
            ret, frame = self.vid.read()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            return frame
        return None

    def getControlInfo(self):
        if self.vid is not None:
            return True
        return False

    def exposedControls(self):
        return {
            "Webcam": {
                "type": "switch",
                "icon": "mdi:webcam",
                "entity_category": "config",
            }
        }

    def startControl(self, topic, data):
        if data.lower() == 'off':
            self.vid.release()
            self.vid = None
        elif data.lower() == 'on':
            self.vid = cv2.VideoCapture(0)
