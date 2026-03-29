"""Manage Linux services; check status, start, or stop specific units"""
import logging
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "SystemD"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings("systemd", [])
        raw_services = self.lnxlink.config["settings"].get("systemd", [])
        raw_services = [] if raw_services is None else raw_services
        if not raw_services:
            logger.info("No systemd settings found on configuration.")

        # Normalise entries: a plain string is treated as a system service.
        # A dict must have at least a 'name' key; 'user: true' marks user services.
        self.services = self._parse_services(raw_services)

        # System bus – always available
        self.system_bus = open_dbus_connection(bus="SYSTEM")

        # Session bus – used for user services; opened lazily so that the
        # module still loads when there is no graphical session.
        self._session_bus = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_services(self, raw):
        """Return a list of normalised service dicts.

        Each dict has:
            name  – the unit name (e.g. 'foo.service')
            user  – True if this is a user-scoped service
            label – display name used for the HA entity
        """
        parsed = []
        for entry in raw:
            if isinstance(entry, str):
                parsed.append({"name": entry, "user": False})
            elif isinstance(entry, dict):
                name = entry.get("name", "")
                if not name:
                    logger.warning("Systemd entry missing 'name' key: %s", entry)
                    continue
                parsed.append({"name": name, "user": bool(entry.get("user", False))})
            else:
                logger.warning("Unrecognised systemd entry type: %s", type(entry))
        return parsed

    @staticmethod
    def _service_label(service):
        """Human-readable label for a service dict."""
        base = service["name"].replace(".service", "")
        return f"User {base}" if service["user"] else base

    @staticmethod
    def _dbus_escape(service_name):
        """Escape a unit name for use in a D-Bus object path."""
        return (
            service_name.replace("-", "_2d")
            .replace(".", "_2e")
            .replace("\\", "_5c")
            .replace("@", "_40")
        )

    def _session_bus_connection(self):
        """Return the SESSION bus, opening it on first use.

        Returns None if the session bus is unavailable.
        """
        if self._session_bus is not None:
            return self._session_bus
        try:
            self._session_bus = open_dbus_connection(bus="SESSION")
            logger.debug("Opened SESSION D-Bus connection for user services")
        except Exception as err:
            logger.warning("Could not open SESSION bus: %s", err)
            self._session_bus = None
        return self._session_bus

    # ------------------------------------------------------------------
    # D-Bus queries
    # ------------------------------------------------------------------

    def _get_active_state_dbus(self, bus, service_name):
        """Query ActiveState via D-Bus. Returns the state string or None on failure."""
        dbus_service = self._dbus_escape(service_name)
        try:
            msg = new_method_call(
                DBusAddress(
                    object_path=f"/org/freedesktop/systemd1/unit/{dbus_service}",
                    bus_name="org.freedesktop.systemd1",
                    interface="org.freedesktop.DBus.Properties",
                ),
                "Get",
                "ss",
                ("org.freedesktop.systemd1.Unit", "ActiveState"),
            )
            reply = bus.send_and_get_reply(msg)
            return reply.body[0][1]
        except Exception as err:
            logger.debug("D-Bus ActiveState query failed for %s: %s", service_name, err)
            return None

    def _dbus_action(self, bus, service_name, action):
        """Send StartUnit / StopUnit via D-Bus. Returns True on success."""
        try:
            msg = new_method_call(
                DBusAddress(
                    object_path="/org/freedesktop/systemd1",
                    bus_name="org.freedesktop.systemd1",
                    interface="org.freedesktop.systemd1.Manager",
                ),
                action,
                "ss",
                (service_name, "replace"),
            )
            bus.send(msg)
            return True
        except Exception as err:
            logger.debug("D-Bus action %s failed for %s: %s", action, service_name, err)
            return False

    # ------------------------------------------------------------------
    # Per-service status / control
    # ------------------------------------------------------------------

    @staticmethod
    def _check_cli_status(stdout, service_name, user):
        """Interpret `systemctl is-active` output.

        Returns 'ON', 'OFF', or raises RuntimeError when the unit is not found.
        systemctl outputs 'unknown' for units that do not exist at all and
        'not-found' when the unit file is missing from the unit path.
        """
        state = stdout.strip()
        if state in ("unknown", "not-found"):
            scope = "user" if user else "system"
            raise RuntimeError(
                f"Systemd {scope} service '{service_name}' was not found "
                f"(systemctl reported: '{state}')"
            )
        return "ON" if state == "active" else "OFF"

    def _get_status(self, service):
        """Return 'ON' or 'OFF' for a single service dict."""
        name = service["name"]

        if service["user"]:
            # Try SESSION bus first
            session = self._session_bus_connection()
            if session is not None:
                state = self._get_active_state_dbus(session, name)
                if state is not None:
                    if state == "not-found":
                        raise RuntimeError(
                            f"Systemd user service '{name}' was not found "
                            f"(D-Bus reported: '{state}')"
                        )
                    return "ON" if state == "active" else "OFF"

            # Fallback: systemctl --user
            stdout, _, _ = syscommand(
                f"systemctl --user is-active {name}", ignore_errors=True
            )
            return self._check_cli_status(stdout, name, user=True)

        # System service – use the SYSTEM bus
        state = self._get_active_state_dbus(self.system_bus, name)
        if state is not None:
            if state == "not-found":
                raise RuntimeError(
                    f"Systemd system service '{name}' was not found "
                    f"(D-Bus reported: '{state}')"
                )
            return "ON" if state == "active" else "OFF"

        # Fallback: systemctl (may need sudo for some units)
        stdout, _, _ = syscommand(f"systemctl is-active {name}", ignore_errors=True)
        return self._check_cli_status(stdout, name, user=False)

    def _control(self, service, turn_on):
        """Start or stop a service. Tries D-Bus first, then CLI fallback."""
        name = service["name"]
        action = "StartUnit" if turn_on else "StopUnit"
        cli_action = "start" if turn_on else "stop"

        if service["user"]:
            session = self._session_bus_connection()
            if session is not None and self._dbus_action(session, name, action):
                return
            # Fallback
            logger.info("Falling back to systemctl --user %s %s", cli_action, name)
            syscommand(f"systemctl --user {cli_action} {name}")
        else:
            if self._dbus_action(self.system_bus, name, action):
                return
            # Fallback
            logger.info("Falling back to sudo systemctl %s %s", cli_action, name)
            syscommand(f"sudo -n systemctl {cli_action} {name}")

    # ------------------------------------------------------------------
    # Addon interface
    # ------------------------------------------------------------------

    def get_info(self):
        """Gather information from the system"""
        info = {}
        for service in self.services:
            label = self._service_label(service)
            try:
                info[label] = self._get_status(service)
            except Exception as err:
                logger.error("Error getting status for %s: %s", service["name"], err)
                info[label] = "OFF"
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for service in self.services:
            label = self._service_label(service)
            discovery_info[f"Systemd {label}"] = {
                "type": "switch",
                "icon": "mdi:application-cog",
                "value_template": f"{{{{ value_json.get('{label}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        # Reconstruct the label from the topic slug so we can look up the service.
        # topic[1] looks like "systemd_user_foo" or "systemd_foo".
        slug = topic[1]  # e.g. "systemd_user_foo_service" → strip prefix below
        slug = slug[8:]  # strip leading "systemd_"

        for service in self.services:
            label = self._service_label(service)
            label_slug = label.lower().replace(" ", "_").replace("-", "_")
            if label_slug == slug:
                self._control(service, turn_on=data.lower() == "on")
                return

        logger.error("No matching service found for topic slug: %s", slug)

    def __del__(self):
        """Close the connections"""
        if hasattr(self, "system_bus"):
            try:
                self.system_bus.close()
            except Exception:
                pass
        if hasattr(self, "_session_bus") and self._session_bus is not None:
            try:
                self._session_bus.close()
            except Exception:
                pass
