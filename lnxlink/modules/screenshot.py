from mss import mss
import numpy as np
import cv2


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Screenshot'
        self.sensor_type = 'camera'
        self.sct = None

    def getInfo(self):
        if self.sct is not None:
            sct_img = self.sct.grab(self.sct.monitors[1])
            frame = np.array(sct_img)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            return frame
        return None

    def getControlInfo(self):
        if self.sct is not None:
            return True
        return False

    def exposedControls(self):
        return {
            "Screenshot": {
                "type": "switch",
                "icon": "mdi:monitor-screenshot",
                "entity_category": "config",
            }
        }

    def startControl(self, topic, data):
        if data.lower() == 'off':
            self.sct = None
        elif data.lower() == 'on':
            self.sct = mss()
