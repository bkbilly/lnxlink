"""Run a terminal command"""


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
        stdout, _ = self.lnxlink.subprocess(data)
        return stdout
