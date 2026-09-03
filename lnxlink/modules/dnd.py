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


class Addon:
    """Addon module for Do Not Disturb (DND) notification inhibition"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Do Not Disturb"
        self.lnxlink = lnxlink
        self.inhibit_cookie: Optional[int] = None
        self.conn = None

        backend_setup = self._setup_backend()
        if backend_setup is None:
            raise RuntimeError("No supported Do Not Disturb backend found")
        self.backend, self._read_state, self._set_state = backend_setup
        logger.debug("DND backend selected: %s", self.backend)

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

    def _setup_backend(self) -> Optional[Tuple[str, Any, Any]]:
        """Detect available desktop environment and return (backend, read_func, set_func)"""
        # 1. KDE Plasma backend
        kwriteconfig = which("kwriteconfig6") or which("kwriteconfig5")
        if kwriteconfig is not None:
            return (
                "kde",
                self._read_kde,
                lambda en: syscommand(
                    f"{kwriteconfig} --file plasmanotifyrc --group DoNotDisturb "
                    f'--key Until "{"2037,1,1,0,0,0.0" if en else ""}"',
                    ignore_errors=True,
                ),
            )

        # 2. Table-driven CLI backends
        cli_backends = {
            "gnome": {
                "bin": "gsettings",
                "read": "gsettings get org.gnome.desktop.notifications show-banners",
                "parse": lambda out: (
                    not self._parse_bool(out)
                    if self._parse_bool(out) is not None
                    else None
                ),
                "set": lambda en: (
                    "gsettings set org.gnome.desktop.notifications show-banners "
                    + ("false" if en else "true")
                ),
            },
            "swaync": {
                "bin": "swaync-client",
                "read": "swaync-client -D",
                "parse": self._parse_bool,
                "set": lambda en: f"swaync-client -d {'-s' if en else '-u'}",
            },
            "dunst": {
                "bin": "dunstctl",
                "read": "dunstctl is-paused",
                "parse": self._parse_bool,
                "set": lambda en: f"dunstctl set-paused {'true' if en else 'false'}",
            },
            "mako": {
                "bin": "makoctl",
                "read": "makoctl mode",
                "parse": lambda out: "dnd" in out.lower(),
                "set": lambda en: f"makoctl mode {'-a' if en else '-r'} dnd",
            },
        }

        for name, cfg in cli_backends.items():
            if which(cfg["bin"]) is not None:
                return (
                    name,
                    lambda c=cfg: self._read_cli(c["read"], c["parse"]),
                    lambda en, c=cfg: syscommand(c["set"](en), ignore_errors=True),
                )

        # 3. FreeDesktop D-Bus backend fallback
        self._init_dbus()
        if self.conn is not None:
            return "freedesktop", self._read_freedesktop, self._set_freedesktop

        return None

    def _init_dbus(self):
        """Initialize session D-Bus connection for persistent notification inhibition"""
        try:
            self.conn = open_dbus_connection(bus="SESSION")
        except Exception as err:
            logger.debug("Failed to connect to session D-Bus in DND module: %s", err)
            self.conn = None

    @staticmethod
    def _read_cli(command: str, parser) -> Tuple[Optional[bool], Any]:
        """Execute a CLI command and parse output"""
        stdout, _, rc = syscommand(command, ignore_errors=True)
        if rc != 0 or not stdout:
            return None, stdout
        return parser(stdout), stdout

    @staticmethod
    def _read_kde() -> Tuple[Optional[bool], Any]:
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

    def _read_freedesktop(self) -> Tuple[Optional[bool], Any]:
        """FreeDesktop D-Bus property 'Inhibited'"""
        if self.inhibit_cookie is not None:
            return True, str(self.inhibit_cookie)
        if self.conn is None:
            return None, ""
        try:
            prop_addr = DBusAddress(
                "/org/freedesktop/Notifications",
                bus_name="org.freedesktop.Notifications",
                interface="org.freedesktop.DBus.Properties",
            )
            msg = new_method_call(
                prop_addr,
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

    def _set_freedesktop(self, enabled: bool) -> None:
        """FreeDesktop D-Bus Inhibit / UnInhibit via persistent connection"""
        if self.conn is None:
            return

        notif_addr = DBusAddress(
            "/org/freedesktop/Notifications",
            bus_name="org.freedesktop.Notifications",
            interface="org.freedesktop.Notifications",
        )

        if enabled:
            if self.inhibit_cookie is None:
                try:
                    msg = new_method_call(
                        notif_addr,
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
                        notif_addr,
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
