"""Report desktop environment accent color"""
import configparser
import logging
import os
from shutil import which

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")

GNOME_ACCENT_COLORS = {
    "blue": (53, 132, 228),
    "teal": (33, 144, 164),
    "green": (58, 148, 74),
    "yellow": (200, 136, 0),
    "orange": (237, 91, 0),
    "red": (230, 45, 66),
    "pink": (213, 97, 153),
    "purple": (145, 65, 172),
    "slate": (94, 92, 100),
}


class Addon:
    """Addon module for Desktop Accent Color"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Accent Color"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "accent_color",
            {
                "read_command": "",
            },
        )
        self.settings = self.lnxlink.config["settings"].get("accent_color", {})

    def exposed_controls(self):
        """Exposes to Home Assistant"""
        return {
            "Accent Color": {
                "type": "sensor",
                "icon": "mdi:palette",
                "value_template": "{{ value_json.hex }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        r, g, b, backend = self._get_accent_color()
        if r is None or g is None or b is None:
            return {
                "hex": None,
                "attributes": {
                    "r": None,
                    "g": None,
                    "b": None,
                    "rgb": None,
                    "hex": None,
                    "backend": backend,
                },
            }

        hex_code = f"#{r:02x}{g:02x}{b:02x}"
        return {
            "hex": hex_code,
            "attributes": {
                "r": r,
                "g": g,
                "b": b,
                "rgb": [r, g, b],
                "hex": hex_code,
                "backend": backend,
            },
        }

    def _get_accent_color(self):
        """Detect accent color from system settings"""
        # 1. Custom command
        read_cmd = str(self.settings.get("read_command", "")).strip()
        if read_cmd:
            stdout, _, rc = syscommand(read_cmd, ignore_errors=True)
            if rc == 0 and stdout:
                rgb = self._parse_color_string(stdout)
                if rgb:
                    return rgb[0], rgb[1], rgb[2], "command"

        # 2. KDE Plasma kdeglobals
        kdeglobals_path = os.path.expanduser("~/.config/kdeglobals")
        if os.path.exists(kdeglobals_path):
            try:
                config = configparser.ConfigParser()
                config.read(kdeglobals_path, encoding="utf-8")
                if "General" in config and "AccentColor" in config["General"]:
                    accent_val = config["General"]["AccentColor"].strip()
                    rgb = self._parse_color_string(accent_val)
                    if rgb:
                        return rgb[0], rgb[1], rgb[2], "kde"
            except Exception as err:
                logger.debug("Failed to read kdeglobals: %s", err)

            if which("kreadconfig6") is not None:
                stdout, _, rc = syscommand(
                    "kreadconfig6 --file kdeglobals --group General --key AccentColor",
                    ignore_errors=True,
                )
                if rc == 0 and stdout:
                    rgb = self._parse_color_string(stdout)
                    if rgb:
                        return rgb[0], rgb[1], rgb[2], "kde_kreadconfig"
            elif which("kreadconfig5") is not None:
                stdout, _, rc = syscommand(
                    "kreadconfig5 --file kdeglobals --group General --key AccentColor",
                    ignore_errors=True,
                )
                if rc == 0 and stdout:
                    rgb = self._parse_color_string(stdout)
                    if rgb:
                        return rgb[0], rgb[1], rgb[2], "kde_kreadconfig"

        # 3. GNOME accent-color
        if which("gsettings") is not None:
            stdout, _, rc = syscommand(
                "gsettings get org.gnome.desktop.interface accent-color",
                ignore_errors=True,
            )
            if rc == 0 and stdout:
                color_name = stdout.strip("'\" \n").lower()
                if color_name in GNOME_ACCENT_COLORS:
                    r, g, b = GNOME_ACCENT_COLORS[color_name]
                    return r, g, b, "gnome"

        return None, None, None, "unknown"

    @staticmethod
    def _parse_color_string(val):
        """Parse RGB comma-separated string, HEX (#ffffff), or RGB array"""
        if not val:
            return None
        text = str(val).strip().strip("'\"")
        if text.startswith("#"):
            text = text.lstrip("#")
            if len(text) == 6:
                try:
                    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
                except ValueError:
                    return None
            elif len(text) == 3:
                try:
                    return (
                        int(text[0] * 2, 16),
                        int(text[1] * 2, 16),
                        int(text[2] * 2, 16),
                    )
                except ValueError:
                    return None
        if "," in text:
            parts = [p.strip() for p in text.split(",") if p.strip()]
            if len(parts) >= 3:
                try:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    return (
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)),
                    )
                except ValueError:
                    return None
        return None
