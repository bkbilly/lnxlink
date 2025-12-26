"""Simulate mouse movement and actions"""
import os
import time
import logging
import threading
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand, get_display_variable

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Mouse"
        self.movement = [0, 0]
        commands = {
            "ydotool": {
                "left_click": "ydotool click 0xc0",
                "right_click": "ydotool click 0xc1",
                "left_mouse_down": "ydotool click 0x40",
                "left_mouse_up": "ydotool click 0x80",
                "move_rel": "ydotool mousemove -x %s -y %s",
                "move_abs": "ydotool mousemove -a -x %s -y %s",
                "run_check": "ydotool mousemove",
                "wheel_up": "ydotool mousemove -w -x 0 -y +1",
                "wheel_down": "ydotool mousemove -w -x 0 -y -1",
            },
            "xdotool": {
                "left_click": "xdotool click 1",
                "right_click": "xdotool click 3",
                "left_mouse_down": "ydotool mousedown 1",
                "left_mouse_up": "ydotool mouseup 1",
                "move_rel": "xdotool mousemove -- %s %s",
                "move_abs": "xdotool mousemove %s %s",
                "wheel_up": "xdotool click 4",
                "wheel_down": "xdotool click 5",
            },
        }
        self.commands = None
        for command, command_options in commands.items():
            if which(command) is not None:
                run_check = command_options.get("run_check")
                if run_check is not None:
                    _, _, returncode = syscommand(run_check)
                    if returncode != 0:
                        continue
                self.commands = command_options
                logger.debug("Using '%s' for mouse control", command)
                break
        if self.commands is None:
            raise SystemError("System commands 'ydotool' or 'xdotool' not found")

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
            "Mouse Click Left Up": {
                "type": "button",
                "icon": "mdi:mouse-move-up",
            },
            "Mouse Click Left Down": {
                "type": "button",
                "icon": "mdi:mouse-move-down",
            },
            "Mouse Wheel Up": {
                "type": "button",
                "icon": "mdi:arrow-vertical-lock",
            },
            "Mouse Wheel Down": {
                "type": "button",
                "icon": "mdi:arrow-vertical-lock",
            },
        }

    # pylint: disable=too-many-branches
    def start_control(self, topic, data):
        """Control system"""
        display_variable = get_display_variable()
        print(display_variable)
        if display_variable is not None and os.environ["DISPLAY"] is None:
            os.environ["DISPLAY"] = display_variable
            logger.info("Initializing empty DISPLAY environment variable")

        if topic[1] == "mouse_coordinates":
            if "," in data:
                coords = data.replace(" ", "").split(",")
            elif " " in data:
                coords = data.split(" ")
            else:
                return
            move_type = "move_abs"
            if coords[0].startswith("+") or coords[0].startswith("-"):
                move_type = "move_rel"
            if coords[1].startswith("+") or coords[1].startswith("-"):
                move_type = "move_rel"
            syscommand(self.commands[move_type] % (coords[0], coords[1]))
        elif topic[1] == "mouse_left":
            self._move([-1, 0])
        elif topic[1] == "mouse_right":
            self._move([1, 0])
        elif topic[1] == "mouse_up":
            self._move([0, -1])
        elif topic[1] == "mouse_down":
            self._move([0, 1])
        elif topic[1] in ["mouse_click", "mouse_click_left"]:
            self.movement = [0, 0]
            syscommand(self.commands["left_click"])
        elif topic[1] == "mouse_click_right":
            self.movement = [0, 0]
            syscommand(self.commands["right_click"])
        elif topic[1] == "mouse_click_left_down":
            syscommand(self.commands["left_mouse_down"])
        elif topic[1] == "mouse_click_left_up":
            self.movement = [0, 0]
            syscommand(self.commands["left_mouse_up"])
        elif topic[1] == "mouse_wheel_up":
            self.movement = [0, 0]
            syscommand(self.commands["wheel_up"])
        elif topic[1] == "mouse_wheel_down":
            self.movement = [0, 0]
            syscommand(self.commands["wheel_down"])

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
            syscommand(self.commands["move_rel"] % (move_x, move_y))
            time.sleep(0.05)
        # Used if the user wants to run the same movement
        self.movement = [0, 0]
