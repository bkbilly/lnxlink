"""Uses xdotool to control mouse"""
import os
import time
import logging
import threading
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Mouse"
        self.lnxlink = lnxlink
        self.movement = [0, 0]
        if which("xdotool") is None:
            raise SystemError("System command 'xdotool' not found")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Mouse Coordinates": {
                "type": "text",
                "icon": "mdi:mouse-variant",
            },
            "Mouse Left": {
                "type": "button",
                "icon": "mdi:gamepad-circle-left",
            },
            "Mouse Right": {
                "type": "button",
                "icon": "mdi:gamepad-circle-right",
            },
            "Mouse Up": {
                "type": "button",
                "icon": "mdi:gamepad-circle-up",
            },
            "Mouse Down": {
                "type": "button",
                "icon": "mdi:gamepad-circle-down",
            },
            "Mouse Click": {
                "type": "button",
                "icon": "mdi:mouse-left-click",
            },
            "Mouse Click Right": {
                "type": "button",
                "icon": "mdi:mouse-right-click",
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if os.environ.get("DISPLAY") is None:
            if self.lnxlink.display is not None:
                os.environ["DISPLAY"] = self.lnxlink.display
                logger.info("Initializing empty DISPLAY environment variable")

        if topic[1] == "mouse_coordinates":
            if "," in data:
                coords = data.replace(" ", "").split(",")
            elif " " in data:
                coords = data.split(" ")
            syscommand(f"xdotool mousemove {coords[0]} {coords[1]}")
        elif topic[1] == "mouse_left":
            self._move([-1, 0])
        elif topic[1] == "mouse_right":
            self._move([1, 0])
        elif topic[1] == "mouse_up":
            self._move([0, -1])
        elif topic[1] == "mouse_down":
            self._move([0, 1])
        elif topic[1] == "mouse_click":
            syscommand("xdotool click 1")
        elif topic[1] == "mouse_click_right":
            syscommand("xdotool click 3")

    def _move(self, movement):
        if self.movement == movement:
            # Stops mouse if it is moving
            self.movement = [0, 0]
        else:
            self.movement = movement
            move_mouse_thr = threading.Thread(target=self._move_mouse)
            move_mouse_thr.start()

    def _move_mouse(self):
        movement = self.movement
        for i in range(1, 90):
            if self.movement != movement:
                # Stops mouse if a new move command is sent
                return
            move_x = movement[0] * i
            move_y = movement[1] * i
            syscommand(f"xdotool mousemove_relative -- {move_x} {move_y}")
            time.sleep(0.05)
        # Used if the user wants to run the same movement
        self.movement = [0, 0]
