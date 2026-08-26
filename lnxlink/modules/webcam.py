"""Track webcam activity for privacy or presence automations"""
import base64
from threading import Lock, Thread, current_thread

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
        self._control_lock = Lock()
        self._reader_failed = False

    def _requirements(self):
        self.lib = {
            "cv2": import_install_package(
                "opencv-python-headless", ">=4.7.0.72", "cv2"
            ),
        }

    def get_camera_frame(self):
        """Convert camera feed to Base64 text"""
        capture = self.vid
        try:
            while capture is not None and self.vid is capture:
                ret, frame = capture.read()
                if not ret or frame is None:
                    self._reader_failed = True
                    break
                _, buffer = self.lib["cv2"].imencode(".jpg", frame)
                frame = base64.b64encode(buffer)
                self.lnxlink.run_module(f"{self.name}/Webcam feed", frame)
        except Exception:
            self._reader_failed = True
            raise
        finally:
            if capture is not None:
                try:
                    capture.release()
                except Exception:
                    pass
            if self.vid is capture:
                self.vid = None
            if self.read_thr is current_thread():
                self.read_thr = None

    def get_info(self):
        """Gather information from the system"""
        capture = self.vid
        reader = self.read_thr
        if capture is not None and reader is not None and reader.is_alive():
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
        with self._control_lock:
            if data.lower() == "off":
                if self.vid is not None:
                    if not self._reader_failed:
                        self.vid.release()
                    self.vid = None
                reader = self.read_thr
                if reader is not None:
                    reader.join()
                    if self.read_thr is reader:
                        self.read_thr = None
            elif data.lower() == "on":
                reader = self.read_thr
                if (
                    self.vid is not None
                    and reader is not None
                    and reader.is_alive()
                    and not self._reader_failed
                ):
                    return
                if self.vid is not None:
                    if not self._reader_failed:
                        self.vid.release()
                    self.vid = None
                reader = self.read_thr
                if reader is not None:
                    reader.join()
                    if self.read_thr is reader:
                        self.read_thr = None
                self.vid = self.lib["cv2"].VideoCapture(0)
                self._reader_failed = False
                self.read_thr = Thread(target=self.get_camera_frame, daemon=True)
                self.read_thr.start()
