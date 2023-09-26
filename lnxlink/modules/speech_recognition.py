"""Checks if the microphone is used"""
from threading import Thread
import logging
import speech_recognition as sr

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Speech Recognition"
        self.run = False
        self.speech = ""

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
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source)
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
