"""Toggle and report Night Light status"""
import logging
from shutil import which
from typing import Any, Dict, Optional, Tuple

from jeepney import DBusAddress, MessageType, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import DBusErrorResponse

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module for Night Light / Blue Light Filter"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Night Light"
        self.lnxlink = lnxlink
        self.inhibit_cookie = None
        self.conn = None

        backend_setup = self._setup_backend()
        if backend_setup is None:
            raise RuntimeError("No supported Night Light backend found")
        self.backend, self._read_state, self._set_state = backend_setup
        logger.debug("Night Light backend selected: %s", self.backend)

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

    def _setup_backend(self) -> Optional[Tuple[str, Any, Any]]:
        """Detect available desktop environment and return (backend, read_func, set_func)"""
        # 1. KDE Plasma (KWin NightLight via D-Bus)
        self._init_dbus()
        if self._kwin_available():
            return "kde", self._read_kde, self._set_kde

        # 2. GNOME (gsettings)
        if which("gsettings") is not None:
            return "gnome", self._read_gnome, self._set_gnome

        # 3. Running process (gammastep / redshift)
        if self._nightlight_process() is not None:
            return (
                "process",
                self._read_process,
                lambda _: logger.warning(
                    "Night Light control is not supported for backend: %s", self.backend
                ),
            )

        return None

    def _init_dbus(self):
        """Initialize session D-Bus connection"""
        if self.conn is not None:
            return
        try:
            self.conn = open_dbus_connection(bus="SESSION")
        except Exception as err:
            logger.debug(
                "Failed to connect to session D-Bus in Night Light module: %s", err
            )
            self.conn = None

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

    def _kwin_get_all(self) -> Dict[str, Any]:
        """Fetch all properties from the KWin NightLight D-Bus interface"""
        kwin_prop_addr = DBusAddress(
            "/org/kde/KWin/NightLight",
            bus_name="org.kde.KWin.NightLight",
            interface="org.freedesktop.DBus.Properties",
        )
        msg = new_method_call(
            kwin_prop_addr,
            "GetAll",
            "s",
            ("org.kde.KWin.NightLight",),
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

    def _set_kde(self, enabled: bool) -> None:
        """Inhibit/Uninhibit KWin NightLight via D-Bus"""
        if self.conn is None:
            return
        kwin_addr = DBusAddress(
            "/org/kde/KWin/NightLight",
            bus_name="org.kde.KWin.NightLight",
            interface="org.kde.KWin.NightLight",
        )
        try:
            if not enabled:
                msg = new_method_call(kwin_addr, "inhibit")
                reply = self.conn.send_and_get_reply(msg, timeout=2.0)
                if reply.header.message_type == MessageType.error:
                    raise DBusErrorResponse(reply)
                if reply.body and len(reply.body) > 0:
                    self.inhibit_cookie = reply.body[0]
            elif self.inhibit_cookie is not None:
                msg = new_method_call(
                    kwin_addr, "uninhibit", "u", (self.inhibit_cookie,)
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
