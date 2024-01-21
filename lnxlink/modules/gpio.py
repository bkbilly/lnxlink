"""Checks GPIO pins from a raspberry"""
import time
from collections import deque
from threading import Thread
from .scripts.helpers import import_install_package


class GpioInputHandle:
    """Handle the Raspberry PI GPIO inputs by fixing spike events"""

    def __init__(self, gpio, pin, callback):
        """Start checking for pin values in a new thread"""
        self.gpio = gpio
        self.pin = pin
        self.callback = callback
        self.pinvalue = None
        readgpio_thr = Thread(target=self.read, daemon=True)
        readgpio_thr.start()

    def read(self):
        """Gets the average value of the input pin and send it to the callback"""
        deq = deque(maxlen=15)
        self.gpio.setup(self.pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        while True:
            deq.append(self.gpio.input(self.pin))
            pinvalue = round(sum(deq) / deq.maxlen)
            if pinvalue != self.pinvalue:
                self.pinvalue = pinvalue
                self.callback(self.pin, self.pinvalue)
            time.sleep(0.1)


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "gpio"
        self.lnxlink = lnxlink
        self.gpio_results = {}
        self.started = False
        if self._is_raspberry():
            self._requirements()

    def get_info(self):
        """Starts only once the GPIO class for each pin"""
        if self._is_raspberry() and not self.started:
            self.started = True
            for device in self.lnxlink.config["settings"]["gpio"]["inputs"]:
                GpioInputHandle(
                    self.lib["gpio"].GPIO, device["pin"], self.input_callback
                )

    def input_callback(self, pin, pinvalue):
        """Sends the data to the MQTT broker asyncronous"""
        value = "ON"
        if pinvalue == 0:
            value = "OFF"
        filter_gpio = list(
            filter(
                lambda pins: pins["pin"] == pin,
                self.lnxlink.config["settings"]["gpio"]["inputs"],
            )
        )
        self.gpio_results[f"input_{filter_gpio[0]['name']}"] = value
        self.lnxlink.run_module(self.name, self.gpio_results)

    def _is_raspberry(self):
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
        return discovery_info
