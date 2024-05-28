"""Checks if the microphone is used"""
from importlib import import_module
from threading import Thread
import logging
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Speech Recognition"
        self.run = False
        self.speech = ""
        try:
            import_module("pyaudio")
        except Exception as err:
            raise SystemError(
                "System package 'python3-pyaudio' or 'portaudio19-dev' not installed"
            ) from err
        self._requirements()

    def _requirements(self):
        self.lib = {
            "alsaaudio": import_install_package("pyalsaaudio", ">=0.9.2", "alsaaudio"),
            "sr": import_install_package(
                "SpeechRecognition", ">=3.10.0", "speech_recognition"
            ),
        }

    def get_info(self):
        """Gather information from the system"""
        status = "OFF"
        if self.run:
            status = "ON"
        return {
            "status": status,
            "speech": self.speech,
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Speech Recognition": {
                "type": "binary_sensor",
                "icon": "mdi:account-tie-voice",
                "value_template": "{{ value_json.status }}",
            },
            "Start Speech Recognition": {
                "type": "button",
                "icon": "mdi:account-tie-voice",
            },
        }

    def start_recognition(self):
        """Start a voice recognition"""
        try:
            recognizer = self.lib["sr"].Recognizer()
            with self.lib["sr"].Microphone() as source:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                self.speech = recognizer.recognize_google(audio)
        except Exception as err:
            logger.error("Error with speech recognition: %s", err)
            self.speech = ""
        self.run = False

    def start_control(self, topic, data):
        """Control system"""
        if not self.run:
            self.run = True
            background = Thread(target=self.start_recognition)
            background.start()
