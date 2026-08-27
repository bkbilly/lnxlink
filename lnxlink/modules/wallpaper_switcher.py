"""Switch and report desktop wallpaper"""
import os
import time
import logging
import shlex
from pathlib import Path
from urllib.parse import urlparse, unquote
from shutil import which

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Wallpaper Switcher"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "wallpaper_switcher",
            {
                "path": "",
                "recursive": False,
                "extensions": [".jpg", ".jpeg", ".png", ".webp", ".bmp"],
                "options": [],
                "refresh_interval": 300,
                "read_command": "",
                "set_command": "",
            },
        )
        self.settings = self.lnxlink.config["settings"].get("wallpaper_switcher", {})
        self.wallpapers = {}
        self.path_to_label = {}
        self.options = []
        self.last_scan = 0
        self.backend = self._detect_backend()
        self._refresh_wallpapers(force=True)

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {
            "Wallpaper Path": {
                "type": "text",
                "icon": "mdi:image",
                "min": 1,
                "max": 4096,
                "value_template": "{{ value_json.path }}",
            }
        }
        if self.options:
            discovery_info["Wallpaper Select"] = {
                "type": "select",
                "icon": "mdi:image-multiple",
                "options": self.options,
                "value_template": "{{ value_json.label }}",
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        if self._refresh_wallpapers():
            self.lnxlink.setup_discovery("wallpaper_switcher")
        current_path = self._read_wallpaper_path()
        label = self._path_to_label(current_path)
        return {
            "path": current_path,
            "label": label,
        }

    def start_control(self, topic, data):
        """Control system"""
        command = topic[1]
        if isinstance(data, dict):
            data = data.get("path") or data.get("label") or ""
        if command == "wallpaper_select":
            path = self.wallpapers.get(str(data), str(data))
        else:
            path = str(data)
        if not path:
            logger.error("Wallpaper path is empty")
            return
        self._set_wallpaper(path)

    def _refresh_wallpapers(self, force=False):
        refresh_interval = int(self.settings.get("refresh_interval", 300) or 300)
        if not force and time.time() - self.last_scan < refresh_interval:
            return False
        self.last_scan = time.time()
        new_map = self._collect_wallpapers()
        if new_map != self.wallpapers:
            self.wallpapers = new_map
            self.path_to_label = {path: label for label, path in new_map.items()}
            self.options = list(new_map.keys())
            return True
        return False

    def _collect_wallpapers(self):
        options = self.settings.get("options") or []
        if options:
            return self._map_paths(options, base_dir=None)

        base_path = str(self.settings.get("path", "")).strip()
        if not base_path:
            return {}
        base_path = os.path.expanduser(base_path)
        base_dir = Path(base_path)
        if base_dir.is_file():
            return self._map_paths([str(base_dir)], base_dir.parent)
        if not base_dir.is_dir():
            logger.error("Wallpaper path not found: %s", base_dir)
            return {}

        recursive = bool(self.settings.get("recursive", False))
        extensions = self._get_extensions()
        if recursive:
            paths = [path for path in base_dir.rglob("*") if path.is_file()]
        else:
            paths = [path for path in base_dir.glob("*") if path.is_file()]
        filtered = [str(path) for path in paths if path.suffix.lower() in extensions]
        return self._map_paths(filtered, base_dir)

    def _map_paths(self, paths, base_dir):
        mapped = {}
        used_labels = set()
        for raw_path in paths:
            norm_path = self._normalize_path(raw_path)
            if base_dir:
                label = os.path.relpath(norm_path, base_dir)
            else:
                label = os.path.basename(norm_path)
            label = label.replace(os.sep, "/")
            if label in used_labels:
                label = f"{label} ({len(used_labels)})"
            used_labels.add(label)
            mapped[label] = norm_path
        return mapped

    def _read_wallpaper_path(self):
        read_command = str(self.settings.get("read_command", "")).strip()
        if read_command:
            stdout, _, _ = syscommand(read_command, ignore_errors=True)
            return self._normalize_path(self._strip_quotes(stdout)) if stdout else None

        if self.backend == "gnome" and which("gsettings") is not None:
            stdout, _, _ = syscommand(
                "gsettings get org.gnome.desktop.background picture-uri",
                ignore_errors=True,
            )
            value = self._strip_quotes(stdout)
            if not value:
                stdout, _, _ = syscommand(
                    "gsettings get org.gnome.desktop.background picture-uri-dark",
                    ignore_errors=True,
                )
                value = self._strip_quotes(stdout)
            return self._normalize_path(value) if value else None

        return None

    def _set_wallpaper(self, path):
        path = self._normalize_path(path)
        if not os.path.exists(path):
            logger.error("Wallpaper file not found: %s", path)
            return

        set_command = str(self.settings.get("set_command", "")).strip()
        if set_command:
            cmd = self._format_command(set_command, path)
            syscommand(cmd, ignore_errors=True)
            return

        if self.backend == "gnome" and which("gsettings") is not None:
            uri = Path(path).as_uri()
            quoted_uri = shlex.quote(uri)
            syscommand(
                f"gsettings set org.gnome.desktop.background picture-uri {quoted_uri}",
                ignore_errors=True,
            )
            syscommand(
                f"gsettings set org.gnome.desktop.background picture-uri-dark {quoted_uri}",
                ignore_errors=True,
            )
            return

        if which("plasma-apply-wallpaperimage") is not None:
            syscommand(
                f"plasma-apply-wallpaperimage {shlex.quote(path)}",
                ignore_errors=True,
            )
            return

        if which("swaymsg") is not None:
            syscommand(
                f"swaymsg output '*' bg {shlex.quote(path)} fill",
                ignore_errors=True,
            )
            return

        logger.error("No supported wallpaper backend found; set set_command")

    def _detect_backend(self):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop or "unity" in desktop:
            return "gnome"
        return "custom"

    def _path_to_label(self, path):
        if not path:
            return None
        norm_path = self._normalize_path(path)
        if self.path_to_label:
            return self.path_to_label.get(norm_path)
        return norm_path

    def _normalize_path(self, path):
        if path is None:
            return None
        text = str(path).strip()
        if text.startswith("file://"):
            parsed = urlparse(text)
            text = unquote(parsed.path)
        return str(Path(os.path.expanduser(text)).resolve())

    def _strip_quotes(self, value):
        if value is None:
            return ""
        return str(value).strip().strip("'").strip('"')

    def _get_extensions(self):
        extensions = self.settings.get("extensions") or []
        if not extensions:
            extensions = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
        return {ext.lower() for ext in extensions}

    def _format_command(self, command, path):
        quoted = shlex.quote(path)
        if "{path}" in command:
            return command.format(path=quoted)
        return f"{command} {quoted}"
