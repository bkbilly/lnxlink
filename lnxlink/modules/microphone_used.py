"""Checks if the microphone is used"""
import glob
import json
import re
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Microphone used"
        self.lnxlink = lnxlink

        _, _, returncode = syscommand(
            "which pactl && pactl -f json list short source-outputs", ignore_errors=True
        )
        self.use_pactl = False
        if returncode == 0:
            self.use_pactl = True

    def get_info(self):
        """Gather information from the system"""
        if self.use_pactl:
            stdout, _, _ = syscommand(
                "pactl -f json list source-outputs",
            )
            # Replace 0,00 values with 0.00
            stdout = re.sub(r"(\s*[+-]?[0-9]+),([0-9]+\s*)", r"\1.\2", stdout)
            data = json.loads(stdout)
            for output in data:
                app_name = output.get("properties", {}).get("application.name")
                if app_name and app_name != "":
                    return {"is_used": "ON", "application": app_name}
            return {"is_used": "OFF", "application": None}
        mics = glob.glob("/proc/asound/**/*c/sub*/status", recursive=True)
        for mic in mics:
            with open(mic, encoding="UTF-8") as mic_content:
                mic_status = mic_content.read().strip().lower()
                if mic_status != "closed":
                    return {"is_used": "ON", "application": None}
        return {"is_used": "OFF", "application": None}

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Microphone used": {
                "type": "binary_sensor",
                "icon": "mdi:microphone",
                "value_template": "{{ value_json.is_used }}",
                "attributes_template": "{{ value_json | tojson }}",
            },
        }
