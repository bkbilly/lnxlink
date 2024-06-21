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
        self.timeout_used = 40

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Gamepad Used": {
                "type": "binary_sensor",
                "icon": "mdi:controller",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        self.watch_gamepads()
        if int(time.time()) - self.last_used < self.timeout_used:
            return True
        return False

    def watch_gamepads(self):
        """Watch for gamepad connections"""
        stdout, _, _ = syscommand(
            "cat /proc/bus/input/devices | grep -P '^H:.* js[0-9]+'", ignore_errors=True
        )
        match = re.findall(r"(event\d+)", stdout)
        if self.gamepads != match:
            logger.info("Gamepads found: %s", match)
            self.gamepads = match
            for running_thread in self.running_threads:
                running_thread.join(1)
            self.running_threads = []
            for event in match:
                watch_thr = Thread(target=self.watch_input, args=(event,), daemon=True)
                watch_thr.start()
                logger.debug("Started for: %s", event)
                self.running_threads.append(watch_thr)

    def watch_input(self, event):
        """Thread that watches gamepad inputs"""
        decode_str = "llHHI"
        with open(f"/dev/input/{event}", "rb") as file:
            while game_data := file.read(struct.calcsize(decode_str)):
                _, _, ev_type, code, value = struct.unpack(decode_str, game_data)
                if ev_type != 0 or code != 0 or value != 0:
                    self.last_used = int(time.time())
                    logger.debug(code, value)
