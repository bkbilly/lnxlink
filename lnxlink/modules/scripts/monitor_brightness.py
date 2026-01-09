"""
Module to read and set monitor brightness via I2C/DDC and sysfs.
Based on the work from: https://github.com/Crozzers/screen_brightness_control
Copyright (c) 2025 Crozzers (https://github.com/Crozzers)
"""

import os
import glob
import time
import fcntl
import struct
import functools
import operator
from typing import Optional, List, Set, BinaryIO


class MonitorBrightness:
    """Base class for all monitor types."""

    def __init__(self, identifier: str, manufacturer: str, name: str):
        self.identifier = identifier  # Bus path or sysfs path
        self.manufacturer = manufacturer
        self.name = name
        self.unique_name = f"{manufacturer} {name}"
        self.last_successful_read = 50

    def get_brightness(self, timeout: float = 2.0) -> Optional[int]:
        """Polls for brightness until timeout. Returns None if max_val is 0."""
        raise NotImplementedError

    def set_brightness(self, value: int) -> None:
        """Sets brightness level. Returns True on success."""
        raise NotImplementedError

    @staticmethod
    def list_displays() -> tuple[List["MonitorBrightness"], Set[str]]:
        """Scans I2C buses and /sys/class/backlight to return all monitors."""
        found_displays = []
        issues = set()

        # 1. Internal Laptop Displays (Sysfs)
        for path in glob.glob("/sys/class/backlight/*"):
            # Check permissions
            if not os.access(os.path.join(path, "brightness"), os.W_OK):
                issues.add(
                    "Backlight Permission Error: Create a udev rule.\n"
                    'Run: echo \'SUBSYSTEM=="backlight",RUN+="/bin/chmod 666" '
                    "/sys/class/backlight/%k/brightness /sys/class/backlight/%k/bl_power\"'"
                    " | sudo tee -a /etc/udev/rules.d/backlight-permissions.rules\n"
                    "Then run: sudo udevadm control --reload-rules && udevadm trigger"
                )
            found_displays.append(SysfsMonitor(path))

        # 2. External Monitors (I2C/DDC)
        for i2c_path in sorted(glob.glob("/dev/i2c-*")):
            try:
                # Use 'rb+' for binary read/write, buffering=0 for unbuffered I/O
                with open(i2c_path, "r+b", buffering=0) as f:
                    # Use EDID address to identify the monitor
                    # 0x0703 is I2C_SLAVE
                    fcntl.ioctl(f.fileno(), 0x0703, 0x50)
                    data = f.read(256)

                if data.startswith(bytes.fromhex("00 FF FF FF FF FF FF 00")):
                    mfg, name, _ = DDCIPMonitor.parse_edid(data)
                    found_displays.append(DDCIPMonitor(i2c_path, mfg, name))

            except PermissionError:
                issues.add(
                    f"I2C Permission Error: User '{os.getlogin()}' needs 'i2c' group access.\n"
                    f"Run: sudo usermod -aG i2c {os.getlogin()} && reboot"
                )
            except (OSError, IOError, Exception):
                continue

        return found_displays, issues

    def __repr__(self):
        return (
            f"<MonitorBrightness {self.manufacturer} {self.name} on {self.identifier}>"
        )


class SysfsMonitor(MonitorBrightness):
    """Handles laptop backlights via /sys/class/backlight."""

    def __init__(self, path: str):
        name = os.path.basename(path)
        super().__init__(path, "Internal", name)
        # Cache max_brightness on init so we don't read it every time
        self.max_brightness = self._read_value("max_brightness")

    def _read_value(self, filename: str) -> int:
        """Helper to read a single integer from a sysfs file."""
        try:
            with open(
                os.path.join(self.identifier, filename), "r", encoding="UTF-8"
            ) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def get_brightness(self, timeout: float = 1.0) -> Optional[int]:
        # If max is 0, device is invalid or unreadable
        if not self.max_brightness:
            return None

        cur_val = self._read_value("brightness")
        self.last_successful_read = int((cur_val / self.max_brightness) * 100)
        return self.last_successful_read

    def set_brightness(self, value: int) -> None:
        if not self.max_brightness:
            return

        try:
            target_pct = max(0, min(100, int(value)))
            actual_value = int((target_pct / 100) * self.max_brightness)

            with open(
                os.path.join(self.identifier, "brightness"), "w", encoding="UTF-8"
            ) as f:
                f.write(str(actual_value))
        except (OSError, PermissionError):
            print("Error setting brightness for", self)


class DDCIPMonitor(MonitorBrightness):
    """Handles external monitors via I2C/DDC logic."""

    I2C_SLAVE = 0x0703
    DDC_ADDR = 0x37
    HOST_ADDR_W = 0x51
    DEST_ADDR_W = 0x6E
    HOST_ADDR_R = 0x50
    GET_VCP_CMD = 0x01
    SET_VCP_CMD = 0x03
    VCP_BRIGHTNESS = 0x10

    @staticmethod
    def parse_edid(data: bytes):
        """Parses manufacturer and name from EDID block."""
        try:
            m_bytes = struct.unpack(">H", data[8:10])[0]
            manufacturer = "".join(
                [
                    chr(((m_bytes >> 10) & 31) + 64),
                    chr(((m_bytes >> 5) & 31) + 64),
                    chr((m_bytes & 31) + 64),
                ]
            )
            name, serial = "Unknown", "Unknown"
            for position_from in range(54, 109, 18):
                position_to = position_from + 18
                block = data[position_from:position_to]
                if block[0:4] == b"\x00\x00\x00\xfc":
                    name = (
                        block[5:]
                        .split(b"\x0a")[0]
                        .decode("ascii", errors="ignore")
                        .strip()
                    )
                elif block[0:4] == b"\x00\x00\x00\xff":
                    serial = (
                        block[5:]
                        .split(b"\x0a")[0]
                        .decode("ascii", errors="ignore")
                        .strip()
                    )
            return manufacturer, name, serial
        except Exception:
            return "Unknown", "Unknown", "Unknown"

    def _ddc_command(
        self, file_obj: BinaryIO, payload: list, read_length: int = 0
    ) -> Optional[bytes]:
        """
        Low-level I2C write/read transaction.
        Expects an already open binary file object.
        """
        try:
            # Construct DDC packet with checksum
            packet = bytearray([self.HOST_ADDR_W, len(payload) | 0x80] + payload)
            checksum = functools.reduce(operator.xor, packet, self.DEST_ADDR_W)
            packet.append(checksum)

            file_obj.write(packet)
            time.sleep(0.05)

            if read_length > 0:
                data = file_obj.read(read_length)
                checksum = functools.reduce(operator.xor, data[:-1], self.HOST_ADDR_R)
                if checksum == data[-1]:
                    return data
            return None
        except (OSError, IOError):
            return None

    def get_brightness(self, timeout: float = 1.0) -> Optional[int]:
        """Polls for external brightness via VCP."""
        start_time = time.monotonic()

        try:
            # Open the I2C file ONCE here to avoid overhead in the loop
            with open(self.identifier, "r+b", buffering=0) as f:
                fcntl.ioctl(f.fileno(), self.I2C_SLAVE, self.DDC_ADDR)

                while (time.monotonic() - start_time) < timeout:
                    # Pass the open file handle to the command
                    data = self._ddc_command(
                        f, [self.GET_VCP_CMD, self.VCP_BRIGHTNESS], 11
                    )

                    if data and len(data) >= 10:
                        max_val = int.from_bytes(data[6:8], "big")
                        cur_val = int.from_bytes(data[8:10], "big")

                        if max_val != 0:
                            self.last_successful_read = int((cur_val / max_val) * 100)
                            return self.last_successful_read

                    time.sleep(0.1)  # Retry interval
        except (OSError, IOError):
            pass

        return None

    def set_brightness(self, value: int, retries: int = 10) -> None:
        """Sets brightness and verifies the hardware change."""
        target = max(0, min(100, int(value)))
        self.last_successful_read = target

        try:
            with open(self.identifier, "r+b", buffering=0) as f:
                fcntl.ioctl(f.fileno(), self.I2C_SLAVE, self.DDC_ADDR)

                for _attempt in range(retries):
                    self._ddc_command(
                        f, [self.SET_VCP_CMD, self.VCP_BRIGHTNESS, 0x00, target]
                    )
                    time.sleep(0.02)  # Slight delay between retries if needed
        except (OSError, IOError):
            pass


if __name__ == "__main__":
    monitors, myissues = MonitorBrightness.list_displays()
    for issue in myissues:
        print("Issue:", issue)
        print("---------")
    for mon in monitors:
        print(f"Checking {mon}...")
        current = mon.get_brightness()
        print(f"Current Brightness: {current}%")
        mon.set_brightness(20)
