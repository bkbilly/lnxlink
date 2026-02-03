"""Monitor the currently active, interactive graphical user."""
import json
import logging

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Monitor the currently active interactive graphical users. This module
       ignores users with locked sessions and non-graphical sessions like SSH.
       If multiple users are logged in, they are separated by ', '. If no users
       are logged in, the sensor reads as 'No user'.

       Requires `loginctl` command to be available."""

    def __init__(self, lnxlink):
        self.name = "Current Users"
        self.lnxlink = lnxlink

        _, _, returncode = syscommand("loginctl --json=short list-sessions")
        if returncode != 0:
            raise SystemError("Could not find loginctl command")

    def get_info(self) -> str:
        active_users = self._get_users()
        if not active_users:
            return "No user"
        else:
            return ", ".join(active_users)


    def exposed_controls(self):
        """Exposes to home assistant"""
        update_interval = self.lnxlink.config.get("update_interval", 5)
        return {
            "Current Users": {
                "type": "sensor",
                "icon": "mdi:account",
                "expire_after": update_interval * 5,
            },
        }


    def _get_sessions(self) -> list:
        """Returns all the current sessions"""
        stdout, _, returncode = syscommand("loginctl --json=short list-sessions")
        if returncode != 0:
            logger.debug("Error running loginctl; returning no current user")
            return []

        return json.loads(stdout)


    def _get_users(self) -> set[str]:
        """Returns the set of users with active, unlocked, graphical sessions.
           Normally computers only have 1 seat, so unlikely we'll get more than
           one."""
        sessions = self._get_sessions()

        active_users = set()

        for session in sessions:
            # We only want user sessions with a seat.
            # SSH sessions won't have a seat
            if session.get("class") == "user" and session.get("seat"):
                session_id = session.get("session")
                username = session.get("user")

                if not session_id or not username:
                    continue

                stdout, _, returncode = syscommand(
                    f"loginctl show-session {session_id} --property=Active --property=LockedHint"
                )

                if returncode != 0:
                    logger.debug("Error running loginctl for a session; skipping")
                elif "Active=yes" in stdout and "LockedHint=no" in stdout:
                    active_users.add(username)

        return active_users
