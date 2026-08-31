"""Toggle and report Night Light status across desktop environments"""
import logging
from shutil import which
from typing import Any, Dict, Optional, Tuple

from jeepney import DBusAddress, MessageType, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import DBusErrorResponse

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")

KWIN_NIGHTLIGHT_SERVICE = "org.kde.KWin.NightLight"
KWIN_NIGHTLIGHT_PATH = "/org/kde/KWin/NightLight"


class Addon:
    """Addon module for Night Light / Blue Light Filter"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Night Light"
        self.lnxlink = lnxlink
        self.inhibit_cookie = None
        self.conn = None
        self.kwin_addr = DBusAddress(
            KWIN_NIGHTLIGHT_PATH,
            bus_name=KWIN_NIGHTLIGHT_SERVICE,
            interface=KWIN_NIGHTLIGHT_SERVICE,
        )
        self.kwin_prop_addr = DBusAddress(
            KWIN_NIGHTLIGHT_PATH,
            bus_name=KWIN_NIGHTLIGHT_SERVICE,
            interface="org.freedesktop.DBus.Properties",
        )
        try:
            self.conn = open_dbus_connection(bus="SESSION")
        except Exception as err:
            logger.debug(
                "Failed to connect to session D-Bus in Night Light module: %s", err
            )
            self.conn = None

        # Decide once which backend to use, so we don't spawn `which`/`pgrep`
        # subprocesses or D-Bus probes on every get_info()/start_control() call.
        self.backend = self._detect_backend()
        if self.backend is None:
            raise RuntimeError("No supported Night Light backend found")
        logger.debug("Night Light backend selected: %s", self.backend)

    def _detect_backend(self) -> Optional[str]:
        """Pick a single Night Light backend, in priority order"""
        if self._kwin_available():
            return "kde"
        if which("gsettings") is not None:
            return "gnome"
        if self._nightlight_process() is not None:
            return "process"
        return None

    def _kwin_available(self) -> bool:
        if self.conn is None:
            return False
        try:
            self._kwin_get_all()
            return True
        except (OSError, DBusErrorResponse):
            return False

    @staticmethod
    def _nightlight_process() -> Optional[str]:
        stdout, _, rc = syscommand(
            "pgrep -x gammastep || pgrep -x redshift", ignore_errors=True
        )
        if rc == 0 and stdout.strip():
            return stdout.strip()
        return None

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Night Light": {
                "type": "switch",
                "icon": "mdi:weather-night",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        enabled, extra_attrs = self._read_state()
        status = None
        if enabled is True:
            status = "ON"
        elif enabled is False:
            status = "OFF"

        attrs = {"source": self.backend}
        attrs.update(extra_attrs)

        return {
            "status": status,
            "attributes": attrs,
        }

    def start_control(self, topic, data):
        """Control system"""
        enabled = self._parse_bool(data)
        if enabled is None:
            logger.error("Expected ON/OFF, received: %s", data)
            return
        self._set_state(enabled)

    def _read_state(self) -> Tuple[Optional[bool], Dict[str, Any]]:
        if self.backend == "kde":
            return self._read_kde()
        if self.backend == "gnome":
            return self._read_gnome()
        return self._read_process()

    def _kwin_get_all(self) -> Dict[str, Any]:
        """Fetch all properties from the KWin NightLight D-Bus interface"""
        msg = new_method_call(
            self.kwin_prop_addr,
            "GetAll",
            "s",
            (KWIN_NIGHTLIGHT_SERVICE,),
        )
        reply = self.conn.send_and_get_reply(msg, timeout=2.0)
        if reply.header.message_type == MessageType.error:
            raise DBusErrorResponse(reply)
        props = {}
        if reply.body and len(reply.body) > 0:
            for key, (_, value) in reply.body[0].items():
                props[key] = value
        return props

    def _read_kde(self) -> Tuple[Optional[bool], Dict[str, Any]]:
        try:
            props = self._kwin_get_all()
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to read KWin NightLight properties: %s", err)
            return None, {}

        running = bool(props.get("running"))
        inhibited = bool(props.get("inhibited"))
        daylight = bool(props.get("daylight"))
        is_active = running and not inhibited

        attrs = {
            "running": running,
            "inhibited": inhibited,
            "daylight": daylight,
        }
        current_temperature = props.get("currentTemperature")
        if current_temperature is not None:
            attrs["current_temperature"] = int(current_temperature)

        return is_active, attrs

    def _read_gnome(self) -> Tuple[Optional[bool], Dict[str, Any]]:
        stdout, _, rc = syscommand(
            "gsettings get org.gnome.settings-daemon.plugins.color night-light-enabled",
            ignore_errors=True,
        )
        if rc != 0 or not stdout:
            return None, {}
        return self._parse_bool(stdout), {"raw": stdout}

    def _read_process(self) -> Tuple[Optional[bool], Dict[str, Any]]:
        pid = self._nightlight_process()
        if pid is None:
            return False, {}
        return True, {"pid": pid}

    def _set_state(self, enabled):
        if self.backend == "kde":
            self._set_kde(enabled)
        elif self.backend == "gnome":
            self._set_gnome(enabled)
        else:
            logger.warning(
                "Night Light control is not supported for backend: %s", self.backend
            )

    def _set_kde(self, enabled: bool) -> None:
        """Inhibit/Uninhibit KWin NightLight via D-Bus"""
        try:
            if not enabled:
                msg = new_method_call(self.kwin_addr, "inhibit")
                reply = self.conn.send_and_get_reply(msg, timeout=2.0)
                if reply.header.message_type == MessageType.error:
                    raise DBusErrorResponse(reply)
                if reply.body and len(reply.body) > 0:
                    self.inhibit_cookie = reply.body[0]
            elif self.inhibit_cookie is not None:
                msg = new_method_call(
                    self.kwin_addr, "uninhibit", "u", (self.inhibit_cookie,)
                )
                reply = self.conn.send_and_get_reply(msg, timeout=2.0)
                if reply.header.message_type == MessageType.error:
                    raise DBusErrorResponse(reply)
                self.inhibit_cookie = None
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to toggle KWin NightLight via D-Bus: %s", err)

    @staticmethod
    def _set_gnome(enabled: bool) -> None:
        value = "true" if enabled else "false"
        syscommand(
            f"gsettings set org.gnome.settings-daemon.plugins.color "
            f"night-light-enabled {value}",
            ignore_errors=True,
        )

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "enabled"}:
            return True
        if text in {"0", "false", "no", "off", "disabled"}:
            return False
        return None
