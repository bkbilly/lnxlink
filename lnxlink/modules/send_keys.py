"""Uses xdotool to press keyboard keys"""
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Send Keys"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Send_Keys": {
                "type": "text",
                "icon": "mdi:keyboard-outline",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        syscommand(f"xdotool key {data}")
