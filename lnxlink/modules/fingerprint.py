"""Connect a R503 fingerprint scanner via UART on a Raspberry PI and control it."""

import copy
import json
import datetime
import logging
import os
import threading
import time
from typing import Any

from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """LNXlink addon wrapper."""

    DEFAULT_SETTINGS = {
        # "serial" matches the working project.
        "serial": "/dev/serial0",
        "baudrate": 57600,
        "password": "0x00000000",
        "minimum_confidence": 0,
        "delete_all_enabled": False,
        "change_password_enabled": False,
        "led_enabled": True,
    }

    def __init__(self, lnxlink):
        """Set up the fingerprint addon."""
        self.name = "fingerprint"
        self.lnxlink = lnxlink

        if not self._is_raspberry():
            raise SystemError("Not supported on non-Raspberry Pi devices")

        self.settings = self._settings()

        self.serial = import_install_package("pyserial", syspackage="serial")
        self.adafruit_fingerprint = import_install_package(
            "adafruit-circuitpython-fingerprint",
            syspackage="adafruit_fingerprint",
        )

        self.fingerprint = Fingerprint(
            settings=self.settings,
            serial_module=self.serial,
            adafruit_fingerprint=self.adafruit_fingerprint,
        )
        self.fingerprint.found_finger = self.found_finger
        self.fingerprint.updated_templates = self.updated_templates
        self.fingerprint.unauthorized = self.unauthorized
        self.fingerprint.state_changed = self.state_changed
        self.fingerprint.error = self.error

    def get_info(self):
        """Return cached state only. UART is owned by the scan thread."""
        return self.fingerprint.state()

    def exposed_controls(self):
        """Expose entities to Home Assistant."""
        controls = {
            "Fingerprint Status": {
                "type": "sensor",
                "icon": "mdi:fingerprint",
                "value_template": "{{ value_json.status }}",
            },
            "Fingerprint Mode": {
                "type": "sensor",
                "icon": "mdi:tune",
                "value_template": "{{ value_json.mode }}",
            },
            "Fingerprint Last ID": {
                "type": "sensor",
                "icon": "mdi:identifier",
                "value_template": "{{ value_json.last_id }}",
            },
            "Fingerprint Last Authorized": {
                "type": "sensor",
                "icon": "mdi:clock-check-outline",
                "value_template": "{{ value_json.last_authorized_time }}",
                "device_class": "timestamp",
            },
            "Fingerprint Confidence": {
                "type": "sensor",
                "icon": "mdi:shield-check",
                "value_template": "{{ value_json.confidence }}",
                "state_class": "measurement",
            },
            "Fingerprint Minimum Confidence": {
                "type": "sensor",
                "icon": "mdi:shield-lock-outline",
                "value_template": "{{ value_json.minimum_confidence }}",
                "entity_category": "diagnostic",
            },
            "Fingerprint Password Warning": {
                "type": "sensor",
                "icon": "mdi:form-textbox-password",
                "value_template": "{{ value_json.password_update_warning }}",
                "entity_category": "diagnostic",
            },
            "Fingerprint Template Count": {
                "type": "sensor",
                "icon": "mdi:counter",
                "value_template": "{{ value_json.template_count }}",
                "unit_of_measurement": "templates",
                "state_class": "measurement",
            },
            "Fingerprint Library Size": {
                "type": "sensor",
                "icon": "mdi:database",
                "value_template": "{{ value_json.library_size }}",
                "unit_of_measurement": "templates",
                "entity_category": "diagnostic",
            },
            "Fingerprint Read Errors": {
                "type": "sensor",
                "icon": "mdi:alert-circle-outline",
                "value_template": "{{ value_json.read_error_count }}",
                "entity_category": "diagnostic",
                "state_class": "measurement",
            },
            "Fingerprint Scan": {
                "type": "button",
                "icon": "mdi:fingerprint",
            },
            "Fingerprint Enroll ID": {
                "type": "text",
                "icon": "mdi:account-plus",
            },
            "Fingerprint Delete ID": {
                "type": "text",
                "icon": "mdi:delete",
            },
        }

        if self.settings.get("delete_all_enabled", False):
            controls["Fingerprint Delete All"] = {
                "type": "button",
                "icon": "mdi:delete-alert",
            }

        if self.settings.get("change_password_enabled", False):
            controls["Fingerprint Change Password"] = {
                "type": "text",
                "icon": "mdi:form-textbox-password",
                "entity_category": "config",
            }

        return controls

    def start_control(self, topic, data):
        """Route commands using the same set_mode model as the working project."""
        command = topic[-1] if isinstance(topic, list) and topic else str(topic)
        command = command.lower().replace(" ", "_")
        payload = self._control_value(data)

        if command in ("fingerprint_scan", "scan"):
            self.fingerprint.set_mode("scan")
        elif command in ("fingerprint_enroll_id", "enroll_id", "enroll"):
            self.fingerprint.set_mode("enroll", self._get_location(payload))
        elif command in ("fingerprint_delete_id", "delete_id", "delete"):
            self.fingerprint.set_mode("delete", self._get_location(payload))
        elif command in ("fingerprint_delete_all", "delete_all", "empty"):
            self._handle_delete_all(payload)
        elif command in (
            "fingerprint_change_password",
            "change_password",
            "password",
        ):
            self._handle_change_password(payload)

    def _handle_delete_all(self, payload):
        """Handle the dangerous delete-all command when explicitly enabled."""
        if not self.settings.get("delete_all_enabled", False):
            logger.error("Fingerprint delete all is disabled in settings.")
            return

        if self._is_truthy(payload):
            self.fingerprint.set_mode("empty")

    def _handle_change_password(self, payload):
        """Handle password-change command when explicitly enabled."""
        if self.settings.get("change_password_enabled", False):
            self.fingerprint.change_password(self._get_password(payload))
        else:
            logger.error("Fingerprint password change is disabled in settings.")

    def publish_state(self, action=None):
        """Publish the current fingerprint state to the main module topic."""
        payload = (
            self.fingerprint.event_payload(action)
            if action
            else self.fingerprint.state()
        )
        self.lnxlink.run_module(self.name, payload)

    def found_finger(self, finger_id, confidence):
        """Handle a successful fingerprint authorization callback."""
        self.publish_state("matched")

    def unauthorized(self):
        """Handle an unauthorized fingerprint scan callback."""
        self.publish_state("unauthorized")

    def updated_templates(self):
        """Handle template list/count update callback."""
        self.publish_state("templates_updated")

    def state_changed(self, action):
        """Handle generic fingerprint state change callback."""
        self.publish_state(action)

    def error(self, stage, err):
        """Handle fingerprint error callback."""
        payload = self.fingerprint.event_payload("error")
        payload["stage"] = stage
        payload["error"] = str(err)
        self.lnxlink.run_module(self.name, payload)

    @staticmethod
    def _is_raspberry():
        """Return whether the host looks like a Raspberry Pi."""
        model = ""
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", "r", encoding="UTF-8") as device_model:
                model = device_model.read()
        return "raspberry" in model.lower()

    def _settings(self) -> dict:
        """Return registered fingerprint settings."""
        self.lnxlink.add_settings(self.name, copy.deepcopy(self.DEFAULT_SETTINGS))
        config = getattr(self.lnxlink, "config", None)
        if not isinstance(config, dict):
            raise TypeError(
                "LNXlink config object is not available after add_settings()."
            )

        settings = config.get("settings")
        if not isinstance(settings, dict):
            raise KeyError("LNXlink config does not contain a 'settings' section.")

        fingerprint_settings = settings.get(self.name)
        if not isinstance(fingerprint_settings, dict):
            raise KeyError("LNXlink did not register settings for 'fingerprint'.")

        return fingerprint_settings

    @staticmethod
    def _control_value(data: Any) -> Any:
        """Decode a control payload from LNXlink."""
        if isinstance(data, (dict, list)):
            return data
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        if not isinstance(data, str):
            return data

        data = data.strip()
        if not data:
            return data

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    @staticmethod
    def _get_location(payload: Any) -> int:
        """Extract a template location from a command payload."""
        if isinstance(payload, dict):
            return int(payload.get("id", payload.get("location")))
        return int(payload)

    @staticmethod
    def _get_password(payload: Any) -> Any:
        """Extract a password value from a command payload."""
        if isinstance(payload, dict):
            return payload.get("new_password", payload.get("password"))
        return payload

    @staticmethod
    def _is_truthy(payload: Any) -> bool:
        """Return whether a command payload is truthy."""
        if isinstance(payload, str):
            return payload.lower() in ("true", "yes", "on", "1", "delete", "empty")
        return bool(payload)


class Fingerprint:  # pylint: disable=too-many-instance-attributes
    """Fingerprint service logic adapted from mqtt_fingerprint_pi."""

    LEDCOLOR_RED = 1
    LEDCOLOR_BLUE = 2
    LEDCOLOR_PURPLE = 3

    LEDMODE_BREATH = 1
    LEDMODE_BLINK = 2
    LEDMODE_STILL = 3
    LEDMODE_OFF = 4

    SERIAL_TIMEOUT = 1
    ENROLL_TIMEOUT = 10
    RECONNECT_INTERVAL = 5
    MAX_READ_ERRORS = 5
    SCAN_SLEEP = 0.01

    def __init__(self, settings, serial_module, adafruit_fingerprint):
        """Set up the fingerprint sensor service."""
        self.settings = settings
        self.serial_module = serial_module
        self.adafruit_fingerprint = adafruit_fingerprint

        self.serial_port = self.settings.get("serial", "/dev/serial0")
        self.baudrate = int(self.settings.get("baudrate", 57600))
        self.timeout = self.SERIAL_TIMEOUT
        self.password = self.parse_password(self.settings.get("password", "0x00000000"))
        self.enroll_timeout = self.ENROLL_TIMEOUT
        self.reconnect_interval = self.RECONNECT_INTERVAL
        self.max_read_errors = self.MAX_READ_ERRORS
        self.minimum_confidence = int(self.settings.get("minimum_confidence", 0))
        self.scan_sleep = self.SCAN_SLEEP
        self.led_enabled = bool(self.settings.get("led_enabled", True))

        self.found_finger = lambda finger_id, confidence: None
        self.updated_templates = lambda: None
        self.unauthorized = lambda: None
        self.state_changed = lambda action: None
        self.error = lambda stage, err: None

        self.mode = "scan"
        self.connected = False
        self.status = "not initialized"
        self.finger_present = False
        self.last_id = None
        self.confidence = None
        self.last_authorized_time = None
        self.last_authorized_id = None
        self.last_authorized_confidence = None
        self.last_update_time = None
        self.restart_requires_password_update = False
        self.password_update_warning = None
        self.matched = False
        self.templates = []
        self.template_count = 0
        self.library_size = None
        self.security_level = None
        self.last_error = None
        self.read_error_count = 0

        self.uart = None
        self.finger = None
        self._consecutive_read_errors = 0
        self._last_connect_attempt = 0

        threading.Thread(target=self.get_fingerprint, daemon=True).start()

    def connect(self, force=False):
        """Connect or reconnect to the fingerprint sensor."""
        now = time.time()
        if not force and self.finger is not None and self.connected:
            return True

        if not force and now - self._last_connect_attempt < self.reconnect_interval:
            return False

        self._last_connect_attempt = now
        self.disconnect()

        try:
            self.status = "connecting"
            self.publish_state("connecting")
            self.uart = self.serial_module.Serial(
                self.serial_port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            self.finger = self.adafruit_fingerprint.Adafruit_Fingerprint(
                self.uart,
                passwd=self.password,
            )
            self.connected = True
            self.status = "connected"
            self.last_error = None
            self._consecutive_read_errors = 0
            self.get_sensor_info()
            self.set_ledcolor(action="reset")
            self.publish_state("connected")
            logger.info("Fingerprint sensor connected on %s", self.serial_port)
            return True
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.connected = False
            self.status = "connection failed"
            self.last_error = str(err)
            self.finger = None
            self._safe_close_uart()
            logger.error("Fingerprint connection failed: %s", err)
            self.error("connect", err)
            return False

    def disconnect(self):
        """Mark the sensor disconnected and close the UART handle."""
        self.connected = False
        self.finger = None
        self._safe_close_uart()

    def reconnect(self, reason):
        """Force a clean reconnect after repeated sensor errors."""
        logger.error("Fingerprint reconnecting: %s", reason)
        self.status = "reconnecting"
        self.connected = False
        self.last_error = str(reason)
        self.publish_state("reconnecting")
        self.disconnect()
        return self.connect(force=True)

    def _safe_close_uart(self):
        """Close the UART handle without raising from cleanup."""
        if self.uart is None:
            return
        try:
            self.uart.close()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        self.uart = None

    def set_mode(self, mode, args=-1):
        """Use the same mode-switch command model as the working project."""
        if args == "" or args is None:
            args = -1
        args = int(args)

        if self.mode != mode:
            logger.info("Fingerprint changed mode to %s", mode)
            self.mode = mode
            self.publish_state(f"mode_{mode}")

            if mode in ("enroll", "delete", "empty") and not self.connect(force=True):
                self.mode = "scan"
                return
            if mode == "enroll":
                self.enroll_new(args)
                self.mode = "scan"
            elif mode == "delete":
                self.delete_model(args)
                self.mode = "scan"
            elif mode == "empty":
                self.empty_library()
                self.mode = "scan"
            elif mode == "scan":
                self.mode = "scan"

    def get_sensor_info(self):
        """Refresh sensor information exactly like the working service."""
        if self.finger is None:
            raise RuntimeError("Fingerprint sensor is not connected")
        if self.finger.read_templates() != self.adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        if self.finger.count_templates() != self.adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        if self.finger.read_sysparam() != self.adafruit_fingerprint.OK:
            raise RuntimeError("Failed to get system parameters")

        self.templates = list(getattr(self.finger, "templates", []))
        self.template_count = getattr(self.finger, "template_count", 0)
        self.library_size = getattr(self.finger, "library_size", None)
        self.security_level = getattr(self.finger, "security_level", None)
        self.updated_templates()

        return {
            "templates": self.templates,
            "size": self.library_size,
        }

    def state(self):
        """Return cached state for LNXlink."""
        return {
            "connected": self.connected,
            "status": self.status,
            "mode": self.mode,
            "finger_present": self.finger_present,
            "matched": self.matched,
            "last_id": self.last_id,
            "confidence": self.confidence,
            "minimum_confidence": self.minimum_confidence,
            "last_authorized_time": self.last_authorized_time,
            "last_authorized_id": self.last_authorized_id,
            "last_authorized_confidence": self.last_authorized_confidence,
            "last_update_time": self.last_update_time,
            "templates": self.templates,
            "template_count": self.template_count,
            "library_size": self.library_size,
            "security_level": self.security_level,
            "serial": self.serial_port,
            "baudrate": self.baudrate,
            "error": self.last_error,
            "read_error_count": self.read_error_count,
            "consecutive_read_errors": self._consecutive_read_errors,
            "password_configured": self.password != (0, 0, 0, 0),
            "password_change_enabled": self.settings.get(
                "change_password_enabled", False
            ),
            "restart_requires_password_update": self.restart_requires_password_update,
            "password_update_warning": self.password_update_warning,
            "delete_all_enabled": self.settings.get("delete_all_enabled", False),
        }

    def event_payload(self, action):
        """Build a complete event payload for immediate LNXlink publishing."""
        self.last_update_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload = self.state()
        payload["time"] = int(time.time())
        return payload

    def publish_state(self, action):
        """Publish cached state changes through the Addon callback."""
        self.state_changed(action)

    def set_ledcolor(self, led_color=None, led_mode=None, action=None):
        """Same LED helper as the working service, including its behavior."""
        if not self.led_enabled or self.finger is None:
            return

        if action == "reset":
            self.finger.set_led(color=self.LEDCOLOR_RED, mode=self.LEDMODE_OFF)
        elif action == "error":
            self.finger.set_led(color=self.LEDCOLOR_RED, mode=self.LEDMODE_STILL)
            time.sleep(1)
            self.set_ledcolor(action="reset")
        elif action == "enroll":
            self.finger.set_led(color=self.LEDCOLOR_PURPLE, mode=self.LEDMODE_BREATH)
        elif action == "success":
            self.finger.set_led(color=self.LEDCOLOR_BLUE, mode=self.LEDMODE_STILL)
            time.sleep(1)
            self.set_ledcolor(action="reset")

        led_mode = self.LEDMODE_STILL
        if led_color is not None and led_mode is not None:
            self.finger.set_led(color=led_color, mode=led_mode)

    def delete_model(self, location):
        """Delete a fingerprint template from the sensor."""
        time.sleep(1)
        if self.finger.delete_model(location) == self.adafruit_fingerprint.OK:
            logger.info("Fingerprint deleted id=%s", location)
            self.get_sensor_info()
            self.status = f"deleted {location}"
            self.publish_state("deleted")
            return True

        logger.error("Fingerprint failed to delete id=%s", location)
        self.set_ledcolor(action="error")
        return False

    def empty_library(self):
        """Delete all fingerprint templates from the sensor."""
        time.sleep(1)
        if self.finger.empty_library() == self.adafruit_fingerprint.OK:
            logger.info("Fingerprint library emptied")
            self.get_sensor_info()
            self.status = "library emptied"
            self.publish_state("library_emptied")
            return True

        logger.error("Fingerprint failed to empty library")
        self.set_ledcolor(action="error")
        return False

    def get_fingerprint(
        self,
    ):  # pylint: disable=too-many-nested-blocks,too-many-statements
        """Continuously scan fingerprints and reconnect after sensor failures."""
        while True:
            if self.mode != "scan":
                time.sleep(self.scan_sleep)
                continue

            if not self.connect():
                time.sleep(self.reconnect_interval)
                continue

            try:
                is_finger_ok = self.finger.get_image() == self.adafruit_fingerprint.OK
            except Exception as err:  # pylint: disable=broad-exception-caught
                self._record_error("get_image", err)
                self._maybe_reconnect_after_error("get_image")
                time.sleep(self.scan_sleep)
                continue

            if not is_finger_ok:
                self._consecutive_read_errors = 0
                if self.finger_present or self.status != "waiting":
                    self.finger_present = False
                    self.status = "waiting"
                    self.matched = False
                    self.publish_state("waiting")
                else:
                    self.status = "waiting"
                    self.matched = False
                time.sleep(self.scan_sleep)
                continue

            self._handle_detected_finger()
            time.sleep(self.scan_sleep)

    def _handle_detected_finger(self):
        """Template and search one detected fingerprint."""
        try:
            self.finger_present = True
            self.status = "finger detected"
            self.publish_state("finger_detected")
            self.set_ledcolor(self.LEDCOLOR_PURPLE, self.LEDMODE_BLINK)
            logger.info("Fingerprint templating")
            time.sleep(0.2)

            if self.finger.image_2_tz(1) != self.adafruit_fingerprint.OK:
                self.finger_present = True
                self.last_id = None
                self.confidence = 0
                self.matched = False
                self.status = "invalid image"
                self.publish_state("invalid_image")
                self.unauthorized()
                self.set_ledcolor(action="error")
                return

            self.status = "templated"
            self.publish_state("templated")
            logger.info("Fingerprint searching")

            if self.finger.finger_search() == self.adafruit_fingerprint.OK:
                self._handle_match()
                return

            self.finger_present = True
            self.last_id = None
            self.confidence = 0
            self.matched = False
            self.status = "unauthorized"
            self.unauthorized()
            self.set_ledcolor(action="error")
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.finger_present = False
            self._record_error("scan", err)
            self.set_ledcolor(action="error")
            self._maybe_reconnect_after_error("scan")

    def _handle_match(self):
        """Update state after a successful fingerprint authorization."""
        self._consecutive_read_errors = 0
        self.last_id = self.finger.finger_id
        self.confidence = self.finger.confidence
        self.finger_present = True

        if self.confidence < self.minimum_confidence:
            self.matched = False
            self.status = "confidence too low"
            logger.error(
                "Fingerprint confidence too low id=%s confidence=%s threshold=%s",
                self.finger.finger_id,
                self.finger.confidence,
                self.minimum_confidence,
            )
            self.unauthorized()
            self.set_ledcolor(action="error")
            return

        self.last_authorized_time = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        self.last_authorized_id = self.finger.finger_id
        self.last_authorized_confidence = self.finger.confidence
        self.matched = True
        self.status = "matched"
        logger.info(
            "Fingerprint detected id=%s confidence=%s",
            self.finger.finger_id,
            self.finger.confidence,
        )
        self.set_ledcolor(self.LEDCOLOR_BLUE, self.LEDMODE_STILL)
        self.found_finger(self.finger.finger_id, self.finger.confidence)
        time.sleep(1)
        self.set_ledcolor(action="reset")

    def _maybe_reconnect_after_error(self, stage):
        """Reconnect the sensor after too many consecutive read failures."""
        if self._consecutive_read_errors >= self.max_read_errors:
            self.reconnect(
                f"{stage} failed {self._consecutive_read_errors} consecutive times"
            )

    def change_password(self, new_password):  # pylint: disable=protected-access
        """Change the fingerprint sensor password."""
        previous_mode = self.mode
        self.mode = "password"
        self.publish_state("mode_password")

        try:
            if not self.connect(force=True):
                return False

            password_bytes = self.parse_password(new_password)
            self.finger._send_packet(  # pylint: disable=protected-access
                [0x12] + list(password_bytes)
            )
            result = self.finger._get_packet(12)[0]  # pylint: disable=protected-access

            if result == self.adafruit_fingerprint.OK:
                self.password = password_bytes
                if hasattr(self.finger, "password"):
                    self.finger.password = password_bytes
                self.restart_requires_password_update = True
                self.password_update_warning = (
                    "Password changed on sensor. Update "
                    "settings.fingerprint.password before restarting LNXlink."
                )
                self.status = "password changed; update config password"
                self.last_error = None
                self.publish_state("password_changed")
                logger.info("Fingerprint password changed")
                self.set_ledcolor(action="success")
                return True

            self.status = "password change failed"
            self.last_error = f"SetPwd returned {result}"
            self.publish_state("password_change_failed")
            logger.error("Fingerprint password change failed with code %s", result)
            self.set_ledcolor(action="error")
            return False
        except Exception as err:  # pylint: disable=broad-exception-caught
            self._record_error("change_password", err)
            self.set_ledcolor(action="error")
            return False
        finally:
            self.mode = previous_mode
            self.publish_state(f"mode_{previous_mode}")

    @staticmethod
    def parse_password(value):
        """Convert a decimal/hex/list password value to a four-byte tuple."""
        if isinstance(value, (list, tuple)) and len(value) == 4:
            return tuple(int(item) & 0xFF for item in value)

        if isinstance(value, str):
            value = value.strip()
            number = int(value, 16) if value.lower().startswith("0x") else int(value)
        else:
            number = int(value)

        number &= 0xFFFFFFFF
        return (
            (number >> 24) & 0xFF,
            (number >> 16) & 0xFF,
            (number >> 8) & 0xFF,
            number & 0xFF,
        )

    def _set_enroll_status(self, status):
        """Publish a detailed enrollment status update."""
        self.status = status
        logger.info("Fingerprint %s", status)
        self.publish_state(status.replace(" ", "_"))

    def enroll_finger(
        self, location, timeout=None
    ):  # pylint: disable=too-many-return-statements,too-many-branches
        """Take two finger images, template them, then store in location."""
        if timeout is None:
            timeout = self.enroll_timeout

        self._set_enroll_status(f"enroll {location}: starting")
        time.sleep(1)
        for fingerimg in range(1, 3):
            self._set_enroll_status(f"enroll {location}: waiting image {fingerimg}")
            self.set_ledcolor(action="enroll")
            start = time.time()

            while True:
                i = self.finger.get_image()
                if i == self.adafruit_fingerprint.OK:
                    self._set_enroll_status(
                        f"enroll {location}: image {fingerimg} captured"
                    )
                    break
                if i == self.adafruit_fingerprint.NOFINGER:
                    if (time.time() - start) > timeout:
                        self._set_enroll_status(
                            f"enroll {location}: timeout image {fingerimg}"
                        )
                        self.set_ledcolor(action="error")
                        return False
                elif i == self.adafruit_fingerprint.IMAGEFAIL:
                    logger.error("Fingerprint enroll imaging error")
                    self._set_enroll_status(f"enroll {location}: imaging error")
                    self.set_ledcolor(action="error")
                    return False
                else:
                    logger.error("Fingerprint enroll get_image error code=%s", i)
                    self._set_enroll_status(f"enroll {location}: get image error {i}")
                    self.set_ledcolor(action="error")
                    return False

            i = self.finger.image_2_tz(fingerimg)
            if i == self.adafruit_fingerprint.OK:
                self.set_ledcolor(action="success")
                self._set_enroll_status(
                    f"enroll {location}: image {fingerimg} templated"
                )
            else:
                logger.error("Fingerprint enroll image_2_tz failed code=%s", i)
                self._set_enroll_status(f"enroll {location}: template failed {i}")
                self.set_ledcolor(action="error")
                return False

            if fingerimg == 1:
                self._set_enroll_status(f"enroll {location}: remove finger")
                time.sleep(1)
                while i != self.adafruit_fingerprint.NOFINGER:
                    i = self.finger.get_image()

        i = self.finger.create_model()
        if i != self.adafruit_fingerprint.OK:
            logger.error("Fingerprint enroll create_model failed code=%s", i)
            self._set_enroll_status(f"enroll {location}: model failed {i}")
            self.set_ledcolor(action="error")
            return False

        i = self.finger.store_model(location)
        if i != self.adafruit_fingerprint.OK:
            logger.error("Fingerprint enroll store_model failed code=%s", i)
            self._set_enroll_status(f"enroll {location}: store failed {i}")
            self.set_ledcolor(action="error")
            return False

        self.get_sensor_info()
        self._set_enroll_status(f"enroll {location}: stored")
        self.updated_templates()
        return True

    def enroll_new(self, position):
        """Enroll a new fingerprint in the requested or first empty position."""
        if position < 0:
            empty_positions = list(
                set(range(0, self.finger.library_size - 1)) - set(self.finger.templates)
            )
            position = empty_positions[0]
        logger.info("Fingerprint enrolling id=%s", position)
        self.enroll_finger(position)
        return position

    def _record_error(self, stage, err):
        """Record, log, and publish a fingerprint error."""
        self.read_error_count += 1
        self._consecutive_read_errors += 1
        self.last_error = str(err)
        self.status = f"{stage} failed"
        logger.error("Fingerprint %s failed: %s", stage, err)
        self.error(stage, err)
