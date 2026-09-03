"""Toggle and report Do Not Disturb (DND) / notification inhibition status"""
import configparser
import logging
import os
from shutil import which
from typing import Any, Dict, Optional, Tuple

from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")

_KDE_UNTIL_ON = "2037,1,1,0,0,0.0"
_KDE_UNTIL_OFF = ""


class Addon:  # pylint: disable=too-many-instance-attributes
    """Addon module for Do Not Disturb (DND) notification inhibition"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Do Not Disturb"
        self.lnxlink = lnxlink
        self.inhibit_cookie: Optional[int] = None
        self.conn = None
        self.notif_addr = DBusAddress(
            "/org/freedesktop/Notifications",
            bus_name="org.freedesktop.Notifications",
            interface="org.freedesktop.Notifications",
        )
        self.prop_addr = DBusAddress(
            "/org/freedesktop/Notifications",
            bus_name="org.freedesktop.Notifications",
            interface="org.freedesktop.DBus.Properties",
        )
        self._init_dbus()

        # Decide once which backend to use, so we don't spawn `which`
        # subprocesses on every get_info()/start_control() call.
        self.kwriteconfig = which("kwriteconfig6") or which("kwriteconfig5")
        self.backend = self._detect_backend()
        if self.backend is None:
            raise RuntimeError("No supported Do Not Disturb backend found")
        logger.debug("DND backend selected: %s", self.backend)

    def _init_dbus(self):
        """Initialize session D-Bus connection for persistent notification inhibition"""
        try:
            self.conn = open_dbus_connection(bus="SESSION")
        except Exception as err:
            logger.debug("Failed to connect to session D-Bus in DND module: %s", err)
            self.conn = None

    def _detect_backend(  # pylint: disable=too-many-return-statements
        self,
    ) -> Optional[str]:
        """Pick a single DND backend, in priority order, based on what's available"""
        if self.kwriteconfig is not None:
            return "kde"
        if which("gsettings") is not None:
            return "gnome"
        if which("swaync-client") is not None:
            return "swaync"
        if which("dunstctl") is not None:
            return "dunst"
        if which("makoctl") is not None:
            return "mako"
        if self.conn is not None:
            return "freedesktop"
        return None

    def exposed_controls(self) -> Dict[str, Dict[str, Any]]:
        """Exposes to Home Assistant"""
        return {
            "Do Not Disturb": {
                "type": "switch",
                "icon": "mdi:minus-circle",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self) -> Dict[str, Any]:
        """Gather information from the system"""
        inhibited, raw = self._read_state()
        status = None
        if inhibited is True:
            status = "ON"
        elif inhibited is False:
            status = "OFF"

        return {
            "status": status,
            "attributes": {
                "inhibited": inhibited,
                "backend": self.backend,
                "raw": raw,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        enabled = self._parse_bool(data)
        if enabled is None:
            logger.error("Expected ON/OFF, received: %s", data)
            return
        self._set_state(enabled)
        # Immediately publish new state to MQTT
        self.lnxlink.run_module(self.name, self.get_info())

    def _read_state(self) -> Tuple[Optional[bool], Any]:
        """Reads DND state from the selected backend"""
        if self.backend == "kde":
            return self._read_kde()
        if self.backend == "gnome":
            return self._read_gnome()
        if self.backend == "swaync":
            return self._read_syscommand("swaync-client -D")
        if self.backend == "dunst":
            return self._read_syscommand("dunstctl is-paused")
        if self.backend == "mako":
            return self._read_mako()
        return self._read_freedesktop()

    def _read_kde(self) -> Tuple[Optional[bool], Any]:
        """KDE Plasma plasmanotifyrc check"""
        plasmanotifyrc_path = os.path.expanduser("~/.config/plasmanotifyrc")
        if not os.path.exists(plasmanotifyrc_path):
            return False, ""
        try:
            config = configparser.ConfigParser()
            config.read(plasmanotifyrc_path, encoding="utf-8")
            if "DoNotDisturb" in config and "Until" in config["DoNotDisturb"]:
                until_str = config["DoNotDisturb"]["Until"].strip()
                if until_str:
                    return True, until_str
        except Exception as err:
            logger.debug("Failed to read plasmanotifyrc: %s", err)
        return False, ""

    def _read_gnome(self) -> Tuple[Optional[bool], Any]:
        """GNOME gsettings (show-banners: false means DND is active)"""
        stdout, _, rc = syscommand(
            "gsettings get org.gnome.desktop.notifications show-banners",
            ignore_errors=True,
        )
        if rc != 0 or not stdout:
            return None, stdout
        show_banners = self._parse_bool(stdout)
        if show_banners is None:
            return None, stdout
        return not show_banners, stdout

    def _read_mako(self) -> Tuple[Optional[bool], Any]:
        stdout, _, rc = syscommand("makoctl mode", ignore_errors=True)
        if rc != 0 or not stdout:
            return None, stdout
        return "dnd" in stdout.lower(), stdout

    def _read_freedesktop(self) -> Tuple[Optional[bool], Any]:
        """FreeDesktop D-Bus property 'Inhibited'"""
        if self.inhibit_cookie is not None:
            return True, str(self.inhibit_cookie)
        if self.conn is None:
            return None, ""
        try:
            msg = new_method_call(
                self.prop_addr,
                "Get",
                "ss",
                ("org.freedesktop.Notifications", "Inhibited"),
            )
            reply = self.conn.send_and_get_reply(msg, timeout=2.0)
            if reply.body and len(reply.body) > 0:
                val = reply.body[0][1]
                if isinstance(val, bool):
                    return val, val
        except Exception as err:
            logger.debug("Error reading Inhibited DBus property: %s", err)
        return None, ""

    @staticmethod
    def _read_syscommand(command: str) -> Tuple[Optional[bool], Any]:
        stdout, _, rc = syscommand(command, ignore_errors=True)
        if rc != 0 or not stdout:
            return None, stdout
        return Addon._parse_bool(stdout), stdout

    def _set_state(self, enabled: bool) -> None:
        """Sets DND state using the selected backend"""
        if self.backend == "kde":
            self._set_kde(enabled)
        elif self.backend == "gnome":
            self._set_gnome(enabled)
        elif self.backend == "swaync":
            flag = "-s" if enabled else "-u"
            syscommand(f"swaync-client -d {flag}", ignore_errors=True)
        elif self.backend == "dunst":
            val = "true" if enabled else "false"
            syscommand(f"dunstctl set-paused {val}", ignore_errors=True)
        elif self.backend == "mako":
            cmd = "mode -a dnd" if enabled else "mode -r dnd"
            syscommand(f"makoctl {cmd}", ignore_errors=True)
        else:
            self._set_freedesktop(enabled)

    def _set_kde(self, enabled: bool) -> None:
        until_val = _KDE_UNTIL_ON if enabled else _KDE_UNTIL_OFF
        syscommand(
            f"{self.kwriteconfig} --file plasmanotifyrc --group DoNotDisturb "
            f'--key Until "{until_val}"',
            ignore_errors=True,
        )

    @staticmethod
    def _set_gnome(enabled: bool) -> None:
        val = "false" if enabled else "true"
        syscommand(
            f"gsettings set org.gnome.desktop.notifications show-banners {val}",
            ignore_errors=True,
        )

    def _set_freedesktop(self, enabled: bool) -> None:
        """FreeDesktop D-Bus Inhibit / UnInhibit via persistent connection"""
        if self.conn is None:
            self._init_dbus()
        if self.conn is None:
            return

        if enabled:
            if self.inhibit_cookie is None:
                try:
                    msg = new_method_call(
                        self.notif_addr,
                        "Inhibit",
                        "ssa{sv}",
                        ("LNXlink", "Do Not Disturb from Home Assistant", {}),
                    )
                    reply = self.conn.send_and_get_reply(msg, timeout=2.0)
                    if reply.body and len(reply.body) > 0:
                        self.inhibit_cookie = reply.body[0]
                        logger.info(
                            "DND inhibited via D-Bus cookie %s", self.inhibit_cookie
                        )
                except Exception as err:
                    logger.debug("Failed to inhibit DND via D-Bus: %s", err)
        else:
            if self.inhibit_cookie is not None:
                try:
                    msg = new_method_call(
                        self.notif_addr,
                        "UnInhibit",
                        "u",
                        (self.inhibit_cookie,),
                    )
                    self.conn.send_message(msg)
                    logger.info(
                        "DND uninhibited via D-Bus cookie %s", self.inhibit_cookie
                    )
                except Exception as err:
                    logger.debug("Failed to uninhibit DND via D-Bus: %s", err)
                finally:
                    self.inhibit_cookie = None

    @staticmethod
    def _parse_bool(value) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "enabled", "(<true>,)"}:
            return True
        if text in {"0", "false", "no", "off", "disabled", "(<false>,)"}:
            return False
        return None
