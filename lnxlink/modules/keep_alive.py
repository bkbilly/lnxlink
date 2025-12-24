"""Prevent monitor sleep or idle states"""
import re
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand, get_display_variable


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Keep Alive"
        self.keepalive = "OFF"
        if which("gsettings") is None or which("xset") is None:
            raise SystemError("System commands 'gsettings' or 'xset' not found")

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
        if which("gsettings"):
            stdout_dim, _, returncode_dim = syscommand(
                "gsettings get org.gnome.desktop.session idle-delay",
                ignore_errors=True,
            )
            stdout_suspend, _, returncode_susp = syscommand(
                "gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type",
                ignore_errors=True,
            )
            if stdout_dim != "" and returncode_dim == 0 and returncode_susp == 0:
                disabled_dim = "0" == stdout_dim.split()[1]
                if disabled_dim and stdout_suspend != "":
                    enabled_list.append("nothing" in stdout_suspend)

        # Check if DPMS is active
        if which("xset"):
            display_variable = get_display_variable()
            if display_variable is not None:
                stdout_xset, _, _ = syscommand(f"xset -display {display_variable} q")
                xset_pattern = re.compile(
                    r"Standby: (\d+)\s+Suspend: (\d+)\s+Off: (\d+)"
                )
                xset_match = re.findall(xset_pattern, stdout_xset)
                for nums in xset_match:
                    enabled_list.append(all(num != "0" for num in nums))
                    if enabled_list[-1]:
                        enabled_list.append("DPMS is Enabled" in stdout_xset)

        return any(enabled_list)

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            if which("gsettings"):
                syscommand(
                    "gsettings set org.gnome.desktop.session idle-delay 600",
                )
                syscommand(
                    'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "suspend"',  # noqa: E501
                )
            if which("xset"):
                syscommand(
                    "xset +dpms",
                )
        elif data.lower() == "on":
            if which("gsettings"):
                syscommand(
                    "gsettings set org.gnome.desktop.session idle-delay 0",
                )

                syscommand(
                    'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "nothing"',  # noqa: E501
                )
            if which("xset"):
                syscommand(
                    "xset -dpms",
                )
