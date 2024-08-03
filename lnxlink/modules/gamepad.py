"""Monitor Gamepad controllers for button presses"""

import re
import time
import struct
import logging
from threading import Thread
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Read events by Gamepad"""

    def __init__(self, lnxlink):
        self.name = "Gamepad"
        self.gamepads = []
        self.running_threads = []
        self.last_used = 0
        self.timeout_used = 60

    def exposed_controls(self):
        """Expose gamepad sensor to Home Assistant"""
        return {
            "Gamepad Status": {
                "type": "sensor",
                "icon": "mdi:controller",
            },
        }

    def get_info(self):
        """Gather gamepad information"""
        self.watch_gamepads()
        if self.gamepads:
            if not (int(time.time()) - self.last_used < self.timeout_used):
                return "Inactive"
            return "On"
        return "Off"

    def watch_gamepads(self):
        """Watch inputs to see if gamepads were connected"""
        stdout, _, _ = syscommand(
            "cat /proc/bus/input/devices | grep -P '^H:.* js[0-9]+'", ignore_errors=True
        )
        match = re.findall(r"(event\d+)", stdout)
        if self.gamepads != match:
            self.gamepads = match
            if self.gamepads:
                logger.info("Gamepads connected: %s", match)
            for running_thread in self.running_threads:
                running_thread.join(1)
            self.running_threads = []
            for event in match:
                watch_thr = Thread(target=self.watch_input, args=(event,), daemon=True)
                watch_thr.start()
                logger.info("Watching input for: %s", event)
                self.running_threads.append(watch_thr)

    def watch_input(self, event):
        """Watch gamepads for inactivity / disconnection"""
        decode_str = "llHHI"
        try:
            with open(f"/dev/input/{event}", "rb") as file:
                while game_data := file.read(struct.calcsize(decode_str)):
                    _, _, ev_type, code, value = struct.unpack(decode_str, game_data)
                    if ev_type != 0 or code != 0 or value != 0:
                        self.last_used = int(time.time())
                        logger.debug(code, value)
        except OSError as e:
            logger.info("Gamepad disconnected: %s", event)
