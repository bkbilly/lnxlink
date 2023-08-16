"""Checks if the microphone is used"""
import glob
import json
import re


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Microphone used"
        self.icon = "mdi:microphone"
        self.sensor_type = "binary_sensor"
        self.lnxlink = lnxlink

        _, returncode = self.lnxlink.subprocess(
            "which pactl && pactl -f json list short source-outputs",
        )
        self.use_pactl = False
        if returncode == 0:
            self.use_pactl = True

    def get_old_info(self):
        """Gather information from the system"""
        if self.use_pactl:
            stdout, _ = self.lnxlink.subprocess(
                "pactl -f json list short source-outputs",
            )
            # Replace 0,00 values with 0.00
            stdout = re.sub(r"(\s*[+-]?[0-9]+),([0-9]+\s*)", r"\1.\2", stdout)
            data = json.loads(stdout)
            if len(data) > 0:
                return "ON"
            return "OFF"
        mics = glob.glob("/proc/asound/**/*c/sub*/status", recursive=True)
        for mic in mics:
            with open(mic, encoding="UTF-8") as mic_content:
                mic_status = mic_content.read().strip().lower()
                if mic_status != "closed":
                    return "ON"
        return "OFF"
