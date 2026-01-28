"""Set and monitor clipboard content"""
import os
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Clipboard"
        self.lnxlink = lnxlink
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
        self.clipboard_tool = None
        self.last_clipboard = ""

        # Add settings with monitoring disabled by default
        self.lnxlink.add_settings(
            "clipboard",
            {
                "monitor_enabled": False,
            },
        )

        # Determine which clipboard tool to use
        if self.session_type == "wayland":
            if which("wl-copy") is not None and which("wl-paste") is not None:
                self.clipboard_tool = "wl-clipboard"
                logger.debug("Using wl-clipboard for Wayland")
            else:
                raise SystemError(
                    "System command 'wl-clipboard' (wl-copy/wl-paste) not found"
                )
        elif self.session_type == "x11":
            if which("xclip") is not None:
                self.clipboard_tool = "xclip"
                logger.debug("Using xclip for X11")
            elif which("xsel") is not None:
                self.clipboard_tool = "xsel"
                logger.debug("Using xsel for X11")
            else:
                raise SystemError("System command 'xclip' or 'xsel' not found")
        else:
            raise SystemError(f"Unsupported session type: {self.session_type}")

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {
            "Clipboard Set": {
                "type": "text",
                "icon": "mdi:clipboard-text",
                "max": 255,
            }
        }

        # Only add monitor sensor if enabled in settings
        if self.lnxlink.config["settings"]["clipboard"]["monitor_enabled"]:
            discovery_info["Clipboard Monitor"] = {
                "type": "sensor",
                "icon": "mdi:clipboard-check",
                "entity_category": "diagnostic",
            }

        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        # Only monitor clipboard if enabled in settings
        if not self.lnxlink.config["settings"]["clipboard"]["monitor_enabled"]:
            return None

        try:
            current_clipboard = self._get_clipboard()

            # Only update if clipboard content changed
            if current_clipboard != self.last_clipboard:
                self.last_clipboard = current_clipboard
                return current_clipboard
        except Exception as err:
            logger.debug("Error reading clipboard: %s", err)

        return self.last_clipboard

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "clipboard_set":
            try:
                self._set_clipboard(data)
                logger.info("Clipboard set successfully")
            except Exception as err:
                logger.error("Error setting clipboard: %s", err)

    def _get_clipboard(self):
        """Get current clipboard content"""
        if self.clipboard_tool == "wl-clipboard":
            # Use wl-paste for Wayland
            stdout, _, returncode = syscommand(
                "wl-paste --no-newline",
                ignore_errors=True,
                timeout=1,
            )
            if returncode == 0:
                return stdout

        elif self.clipboard_tool == "xclip":
            # Use xclip for X11
            stdout, _, returncode = syscommand(
                "xclip -selection clipboard -o",
                ignore_errors=True,
                timeout=1,
            )
            if returncode == 0:
                return stdout

        elif self.clipboard_tool == "xsel":
            # Use xsel for X11
            stdout, _, returncode = syscommand(
                "xsel --clipboard --output",
                ignore_errors=True,
                timeout=1,
            )
            if returncode == 0:
                return stdout

        return ""

    def _set_clipboard(self, text):
        """Set clipboard content"""
        # Escape single quotes in text for shell command
        escaped_text = text.replace("'", "'\\''")

        if self.clipboard_tool == "wl-clipboard":
            # Use wl-copy for Wayland
            _, _, returncode = syscommand(
                f"printf '%s' '{escaped_text}' | wl-copy",
                timeout=2,
            )
            if returncode != 0:
                raise SystemError(f"wl-copy failed with code {returncode}")

        elif self.clipboard_tool == "xclip":
            # Use xclip for X11
            _, _, returncode = syscommand(
                f"printf '%s' '{escaped_text}' | xclip -selection clipboard",
                timeout=2,
            )
            if returncode != 0:
                raise SystemError(f"xclip failed with code {returncode}")

        elif self.clipboard_tool == "xsel":
            # Use xsel for X11
            _, _, returncode = syscommand(
                f"printf '%s' '{escaped_text}' | xsel --clipboard --input",
                timeout=2,
            )
            if returncode != 0:
                raise SystemError(f"xsel failed with code {returncode}")

        # Update last_clipboard to avoid triggering monitor on self-set
        self.last_clipboard = text
