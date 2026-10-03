"""Read battery levels of Logitech devices by talking HID++ over hidraw

Devices behind a receiver the kernel doesn't recognise (the Logi Bolt 046d:c548
for one, missing from the hid-logitech-dj table) never reach UPower, so their
battery is invisible to the whole system. Asking them directly over /dev/hidraw
fills that gap. Devices the kernel does drive are left alone, UPower already
reports those.

Opening /dev/hidraw* needs permissions which no distro grants by default. A
udev rule handing them to the seat user is enough:

    SUBSYSTEM=="hidraw", ATTRS{idVendor}=="046d", TAG+="uaccess"

Without it nothing is reported and nothing breaks.
"""
import glob
import logging
import os
import select
import time

logger = logging.getLogger("lnxlink")

LOGITECH_VENDOR = "046D"
KERNEL_DRIVER = "logitech-hidpp-device"

REPORT_SHORT = 0x10
REPORT_LONG = 0x11
ERROR_HIDPP1 = 0x8F
ERROR_HIDPP2 = 0xFF
RESPONSE_TIMEOUT = 0.6
REQUEST_ATTEMPTS = 2
MAX_SLOTS = 6

FEATURE_ROOT = 0x0000
FEATURE_DEVICE_NAME = 0x0005
FEATURE_BATTERY_STATUS = 0x1000
FEATURE_UNIFIED_BATTERY = 0x1004


class HidPP:
    """A HID++ conversation with one hidraw node"""

    def __init__(self, node):
        """Open the node for the exchange"""
        self.fd = os.open(f"/dev/{node}", os.O_RDWR | os.O_NONBLOCK)
        self.software_id = 0

    def close(self):
        """Close the node"""
        os.close(self.fd)

    def _drain(self):
        """Drop unsolicited reports queued up before a request"""
        while select.select([self.fd], [], [], 0)[0]:
            try:
                os.read(self.fd, 64)
            except OSError:
                return

    def request(self, slot, feature, function, params=b""):
        """Send one HID++ request and wait for its answer

        The software id in the low nibble of the tag changes on every request,
        otherwise a late answer to the previous one is taken for this reply.
        """
        for _ in range(REQUEST_ATTEMPTS):
            self.software_id = self.software_id % 15 + 1
            tag = (function << 4) | self.software_id
            self._drain()
            header = bytes([REPORT_SHORT, slot, feature, tag])
            try:
                os.write(self.fd, header + params.ljust(3, b"\x00"))
            except OSError as err:
                logger.debug("HID++ write failed: %s", err)
                return None
            deadline = time.time() + RESPONSE_TIMEOUT
            while True:
                left = deadline - time.time()
                if left <= 0 or not select.select([self.fd], [], [], left)[0]:
                    break
                try:
                    data = os.read(self.fd, 64)
                except OSError:
                    continue
                if len(data) < 4 or data[0] not in (REPORT_SHORT, REPORT_LONG):
                    continue
                if data[1] != slot:
                    continue
                if data[2] in (ERROR_HIDPP1, ERROR_HIDPP2):
                    # An error names the request it belongs to, so a late one
                    # from an earlier exchange doesn't cut this one short
                    if len(data) > 4 and data[3] == feature and data[4] == tag:
                        return None
                    continue
                if data[2] == feature and data[3] == tag:
                    return data[4:]
        return None

    def feature_index(self, slot, feature_id):
        """Resolve a HID++ 2.0 feature id to the index this device gave it"""
        params = bytes([feature_id >> 8, feature_id & 0xFF, 0])
        reply = self.request(slot, FEATURE_ROOT, 0x00, params)
        if reply and reply[0]:
            return reply[0]
        return None

    def ping(self, slot):
        """Check if any device answers on this slot"""
        return self.request(slot, FEATURE_ROOT, 0x01, b"\x00\x00\xaf") is not None

    def device_name(self, slot):
        """Friendly name of the device and its HID++ device type code"""
        index = self.feature_index(slot, FEATURE_DEVICE_NAME)
        if index is None:
            return None, None
        reply = self.request(slot, index, 0x02, b"\x00")
        device_type = reply[0] if reply else None
        length = self.request(slot, index, 0x00)
        if not length:
            return None, device_type
        name = ""
        for position in range(0, length[0], 16):
            chunk = self.request(slot, index, 0x01, bytes([position]))
            if not chunk:
                break
            name += chunk.decode("latin1")
        return name[: length[0]].rstrip("\x00") or None, device_type

    def battery(self, slot):
        """Charge percentage and HID++ charge state code of the device"""
        index = self.feature_index(slot, FEATURE_UNIFIED_BATTERY)
        if index is not None:
            reply = self.request(slot, index, 0x01)
            if reply:
                return reply[0], reply[2]
        index = self.feature_index(slot, FEATURE_BATTERY_STATUS)
        if index is not None:
            reply = self.request(slot, index, 0x00)
            if reply:
                return reply[0], reply[2]
        return None, None


def _uevent(hid_path):
    """Read a hid device uevent into a dictionary"""
    attributes = {}
    try:
        with open(os.path.join(hid_path, "uevent"), encoding="utf8") as uevent:
            for line in uevent:
                key, _, value = line.strip().partition("=")
                attributes[key] = value
    except OSError:
        return None
    return attributes


def _speaks_hidpp(hid_path):
    """Check if the report descriptor declares both HID++ reports"""
    try:
        with open(os.path.join(hid_path, "report_descriptor"), "rb") as descriptor:
            report_descriptor = descriptor.read()
    except OSError:
        return False
    return all(
        marker in report_descriptor
        for marker in (b"\x06\x00\xff", b"\x85\x10", b"\x85\x11")
    )


def _nodes():
    """Find the Logitech hidraw nodes worth asking, as (node, claimed slots)

    A node driven by the kernel HID++ driver is skipped outright, UPower knows
    about it already. The slots of a receiver's kernel driven children are
    claimed for the same reason, and skipping them also keeps us off a radio
    channel the kernel is using, where the two conversations answer each other.
    """
    candidates = []
    kernel_driven = []
    for sysfs in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        hid_path = os.path.join(sysfs, "device")
        attributes = _uevent(hid_path)
        if attributes is None:
            continue
        if LOGITECH_VENDOR not in attributes.get("HID_ID", "").upper():
            continue
        phys = attributes.get("HID_PHYS", "")
        driver = os.path.basename(os.path.realpath(os.path.join(hid_path, "driver")))
        if driver == KERNEL_DRIVER:
            kernel_driven.append(phys)
        elif _speaks_hidpp(hid_path):
            candidates.append((os.path.basename(sysfs), phys))

    for node, phys in candidates:
        claimed = set()
        for child_phys in kernel_driven:
            # A child of this receiver is its phys with the slot appended
            if child_phys.startswith(f"{phys}:"):
                slot = child_phys[len(phys) + 1 :]
                if slot.isdigit():
                    claimed.add(int(slot))
        yield node, claimed


def _node_batteries(hidpp, node, claimed):
    """Ask every unclaimed slot of one node for its battery"""
    batteries = []
    for slot in range(1, MAX_SLOTS + 1):
        if slot in claimed or not hidpp.ping(slot):
            continue
        percent, charge_state = hidpp.battery(slot)
        if percent is None:
            continue
        name, device_type = hidpp.device_name(slot)
        batteries.append(
            {
                "name": name,
                "device_type": device_type,
                "percent": percent,
                "charge_state": charge_state,
                "node": node,
                "slot": slot,
            }
        )
    return batteries


def get_batteries():
    """Gets every Logitech HID++ device the kernel leaves unreported"""
    batteries = []
    for node, claimed in _nodes():
        try:
            hidpp = HidPP(node)
        except OSError as err:
            logger.debug("Can't open %s to read HID++ batteries: %s", node, err)
            continue
        try:
            batteries.extend(_node_batteries(hidpp, node, claimed))
        except OSError as err:
            logger.debug("Failed reading HID++ batteries from %s: %s", node, err)
        finally:
            hidpp.close()
    return batteries
