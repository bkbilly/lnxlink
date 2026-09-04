"""Track and control the session lock state"""
import logging
import os
from shutil import which
from typing import Any, Dict, Optional, Tuple

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module for session locking and lock state monitoring"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Session Lock"
        self.lnxlink = lnxlink
        if which("loginctl") is None:
            raise RuntimeError(
                "loginctl not found, session lock state is not supported"
            )
        # Resolve the session once, at startup, instead of on every read/lock/unlock.
        self.user = os.environ.get("USER") or os.environ.get("LOGNAME")
        self.session_id = self._detect_session_id()

    def exposed_controls(self) -> Dict[str, Dict[str, Any]]:
        """Exposes to home assistant"""
        return {
            "Session Lock": {
                "type": "switch",
                "icon": "mdi:lock",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self) -> Dict[str, Any]:
        """Gather information from the system"""
        locked, raw = self._read_lock_state()
        status = None
        if locked is True:
            status = "ON"
        elif locked is False:
            status = "OFF"
        return {
            "status": status,
            "attributes": {
                "locked": locked,
                "session_id": self.session_id,
                "user": self.user,
                "raw": raw,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        enabled = self._parse_bool(data)
        if enabled is None:
            logger.error("Expected ON/OFF, received: %s", data)
            return
        if enabled:
            self._lock()
        else:
            self._unlock()
        self.lnxlink.run_module(self.name, self.get_info())

    def _detect_session_id(self) -> Optional[str]:
        """Resolve the current session id once, at startup"""
        env_session = os.environ.get("XDG_SESSION_ID")
        if env_session:
            return env_session

        stdout, _, _ = syscommand(
            "loginctl list-sessions --no-legend", ignore_errors=True
        )
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and self.user and parts[2] == self.user:
                return parts[0]
        return None

    def _read_lock_state(self) -> Tuple[Optional[bool], str]:
        if not self.session_id:
            return None, ""
        stdout, _, _ = syscommand(
            f"loginctl show-session {self.session_id} -p LockedHint",
            ignore_errors=True,
        )
        value = stdout.split("=", maxsplit=1)[-1].strip()
        return self._parse_bool(value), stdout

    def _lock(self):
        command = "loginctl lock-session"
        if self.session_id:
            command = f"{command} {self.session_id}"
        syscommand(command, ignore_errors=True)

    def _unlock(self):
        command = "loginctl unlock-session"
        if self.session_id:
            command = f"{command} {self.session_id}"
        syscommand(command, ignore_errors=True)

    @staticmethod
    def _parse_bool(value) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "locked"}:
            return True
        if text in {"0", "false", "no", "off", "unlocked"}:
            return False
        return None
