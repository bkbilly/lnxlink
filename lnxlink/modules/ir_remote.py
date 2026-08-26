"""Control IR devices or decode incoming signals on a Raspberry PI"""
import json
import logging
import os
import time
from threading import Thread

from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "IR Remote"
        self.lnxlink = lnxlink
        self.gpio_results = {}
        self.started = False
        if not self._is_raspberry():
            raise SystemError("Not supported non Raspberry PI devices")
        self.lnxlink.add_settings(
            "ir_remote",
            {
                "receiver": None,
                "transmitter": None,
                "buttons": [],
            },
        )
        receiver = self.lnxlink.config["settings"]["ir_remote"]["receiver"]
        transmitter = self.lnxlink.config["settings"]["ir_remote"]["transmitter"]
        if receiver in [None, []] and transmitter in [None, []]:
            raise SystemError("No configuration found")
        self._requirements()
        self.irremote = None

    def get_info(self):
        """Starts only once the GPIO class for each pin"""
        if not self.started:
            self.irremote = IRRemote(self.lib["pigpio"])
            self.started = True
            receiver = self.lnxlink.config["settings"]["ir_remote"]["receiver"]
            if receiver:
                self.irremote.setup_receiver(receiver, self.receiver_callback)

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        receiver = self.lnxlink.config["settings"]["ir_remote"]["receiver"]
        transmitter = self.lnxlink.config["settings"]["ir_remote"]["transmitter"]
        if receiver:
            discovery_info["IR Receiver"] = {
                "type": "infrared",
                "schema": "receiver",
                "icon": "mdi:square-wave",
                "subtopic": True,
            }
            discovery_info["IR Receiver Event"] = {
                "type": "event",
                "event_type": "button_short_press",
                "event_subtype": "ir_received",
                "icon": "mdi:remote",
                "subtopic": True,
            }
        if transmitter:
            discovery_info["IR Transmitter"] = {
                "type": "infrared",
                "schema": "emitter",
                "icon": "mdi:remote",
                "subtopic": True,
            }
            for button in self.lnxlink.config["settings"]["ir_remote"]["buttons"]:
                discovery_info[f"IR {button['name']}"] = {
                    "type": "button",
                    "icon": button.get("icon", "mdi:square-wave"),
                    "payload_press": json.dumps(button["data"]),
                }

        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        transmitter = self.lnxlink.config["settings"]["ir_remote"]["transmitter"]
        if transmitter and self.irremote is not None:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    pass

            frequency = 38.0
            repeat_count = 0
            if isinstance(data, dict):
                ir_signal = data.get("timings", [])
                modulation = data.get("modulation", 38000)
                frequency = modulation / 1000.0 if modulation else 38.0
                repeat_count = data.get("repeat_count", 0)
            else:
                ir_signal = data

            if ir_signal:
                self.irremote.pause = True
                self.irremote.send_signal(
                    transmitter,
                    ir_signal,
                    frequency=frequency,
                    repeat_count=repeat_count,
                )
                self.irremote.pause = False

    def receiver_callback(self, rawsignal, binsignal, decsignal, protocol):
        """Callback that sends the data to the MQTT broker"""
        timings = []
        for i, duration in enumerate(rawsignal):
            if i % 2 == 1:
                timings.append(-abs(duration))
            else:
                timings.append(abs(duration))

        tosend = {
            "timings": timings,
            "modulation": 38000,
            "rawsignal": rawsignal,
            "binsignal": binsignal,
            "decsignal": decsignal,
            "protocol": protocol,
        }
        self.lnxlink.run_module(f"{self.name}/IR Receiver", tosend)
        self.lnxlink.run_module(
            f"{self.name}/IR Receiver Event",
            tosend,
            retain=False,
            force_update=True,
            coalesce=False,
        )
        logger.debug("{%s}:{%s} = {%s}", protocol, decsignal, binsignal)

    def _requirements(self):
        self.lib = {
            "pigpio": import_install_package("pigpio"),
        }

    def _is_raspberry(self):
        model = ""
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", encoding="UTF-8") as f:
                model = f.read()
        if "raspberry" in model.lower():
            return True
        return False


class IRRemote:
    """docstring for IRRemote"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, pigpio):
        self.pigpio = pigpio
        self.pi = self.pigpio.pi()  # Connect to Pi.
        if not self.pi.connected:
            raise SystemError("Make sure the pigpiod daemon is running")

        self.gpio_rx = None
        self.last_tick = 0
        self.in_code = False
        self.ir_signal = []
        self.fetching_code = False

        self.read_thr = None
        self.pause = False

    def start_receiving(self, callback):
        """Start listening for IR commands"""
        while True:
            self.ir_signal = []
            self.fetching_code = True
            while self.fetching_code:
                time.sleep(0.1)
            time.sleep(0.5)
            signal = list(self.ir_signal)
            binsignal, decsignal, protocol = SignalDecoder().decode_signal(signal)
            callback(signal, binsignal, decsignal, protocol)
            time.sleep(0.1)

    def setup_receiver(self, gpio, callback):
        """Setup GPIO and it's callback"""
        self.gpio_rx = gpio
        if self.gpio_rx:
            glitch = 100
            self.pi.set_mode(
                self.gpio_rx, self.pigpio.INPUT
            )  # IR RX connected to this GPIO.
            self.pi.set_glitch_filter(self.gpio_rx, glitch)  # Ignore glitches.
            self.pi.callback(
                self.gpio_rx, self.pigpio.EITHER_EDGE, self.gpio_callback_handler
            )
            if self.read_thr is None:
                self.read_thr = Thread(
                    target=self.start_receiving, args=(callback,), daemon=True
                )
                self.read_thr.start()

    def disconnect(self):
        """Disconnects from GPIO and stops any running process"""
        if self.gpio_rx:
            self.pi.set_glitch_filter(self.gpio_rx, 0)  # Cancel glitch filter.
            self.pi.set_watchdog(self.gpio_rx, 0)  # Cancel watchdog.
            self.pi.stop()  # Disconnect from Pi
            if self.read_thr is not None:
                self.read_thr.join(timeout=5.0)
                self.read_thr = None

    def send_signal(self, gpio, ir_signal, frequency=38.0, repeat_count=0):
        """Sends an IR Signal to the IR LED"""
        self.pi.set_mode(gpio, self.pigpio.OUTPUT)  # IR TX connected to this GPIO.

        # Create wave
        self.pi.wave_add_new()
        waves_dict = {}
        wave_sequence = []
        for pulse_index, duration_us in enumerate(ir_signal):
            duration_us = abs(int(duration_us))
            if pulse_index & 1:  # Space
                if duration_us not in waves_dict:
                    self.pi.wave_add_generic([self.pigpio.pulse(0, 0, duration_us)])
                    waves_dict[duration_us] = self.pi.wave_create()
            else:  # Pulse
                if duration_us not in waves_dict:
                    wave_pulses = self.carrier(gpio, duration_us, frequency)
                    self.pi.wave_add_generic(wave_pulses)
                    waves_dict[duration_us] = self.pi.wave_create()
            wave_sequence.append(waves_dict[duration_us])

        for _ in range(max(1, repeat_count + 1)):
            self.pi.wave_chain(wave_sequence)
            while self.pi.wave_tx_busy():
                time.sleep(0.002)
        self.pi.wave_clear()
        self.pi.set_mode(gpio, self.pigpio.INPUT)

    def carrier(self, gpio, micros, frequency=38.0):
        """Generate carrier square wave"""
        wave_pulses = []
        cycle = 1000.0 / frequency
        cycles = int(round(micros / cycle))
        on = int(round(cycle / 2.0))
        time_elapsed = 0
        for cycle_index in range(cycles):
            target = int(round((cycle_index + 1) * cycle))
            time_elapsed += on
            off = target - time_elapsed
            time_elapsed += off
            wave_pulses.append(self.pigpio.pulse(1 << gpio, 0, on))
            wave_pulses.append(self.pigpio.pulse(0, 1 << gpio, off))
        return wave_pulses

    def normalise(self, code_durations):
        """This function identifies the distinct pulses and takes the
        average of the lengths making up each distinct pulse. Pulses
        and spaces are processed separately."""

        tolerance = 15
        toler_min = (100 - tolerance) / 100.0
        toler_max = (100 + tolerance) / 100.0

        entries = len(code_durations)
        processed_flags = [0] * entries  # Set all entries not processed.
        for start_index in range(entries):
            if not processed_flags[start_index]:  # Not processed?
                base_duration = code_durations[start_index]
                total_duration = base_duration
                similar = 1.0

                # Find all pulses with similar lengths to the start pulse.
                for compare_index in range(start_index + 2, entries, 2):
                    if not processed_flags[compare_index]:  # Unprocessed.
                        if (
                            (code_durations[compare_index] * toler_min)
                            < base_duration
                            < (code_durations[compare_index] * toler_max)
                        ):  # Similar.
                            total_duration = (
                                total_duration + code_durations[compare_index]
                            )
                            similar += 1.0

                # Calculate the average pulse length.
                average_duration = int(round(total_duration / similar, 0))
                code_durations[start_index] = average_duration

                # Set all similar pulses to the average value.
                for compare_index in range(start_index + 2, entries, 2):
                    if not processed_flags[compare_index]:  # Unprocessed.
                        if (
                            (code_durations[compare_index] * toler_min)
                            < base_duration
                            < (code_durations[compare_index] * toler_max)
                        ):  # Similar.
                            code_durations[compare_index] = average_duration
                            processed_flags[compare_index] = 1

    def end_of_code(self):
        """End of the IR code"""
        short = 10
        if len(self.ir_signal) > short:
            self.normalise(self.ir_signal)
            self.fetching_code = False
        else:
            self.ir_signal = []

    def gpio_callback_handler(self, gpio, level, tick):
        """Callback function of GPIO input"""
        pre_ms = 200
        post_ms = 25
        pre_us = pre_ms * 1000
        post_us = post_ms * 1000

        if level != self.pigpio.TIMEOUT:
            edge = self.pigpio.tickDiff(self.last_tick, tick)
            self.last_tick = tick

            if self.fetching_code:
                if (edge > pre_us) and (not self.in_code):  # Start of a self.ir_signal.
                    self.in_code = True
                    self.pi.set_watchdog(gpio, post_ms)  # Start watchdog.

                elif (edge > post_us) and self.in_code:  # End of a self.ir_signal.
                    self.in_code = False
                    self.pi.set_watchdog(gpio, 0)  # Cancel watchdog.
                    self.end_of_code()

                elif self.in_code:
                    if not self.pause:
                        self.ir_signal.append(edge)

        else:
            self.pi.set_watchdog(gpio, 0)  # Cancel watchdog.
            if self.in_code:
                self.in_code = False
                self.end_of_code()


class SignalDecoder:
    """Decode IR signals using specific protocols"""

    def decode_signal(self, ir_signal):
        """Tries to find the correct signal protocol"""
        if binary_signal := self.decode_nec(ir_signal.copy()):
            return binary_signal, int(binary_signal, 2), "NEC"
        if binary_signal := self.decode_rc5(ir_signal.copy()):
            return binary_signal, int(binary_signal, 2), "RC5"
        if binary_signal := self.decode_sirc(ir_signal.copy()):
            return binary_signal, int(binary_signal, 2), "SIRC"
        if binary_signal := self.decode_philips(ir_signal.copy()):
            return binary_signal, int(binary_signal, 2), "PHILIPS"
        return None, None, None

    def decode_nec(self, ir_signal):
        """▁▁▆▆▆▆▆▆▁▁▁▁▁▁▁▆▆▁▁▆▆▁▁▁▁▆▆▁▁
        |lpulse|lspace| 0 |  1  | 0 |"""

        logger.debug("Decoding using NEC Protocol")
        # protocol_leading = 9000
        # protocol_leading_space = 4500
        protocol_pulse = 562.5
        protocol_pulse_high = 1687.5
        width = 500

        ir_signal = ir_signal[2:]
        if len(set(ir_signal[0::2])) != 1:
            return None

        mybin = []
        for pulse, space in zip(ir_signal[0::2], ir_signal[1::2]):
            if not protocol_pulse - width < pulse < protocol_pulse + width:
                return None
            if protocol_pulse - width < space < protocol_pulse + width:
                mybin.append("0")
            elif protocol_pulse_high - width < space < protocol_pulse_high + width:
                mybin.append("1")
            else:
                return None
        return "".join(mybin)

    # pylint: disable=too-many-branches
    def decode_rc5(self, ir_signal):
        """▁▁▁▆▆▆▁▁▁▆▆▆▆▆▆▁▁▁▆▆▆▁▁▁
        |  1  |  1  | 0  |  0  |"""
        logger.debug("Decoding using RC5 Protocol")
        if len(set(ir_signal[0::2])) == 1:
            return None
        while len(set(ir_signal[1::2])) > 2:
            ir_signal.remove(max(ir_signal[1::2]))

        protocol_pulse = min(ir_signal)
        width = protocol_pulse / 2

        tmp_signal = [0]
        for pulse, space in zip(ir_signal[0::2], ir_signal[1::2]):
            if protocol_pulse - width < pulse < protocol_pulse + width:
                tmp_signal.append(1)
            elif protocol_pulse * 2 - width < pulse < protocol_pulse * 2 + width:
                tmp_signal.append(1)
                tmp_signal.append(1)
            else:
                logger.debug("pulse: %s", pulse)
                return None

            if protocol_pulse - width < space < protocol_pulse + width:
                tmp_signal.append(0)
            elif protocol_pulse * 2 - width < space < protocol_pulse * 2 + width:
                tmp_signal.append(0)
                tmp_signal.append(0)

        tmp_signal.append(1)
        tmp_signal.append(0)
        mybin = []
        for first, second in zip(tmp_signal[0::2], tmp_signal[1::2]):
            if first == 0 and second == 1:
                mybin.append("1")
            elif first == 1 and second == 0:
                mybin.append("0")
            else:
                logger.debug("can't decode: %s, %s", first, second)
                return None

        if len(mybin) < 4:
            return None
        mybin = mybin[3:]
        return "".join(mybin)

    def decode_sirc(self, ir_signal):
        """▁▁▆▆▆▆▆▆▁▁▁▁▁▁▁▆▆▆▁▁▆▆▆▆▆▁▁▆▆▆▆▆▁▁
        |lpulse|lspace|  0  |  1  |   1   |"""

        logger.debug("Decoding using Sony SIRC Protocol")
        protocol_leading = 2400
        protocol_leading_space = 600
        protocol_pulse = 600
        protocol_pulse_high = 1200
        width = 300

        leading_pulse = ir_signal.pop(0)
        if not protocol_leading - width < leading_pulse < protocol_leading + width:
            logger.debug("leading_pulse: %s", leading_pulse)
            return None
        leading_space = ir_signal.pop(0)
        if (
            not protocol_leading_space - width
            < leading_space
            < protocol_leading_space + width
        ):
            logger.debug("leading_space: %s", leading_space)
            return None
        if len(set(ir_signal[1::2])) > 2:
            return None

        mybin = []
        for pulse, space in zip(ir_signal[0::2], ir_signal[1::2]):
            if protocol_pulse - width < pulse < protocol_pulse + width:
                mybin.append("0")
            elif protocol_pulse_high - width < pulse < protocol_pulse_high + width:
                mybin.append("1")
            else:
                logger.debug("pulse: %s", pulse)
                return None

            if not protocol_pulse - width < space < protocol_pulse + width:
                # Stop repeated signal
                logger.debug("SIRC space: %s", space)
                break

        if "1" not in mybin:
            return None
        return "".join(mybin)

    def decode_philips(self, ir_signal):
        """▁▁▆▆▆▆▆▆▁▁▁▁▁▁▁▆▆▁▁▆▆▆▁▁▁▆▆▆▁▁▁
           |lpulse|lspace| 0 |  1  |  1  |
        Custom protocol that decodes philips IR signals"""

        logger.debug("Decoding using Custom Protocol")
        low = 430
        high = 860
        width = 200

        ir_signal = ir_signal[2:]
        mybin = []
        for pulse, _ in zip(ir_signal[0::2], ir_signal[1::2]):
            if low - width < pulse < low + width:
                mybin.append("0")
            elif high - width < pulse < high + width:
                mybin.append("1")
            else:
                mybin.append("0")
                mybin.append("1")
        return "".join(mybin)
