"""Report and set the desktop environment's accent color"""
import configparser
import logging
import os
from shutil import which
from typing import Optional, Tuple

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")

ACCENT_COLORS = {
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
    """Addon module for the desktop environment's accent color"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Accent Color"
        self.lnxlink = lnxlink
        self.kwriteconfig = which("kwriteconfig6") or which("kwriteconfig5")
        self.kreadconfig = which("kreadconfig6") or which("kreadconfig5")

        # Decide once which backend to use, so we don't spawn `which`
        # subprocesses on every get_info()/start_control() call.
        self.backend = self._detect_backend()
        if self.backend is None:
            raise RuntimeError("No supported Accent Color backend found")
        logger.debug("Accent Color backend selected: %s", self.backend)

    def _detect_backend(self) -> Optional[str]:
        """Pick a single accent color backend, in priority order"""
        if self.kwriteconfig is not None:
            return "kde"
        if which("gsettings") is not None:
            return "gnome"
        return None

    def exposed_controls(self):
        """Exposes to Home Assistant"""
        return {
            "Accent Color": {
                "type": "select",
                "icon": "mdi:palette",
                "options": list(ACCENT_COLORS),
                "value_template": "{{ value_json.name }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        r, g, b = self._read_color()
        name, exact = self._closest_name(r, g, b) if r is not None else (None, None)
        hex_code = f"#{r:02x}{g:02x}{b:02x}" if r is not None else None
        return {
            "name": name,
            "attributes": {
                "r": r,
                "g": g,
                "b": b,
                "rgb": [r, g, b] if r is not None else None,
                "hex": hex_code,
                "exact": exact,
                "backend": self.backend,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        color = str(data).strip().lower()
        if color not in ACCENT_COLORS:
            logger.error(
                "Invalid accent color '%s'. Allowed options: %s",
                data,
                list(ACCENT_COLORS),
            )
            return
        self._set_color(color)
        self.lnxlink.run_module(self.name, self.get_info())

    def _read_color(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Detect accent color from system settings"""
        if self.backend == "kde":
            return self._read_kde()
        return self._read_gnome()

    def _read_kde(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        kdeglobals_path = os.path.expanduser("~/.config/kdeglobals")
        if os.path.exists(kdeglobals_path):
            try:
                config = configparser.ConfigParser()
                config.read(kdeglobals_path, encoding="utf-8")
                if "General" in config and "AccentColor" in config["General"]:
                    rgb = self._parse_color_string(config["General"]["AccentColor"])
                    if rgb:
                        return rgb
            except Exception as err:
                logger.debug("Failed to read kdeglobals: %s", err)

        if self.kreadconfig is not None:
            stdout, _, rc = syscommand(
                f"{self.kreadconfig} --file kdeglobals --group General --key AccentColor",
                ignore_errors=True,
            )
            if rc == 0 and stdout:
                rgb = self._parse_color_string(stdout)
                if rgb:
                    return rgb

        return None, None, None

    @staticmethod
    def _read_gnome() -> Tuple[Optional[int], Optional[int], Optional[int]]:
        stdout, _, rc = syscommand(
            "gsettings get org.gnome.desktop.interface accent-color",
            ignore_errors=True,
        )
        if rc == 0 and stdout:
            color_name = stdout.strip("'\" \n").lower()
            if color_name in ACCENT_COLORS:
                return ACCENT_COLORS[color_name]
        return None, None, None

    def _set_color(self, color: str) -> None:
        if self.backend == "kde":
            self._set_kde(color)
        else:
            self._set_gnome(color)

    def _set_kde(self, color: str) -> None:
        r, g, b = ACCENT_COLORS[color]
        # Plasma watches kdeglobals for changes and applies the new accent
        # to running apps without needing an extra reconfigure/reload call.
        syscommand(
            f"{self.kwriteconfig} --file kdeglobals --group General "
            f'--key AccentColor "{r},{g},{b}"',
            ignore_errors=True,
        )
        syscommand(
            f"{self.kwriteconfig} --file kdeglobals --group General "
            f"--key AccentColorFromWallpaper --type bool false",
            ignore_errors=True,
        )

    @staticmethod
    def _set_gnome(color: str) -> None:
        syscommand(
            f"gsettings set org.gnome.desktop.interface accent-color {color}",
            ignore_errors=True,
        )

    @staticmethod
    def _closest_name(r: int, g: int, b: int) -> Tuple[str, bool]:
        """Return the closest named accent color, and whether it's an exact match"""
        best_name, best_dist = None, None
        for name, (cr, cg, cb) in ACCENT_COLORS.items():
            dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
            if best_dist is None or dist < best_dist:
                best_name, best_dist = name, dist
        return best_name, best_dist == 0

    @staticmethod
    def _parse_color_string(  # pylint: disable=too-many-return-statements
        val,
    ) -> Optional[Tuple[int, int, int]]:
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
