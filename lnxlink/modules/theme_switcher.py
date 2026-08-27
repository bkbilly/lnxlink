"""Switch between light and dark desktop themes"""
import logging
import os
import shlex
from shutil import which

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module for desktop theme switching"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Theme Switcher"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "theme_switcher",
            {
                "read_command": "",
                "light_command": "",
                "dark_command": "",
                "light_value": "default",
                "dark_value": "prefer-dark",
                "light_theme": "BreezeLight",
                "dark_theme": "BreezeDark",
            },
        )
        self.settings = self.lnxlink.config["settings"].get("theme_switcher", {})

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Theme": {
                "type": "switch",
                "icon": "mdi:theme-light-dark",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        is_dark, source, raw, theme = self._read_state()
        status = None
        if is_dark is True:
            status = "ON"
        elif is_dark is False:
            status = "OFF"
        return {
            "status": status,
            "attributes": {
                "is_dark": is_dark,
                "source": source,
                "raw": raw,
                "theme": theme,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        enabled = self._parse_bool(data)
        if enabled is None:
            logger.error("Expected ON/OFF, received: %s", data)
            return
        self._set_state(enabled)
        self.lnxlink.run_module(self.name, self.get_info())

    def _read_state(self):
        # 1. Custom read command
        read_command = str(self.settings.get("read_command", "")).strip()
        if read_command:
            stdout, _, _ = syscommand(read_command, ignore_errors=True)
            return self._parse_theme(stdout), "command", stdout, stdout.strip()

        # 2. GNOME gsettings
        if which("gsettings") is not None:
            stdout, _, rc = syscommand(
                "gsettings get org.gnome.desktop.interface color-scheme",
                ignore_errors=True,
            )
            value = self._strip_quotes(stdout)
            if rc == 0 and value:
                return (
                    self._parse_theme(value),
                    "gnome_gsettings",
                    stdout,
                    value,
                )

        # 3. KDE Plasma kreadconfig
        for tool in ["kreadconfig6", "kreadconfig5"]:
            if which(tool) is not None:
                stdout, _, rc = syscommand(
                    f"{tool} --file kdeglobals --group General --key ColorScheme",
                    ignore_errors=True,
                )
                if rc == 0 and stdout.strip():
                    val = stdout.strip()
                    return self._parse_theme(val), "kde_config", stdout, val

        # 4. Fallback GNOME gtk-theme
        if which("gsettings") is not None:
            theme_stdout, _, rc = syscommand(
                "gsettings get org.gnome.desktop.interface gtk-theme",
                ignore_errors=True,
            )
            theme_value = self._strip_quotes(theme_stdout)
            if rc == 0 and theme_value:
                return (
                    self._parse_theme(theme_value),
                    "gnome_gtk_theme",
                    theme_stdout,
                    theme_value,
                )

        return None, "none", "", None

    def _set_state(self, is_dark):
        light_command = str(self.settings.get("light_command", "")).strip()
        dark_command = str(self.settings.get("dark_command", "")).strip()
        if is_dark and dark_command:
            syscommand(dark_command, ignore_errors=True)
            return
        if not is_dark and light_command:
            syscommand(light_command, ignore_errors=True)
            return

        # 1. GNOME gsettings
        if which("gsettings") is not None:
            light_value = self._strip_quotes(self.settings.get("light_value", "default"))
            dark_value = self._strip_quotes(self.settings.get("dark_value", "prefer-dark"))
            target_value = dark_value if is_dark else light_value
            syscommand(
                f"gsettings set org.gnome.desktop.interface color-scheme {shlex.quote(target_value)}",
                ignore_errors=True,
            )

            theme_key = "dark_theme" if is_dark else "light_theme"
            theme_value = self._strip_quotes(self.settings.get(theme_key, ""))
            if theme_value:
                syscommand(
                    f"gsettings set org.gnome.desktop.interface gtk-theme {shlex.quote(theme_value)}",
                    ignore_errors=True,
                )

        # 2. KDE Plasma apply colorscheme
        if which("plasma-apply-colorscheme") is not None:
            theme_key = "dark_theme" if is_dark else "light_theme"
            default_theme = "BreezeDark" if is_dark else "BreezeLight"
            theme_value = self._strip_quotes(self.settings.get(theme_key, default_theme))
            syscommand(
                f"plasma-apply-colorscheme {shlex.quote(theme_value)}",
                ignore_errors=True,
            )

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "dark"}:
            return True
        if text in {"0", "false", "no", "off", "light"}:
            return False
        return None

    @staticmethod
    def _parse_theme(value):
        if value is None:
            return None
        text = str(value).strip().lower()
        if "dark" in text or text in {"prefer-dark", "dark"}:
            return True
        if "light" in text or text in {"default", "light"}:
            return False
        return None

    @staticmethod
    def _strip_quotes(value):
        if value is None:
            return ""
        return str(value).strip().strip("'").strip('"')
