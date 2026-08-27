"""Create user-defined custom sensors with arbitrary commands and HA discovery metadata"""
import json
import logging
import time
from typing import Any, Dict

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module for user-defined custom command sensors"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Custom Sensors"
        self.lnxlink = lnxlink
        self.discovery_info: Dict[str, Dict[str, Any]] = {}
        self.lnxlink.add_settings(
            "custom_sensors",
            {},
        )
        self.sensor_state: Dict[str, Dict[str, Any]] = {}

    def _get_sensor_configs(self) -> Dict[str, Dict[str, Any]]:
        """Normalize sensor configurations from settings dict or list"""
        raw_settings = self.lnxlink.config["settings"].get("custom_sensors", {})
        if raw_settings is None:
            return {}

        configs = {}
        if isinstance(raw_settings, dict):
            for sensor_id, cfg in raw_settings.items():
                if isinstance(cfg, dict):
                    configs[str(sensor_id)] = {
                        "id": str(sensor_id),
                        "name": cfg.get("name", str(sensor_id)),
                        "command": cfg.get("command", ""),
                        "type": cfg.get("type", "sensor"),
                        "device_class": cfg.get("device_class"),
                        "state_class": cfg.get("state_class"),
                        "unit": cfg.get("unit") or cfg.get("unit_of_measurement"),
                        "icon": cfg.get("icon", "mdi:gauge"),
                        "interval": int(cfg.get("interval", cfg.get("every_sec", 10))),
                        "timeout": int(cfg.get("timeout", 5)),
                    }
        elif isinstance(raw_settings, list):
            for item in raw_settings:
                if isinstance(item, dict):
                    sensor_id = item.get("id") or item.get("name", "sensor")
                    configs[str(sensor_id)] = {
                        "id": str(sensor_id),
                        "name": item.get("name", str(sensor_id)),
                        "command": item.get("command", ""),
                        "type": item.get("type", "sensor"),
                        "device_class": item.get("device_class"),
                        "state_class": item.get("state_class"),
                        "unit": item.get("unit") or item.get("unit_of_measurement"),
                        "icon": item.get("icon", "mdi:gauge"),
                        "interval": int(item.get("interval", item.get("every_sec", 10))),
                        "timeout": int(item.get("timeout", 5)),
                    }
        return configs

    def exposed_controls(self) -> Dict[str, Dict[str, Any]]:
        """Exposes to Home Assistant discovery"""
        self.discovery_info = {}
        configs = self._get_sensor_configs()

        for sensor_id, cfg in configs.items():
            if not cfg["command"]:
                continue

            entity_title = cfg["name"]
            control_type = cfg["type"]
            control_def: Dict[str, Any] = {
                "type": control_type,
                "icon": cfg["icon"],
                "subtopic": True,
                "value_template": "{{ value_json.value if (value_json is mapping and 'value' in value_json) else value }}",
                "attributes_template": "{{ value_json.attributes | tojson if (value_json is mapping and 'attributes' in value_json) else '{}' }}",
            }
            if cfg.get("unit"):
                control_def["unit"] = cfg["unit"]
            if cfg.get("device_class"):
                control_def["device_class"] = cfg["device_class"]
            if cfg.get("state_class"):
                control_def["state_class"] = cfg["state_class"]

            self.discovery_info[entity_title] = control_def

            if sensor_id not in self.sensor_state:
                self.sensor_state[sensor_id] = {
                    "last_time": 0,
                    "last_data": None,
                }

        return self.discovery_info

    def get_info(self, force_update: bool = False):
        """Gather information from the system and publish subtopics"""
        configs = self._get_sensor_configs()
        cur_time = time.time()

        for sensor_id, cfg in configs.items():
            if not cfg["command"]:
                continue

            state = self.sensor_state.setdefault(
                sensor_id, {"last_time": 0, "last_data": None}
            )
            interval = max(1, cfg["interval"])

            if force_update or (cur_time - state["last_time"] >= interval):
                state["last_time"] = cur_time
                stdout, stderr, rc = syscommand(
                    cfg["command"],
                    ignore_errors=True,
                    timeout=cfg["timeout"],
                )
                if rc == 0:
                    raw_val = stdout.strip()
                    payload = self._format_payload(raw_val, cfg["type"])
                    state["last_data"] = payload
                    self.lnxlink.run_module(
                        f"{self.name}/{sensor_id}",
                        payload,
                        force_update=force_update,
                    )
                else:
                    logger.warning(
                        "Custom sensor '%s' command failed (exit code %s): %s",
                        sensor_id,
                        rc,
                        stderr.strip(),
                    )

        return None

    @staticmethod
    def _format_payload(raw: str, control_type: str) -> Dict[str, Any]:
        """Format raw command stdout to structured payload"""
        # Try JSON first
        if raw.startswith("{") and raw.endswith("}"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if "value" in data:
                        return data
                    return {"value": raw, "attributes": data}
            except Exception:
                pass

        if control_type == "binary_sensor":
            is_on = raw.lower() not in {"false", "no", "0", "off", "", "null"}
            return {
                "value": "ON" if is_on else "OFF",
                "attributes": {"raw": raw},
            }

        return {
            "value": raw,
            "attributes": {"raw": raw},
        }
