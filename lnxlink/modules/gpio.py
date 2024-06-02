"""Checks GPIO pins from a raspberry"""
import os
import time
from collections import deque
from threading import Thread
from lnxlink.modules.scripts.helpers import import_install_package


class GpioHandle:
    """Handle the Raspberry PI GPIO inputs by fixing spike events"""

    def __init__(self, gpio, pin, callback, setup="input"):
        """Start checking for pin values in a new thread"""
        self.gpio = gpio
        self.pin = pin
        self.callback = callback
        self.setup = setup
        self.pinvalue = None
        readgpio_thr = Thread(target=self.read, daemon=True)
        readgpio_thr.start()

    def read(self):
        """Gets the average value of the input pin and send it to the callback"""
        if self.setup == "input":
            self.gpio.setup(self.pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
            deq = deque(maxlen=15)
        elif self.setup == "output":
            deq = deque(maxlen=1)
        while True:
            if self.setup == "input":
                deq.append(self.gpio.input(self.pin))
            else:
                deq.append(0)
                if self.gpio.gpio_function(self.pin) == self.gpio.OUT:
                    deq.append(1)
            pinvalue = round(sum(deq) / deq.maxlen)
            if pinvalue != self.pinvalue:
                self.pinvalue = pinvalue
                self.callback(self.pin, self.pinvalue, self.setup)
            time.sleep(0.1)


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "gpio"
        self.lnxlink = lnxlink
        self.gpio_results = {}
        self.started = False
        if not self._is_raspberry():
            raise SystemError("Not supported non Raspberry PI devices")
        self._requirements()

    def get_info(self):
        """Starts only once the GPIO class for each pin"""
        if self._is_raspberry() and not self.started:
            self.started = True
            for device in self.lnxlink.config["settings"]["gpio"]["inputs"]:
                GpioHandle(
                    self.lib["gpio"].GPIO, device["pin"], self.pin_callback, "input"
                )
            for device in self.lnxlink.config["settings"]["gpio"]["outputs"]:
                GpioHandle(
                    self.lib["gpio"].GPIO, device["pin"], self.pin_callback, "output"
                )

    def pin_callback(self, pin, pinvalue, pintype):
        """Sends the data to the MQTT broker asyncronous"""
        value = "ON"
        if pinvalue == 0:
            value = "OFF"
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
            with open("/proc/device-tree/model", "r", encoding="UTF-8") as f:
                model = f.read()
        if "raspberry" in model.lower():
            return True
        return False

    def _requirements(self):
        self.lib = {
            "gpio": import_install_package("RPi.GPIO"),
        }
        self.lib["gpio"].GPIO.setmode(self.lib["gpio"].GPIO.BCM)

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
        pin = outputs[out_key]
        if data.lower() == "on":
            self.lib["gpio"].GPIO.setup(pin, self.lib["gpio"].GPIO.OUT)
            self.lib["gpio"].GPIO.output(pin, self.lib["gpio"].GPIO.HIGH)
        elif data.lower() == "off":
            self.lib["gpio"].GPIO.setup(pin, self.lib["gpio"].GPIO.OUT)
            self.lib["gpio"].GPIO.output(pin, self.lib["gpio"].GPIO.LOW)
            self.lib["gpio"].GPIO.setup(pin, self.lib["gpio"].GPIO.IN)
