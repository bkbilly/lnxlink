"""Monitor Gamepad controllers for button presses"""
import logging
import re
import struct
import time
from threading import Lock, Thread

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Read events by Gamepad"""

    def __init__(self, lnxlink):
        self.name = "Gamepad"
        self.gamepads = []
        self.running_threads = {}
        self.last_used = {}
        self.watcher_tokens = {}
        self.activity_lock = Lock()
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
        now = int(time.time())
        with self.activity_lock:
            last_used = list(self.last_used.values())
        return any(now - used < self.timeout_used for used in last_used)

    def watch_gamepads(self):
        """Watch for gamepad connections"""
        stdout, _, _ = syscommand(
            "cat /proc/bus/input/devices | grep -P '^H:.* js[0-9]+'", ignore_errors=True
        )
        match = re.findall(r"(event\d+)", stdout)
        if self.gamepads != match:
            logger.info("Gamepads found: %s", match)
            self.gamepads = match

            for event in set(self.running_threads) - set(match):
                self.running_threads.pop(event)
                with self.activity_lock:
                    self.watcher_tokens.pop(event, None)
                    self.last_used.pop(event, None)

        for event in match:
            running_thread = self.running_threads.get(event)
            if running_thread is None or not running_thread.is_alive():
                watcher_token = object()
                with self.activity_lock:
                    self.watcher_tokens[event] = watcher_token
                watch_thr = Thread(
                    target=self.watch_input,
                    args=(event, watcher_token),
                    daemon=True,
                )
                watch_thr.start()
                logger.debug("Started for: %s", event)
                self.running_threads[event] = watch_thr

    def watch_input(self, event, watcher_token):
        """Thread that watches gamepad inputs"""
        decode_str = "llHHI"
        try:
            with open(f"/dev/input/{event}", "rb") as file:
                while game_data := file.read(struct.calcsize(decode_str)):
                    _, _, ev_type, code, value = struct.unpack(decode_str, game_data)
                    if ev_type != 0 or code != 0 or value != 0:
                        with self.activity_lock:
                            if self.watcher_tokens.get(event) is watcher_token:
                                self.last_used[event] = int(time.time())
                        logger.debug("%s %s", code, value)
        except OSError as err:
            # Errno 19: "No such device" happens when the gamepad is disconnected
            if err.errno == 19:
                logger.info("Gamepad disconnected: %s", event)
            else:
                logger.error("Gamepad error for %s: %s", event, err)
        except Exception as err:
            logger.error("Unexpected error for %s: %s", event, err)
        finally:
            with self.activity_lock:
                if self.watcher_tokens.get(event) is watcher_token:
                    self.watcher_tokens.pop(event, None)
                    self.last_used.pop(event, None)
