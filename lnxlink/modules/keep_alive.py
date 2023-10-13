"""Keeps display on"""
import re
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.lnxlink = lnxlink
        self.name = "Keep Alive"
        self.keepalive = "OFF"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Keep Alive": {
                "type": "switch",
                "icon": "mdi:mouse-variant",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        enabled_list = []

        # Check if Gnome Idle Time is active
        stdout_dim, _, _ = syscommand(
            "gsettings get org.gnome.desktop.session idle-delay"
        )
        stdout_suspend, _, _ = syscommand(
            "gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type"
        )
        if stdout_dim != "":
            disabled_dim = "0" == stdout_dim.split()[1]
            if disabled_dim and stdout_suspend != "":
                enabled_list.append("nothing" in stdout_suspend)

        # Check if DPMS is active
        stdout_xset, _, _ = syscommand("xset q")
        xset_pattern = re.compile(r"Standby: (\d+)\s+Suspend: (\d+)\s+Off: (\d+)")
        xset_match = re.findall(xset_pattern, stdout_xset)
        for nums in xset_match:
            enabled_list.append(all(num != "0" for num in nums))
            if enabled_list[-1]:
                enabled_list.append("DPMS is Enabled" in stdout_xset)

        return any(enabled_list)

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            syscommand(
                "gsettings set org.gnome.desktop.session idle-delay 600",
            )
            syscommand(
                'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "suspend"',
            )
            syscommand(
                "xset +dpms",
            )
        elif data.lower() == "on":
            syscommand(
                "gsettings set org.gnome.desktop.session idle-delay 0",
            )
            syscommand(
                'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "nothing"',
            )
            syscommand(
                "xset -dpms",
            )
