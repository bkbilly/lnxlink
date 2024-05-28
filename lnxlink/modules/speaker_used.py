"""Checks if the Speaker is used"""
import glob
import json
import re
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Speaker used"
        self.lnxlink = lnxlink

        _, _, returncode = syscommand(
            "which pactl && pactl -f json list short sink-inputs", ignore_errors=True
        )
        self.use_pactl = False
        if returncode == 0:
            self.use_pactl = True

    def get_info(self):
        """Gather information from the system"""
        if self.use_pactl:
            stdout, _, _ = syscommand(
                "pactl -f json list short sink-inputs",
            )
            # Replace 0,00 values with 0.00
            stdout = re.sub(r"(\s*[+-]?[0-9]+),([0-9]+\s*)", r"\1.\2", stdout)
            data = json.loads(stdout)
            if len(data) > 0:
                return "ON"
            return "OFF"
        speakers = glob.glob("/proc/asound/card*/pcm*/sub*/status", recursive=True)
        for speaker in speakers:
            with open(speaker, encoding="UTF-8") as speaker_content:
                speaker_status = speaker_content.read().strip().lower()
                if speaker_status != "closed":
                    return "ON"
        return "OFF"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Speaker used": {
                "type": "binary_sensor",
                "icon": "mdi:speaker",
            },
        }
