"""Run a terminal command"""
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "bash"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Bash_Command": {
                "type": "text",
                "icon": "mdi:bash",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        stdout, _, _ = syscommand(data)
        return stdout
