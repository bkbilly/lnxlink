"""Broadcast keystrokes or complex combinations"""
import os
import re
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand, get_display_variable

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Send Keys"
        self.used_tool = None
        if which("ydotool") is not None:
            self.used_tool = "ydotool"
        elif which("xdotool") is not None:
            self.used_tool = "xdotool"
        else:
            raise SystemError("System command 'xdotool' or 'ydotool' not found")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Send Keys": {
                "type": "text",
                "icon": "mdi:keyboard-outline",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if data == "":
            logger.debug("No key data provided to send.")
            return
        display_variable = get_display_variable()
        if display_variable is not None and os.environ["DISPLAY"] is None:
            os.environ["DISPLAY"] = display_variable
            logger.info("Initializing empty DISPLAY environment variable")
        if self.used_tool == "ydotool":
            event_codes_path = "/usr/include/linux/input-event-codes.h"
            key_map = self._extract_key_definitions(event_codes_path)
            data = self._create_key_representation(data, key_map)
            logger.debug("Sending keys via ydotool: %s", data)
        syscommand(f"{self.used_tool} key {data}")

    def _create_key_representation(self, key_string, key_map):
        """
        Converts a string like "<ctrl>+<alt>+a+b" into a list of press/release tuples.
        """
        special_keys = ["ctrl", "alt", "shift", "cmd", "super"]
        sequence = []
        for keys in key_string.lower().split(" "):
            modifiers_pressed_in_order = []

            for key in keys.split("+"):
                if key in special_keys or (key.startswith("<") and key.endswith(">")):
                    key = key.replace("<", "").replace(">", "")
                    sequence.append((key, 1))
                    modifiers_pressed_in_order.append(key)
                else:
                    sequence.append((key, 1))
                    sequence.append((key, 0))
            for key in reversed(modifiers_pressed_in_order):
                sequence.append((key, 0))

        logger.info("press sequence for ydotool: %s", sequence)
        formatted_parts = []
        for key_name, action in sequence:
            if key_name in key_map:
                code = key_map.get(key_name)
                formatted_string = ":".join(map(str, [code, action]))
                formatted_parts.append(formatted_string)
            else:
                logger.warning("Key '%s' not found in key map.", key_name)
        formatted_output = " ".join(formatted_parts)

        return formatted_output

    def _extract_key_definitions(self, file_path):
        """
        Reads a file, finds lines starting with '#define KEY_', and extracts
        the key name and its integer/hexadecimal value.
        """
        key_definitions = {}

        # Pattern remains the same: capture KEY_name and the value
        pattern = r"^\s*#define\s+KEY_([^\s]+)\s+([0-9xXA-Fa-f]+).*$"

        # Check if the file exists before attempting to open it
        if not os.path.exists(file_path):
            logger.error("The file was not found at '%s'.", file_path)
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    match = re.search(pattern, line)

                    if match:
                        key_name = match.group(1).lower()
                        value_str = match.group(2)

                        try:
                            if value_str.lower().startswith("0x"):
                                value = int(value_str, 16)
                            else:
                                value = int(value_str)

                            key_definitions[key_name] = value
                            if key_name.startswith("left") and not key_name.endswith(
                                "left"
                            ):
                                key_name_dup = key_name.replace("left", "")
                                key_definitions[key_name_dup] = value
                        except ValueError:
                            logger.warning(
                                "Failed to convert value '%s' on line %s in file '%s'",
                                value_str,
                                line_number,
                                file_path,
                            )

        except IOError as e:
            logger.error(
                "An I/O error occurred while reading the file '%s': %s", file_path, e
            )
            return None

        return key_definitions
