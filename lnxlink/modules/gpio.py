"""Control and monitor Raspberry Pi GPIO pins"""
import os
from threading import Timer

from lnxlink.modules.scripts.helpers import import_install_package


class GpioHandle:
    """Handle Raspberry PI GPIO inputs (with glitch filtering) and outputs."""

    def __init__(self, lib_gpio, pin, callback, setup="input"):
        self.lib_gpio = lib_gpio
        self.pin = pin
        self.callback = callback
        self.setup = setup

        # Delay for input glitch filtering (seconds)
        self.delay = 0.15
        self.timer = None
        self.last_reported_state = None

        if self.setup == "input":
            self.lib_gpio.setup(
                self.pin,
                self.lib_gpio.IN,
                pull_up_down=self.lib_gpio.PUD_UP,
            )
            self.last_reported_state = self.lib_gpio.input(self.pin)
            self.callback(self.pin, self.last_reported_state, self.setup)

            self.lib_gpio.add_event_detect(
                self.pin,
                self.lib_gpio.BOTH,
                callback=self.edge_detected,
                bouncetime=20,
            )

        elif self.setup == "output":
            # Establish the initial baseline state and report it immediately upon boot
            self.last_reported_state = (
                1 if self.lib_gpio.gpio_function(self.pin) == self.lib_gpio.OUT else 0
            )
            self.callback(self.pin, self.last_reported_state, self.setup)

    def edge_detected(self, channel):
        """Cancels active timers and starts a new verification countdown instantly upon detecting a GPIO state change"""
        if self.timer is not None:
            self.timer.cancel()

        current_state = self.lib_gpio.input(self.pin)

        if current_state == self.last_reported_state:
            return

        if self.delay > 0:
            self.timer = Timer(
                self.delay, self.verify_and_trigger, args=[current_state]
            )
            self.timer.start()
        else:
            self.verify_and_trigger(current_state)

    def verify_and_trigger(self, target_state):
        """Verifies GPIO state after a delay and triggers the external callback"""
        current_state = self.lib_gpio.input(self.pin)

        if current_state == target_state and current_state != self.last_reported_state:
            self.last_reported_state = current_state
            self.callback(self.pin, current_state, self.setup)

    def set_state(self, command):
        """Changes the output pin state and triggers the callback."""
        if self.setup != "output":
            return

        if command.lower() == "on":
            self.lib_gpio.setup(self.pin, self.lib_gpio.OUT)
            self.lib_gpio.output(self.pin, self.lib_gpio.HIGH)
            self.last_reported_state = 1

        elif command.lower() == "off":
            self.lib_gpio.setup(self.pin, self.lib_gpio.OUT)
            self.lib_gpio.output(self.pin, self.lib_gpio.LOW)
            self.lib_gpio.setup(self.pin, self.lib_gpio.IN)
            self.last_reported_state = 0

        self.callback(self.pin, self.last_reported_state, self.setup)


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "gpio"
        self.lnxlink = lnxlink
        self.gpio_results = {}
        self.started = False
        self.handles = {}

        if not self._is_raspberry():
            raise SystemError("Not supported non Raspberry PI devices")
        self.lnxlink.add_settings(
            "gpio",
            {
                "inputs": [],
                "outputs": [],
            },
        )
        self.lib_gpio = import_install_package("RPi.GPIO")
        self.lib_gpio.GPIO.setmode(self.lib_gpio.GPIO.BCM)

    def get_info(self):
        """Starts only once the GPIO class for each pin"""
        if self._is_raspberry() and not self.started:
            self.started = True

            for device in self.lnxlink.config["settings"]["gpio"]["inputs"]:
                pin = device["pin"]
                self.handles[pin] = GpioHandle(
                    self.lib_gpio.GPIO, pin, self.pin_callback, "input"
                )

            for device in self.lnxlink.config["settings"]["gpio"]["outputs"]:
                pin = device["pin"]
                self.handles[pin] = GpioHandle(
                    self.lib_gpio.GPIO, pin, self.pin_callback, "output"
                )
        return self.gpio_results

    def pin_callback(self, pin, pinvalue, pintype):
        """Sends the data to the MQTT broker asyncronous"""
        value = "ON" if pinvalue == 1 else "OFF"

        filter_input_gpio = list(
            filter(
                lambda pins: pins["pin"] == pin,
                self.lnxlink.config["settings"]["gpio"]["inputs"],
            )
        )
        filter_output_gpio = list(
            filter(
                lambda pins: pins["pin"] == pin,
                self.lnxlink.config["settings"]["gpio"]["outputs"],
            )
        )
        filter_gpio = filter_input_gpio + filter_output_gpio
        self.gpio_results[f"{pintype}_{filter_gpio[0]['name']}"] = value
        self.lnxlink.run_module(self.name, self.gpio_results)

    def _is_raspberry(self):
        model = ""
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", encoding="UTF-8") as f:
                model = f.read()
        if "raspberry" in model.lower():
            return True
        return False

    def exposed_controls(self):
        """Exposes to home assistant"""
        if not self._is_raspberry():
            return {}
        discovery_info = {}
        for device in self.lnxlink.config["settings"]["gpio"]["inputs"]:
            discovery_info[f"GPIO {device['name']}"] = {
                "type": "binary_sensor",
                "value_template": f"{{{{ value_json.get('input_{device['name']}') }}}}",
                "device_class": device.get("device_class", "None"),
            }
        for device in self.lnxlink.config["settings"]["gpio"]["outputs"]:
            discovery_info[f"GPIO {device['name']}"] = {
                "type": "switch",
                "value_template": f"{{{{ value_json.get('output_{device['name']}') }}}}",
                "icon": device.get("device_class", "mdi:bullhorn"),
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        outputs = self.lnxlink.config["settings"]["gpio"]["outputs"]
        outputs = {
            item["name"].lower().replace(" ", "_"): item["pin"] for item in outputs
        }

        out_key = topic[1].replace("gpio_", "")

        if out_key in outputs:
            pin = outputs[out_key]
            if pin in self.handles:
                self.handles[pin].set_state(data)
