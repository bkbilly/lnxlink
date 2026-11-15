"""Track memory usage and availability"""
import glob
import logging
import os
import re
import shutil

import psutil

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


def _format_bytes(num_bytes):
    """Format bytes into a human-readable string (e.g. 16.0 GB, 30.3 GB)"""
    if not num_bytes or num_bytes <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num_bytes < 1024 or unit == "PB":
            val = round(num_bytes, 1)
            if val.is_integer():
                val = int(val)
            return f"{val} {unit}"
        num_bytes /= 1024
    return f"{num_bytes} B"


def _format_size_str(size_str):
    """Convert size string like '16384 MB' to human-readable format like '16 GB'"""
    if not size_str:
        return ""
    match = re.match(r"^([\d.]+)\s*([a-zA-Z]+)?", str(size_str).strip())
    if not match:
        return str(size_str)
    val = float(match.group(1))
    unit = (match.group(2) or "MB").upper()
    multipliers = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024**2,
        "M": 1024**2,
        "GB": 1024**3,
        "G": 1024**3,
        "TB": 1024**4,
        "T": 1024**4,
    }
    bytes_num = val * multipliers.get(unit, 1024**2)
    return _format_bytes(bytes_num)


class MemoryDIMMs:
    """Extract memory DIMM hardware information without root privileges"""

    dram_types = {
        0x0B: "DDR3",
        0x0C: "DDR4",
        0x0E: "DDR4E",
        0x0F: "LPDDR4",
        0x10: "LPDDR4X",
        0x11: "LPDDR5",
        0x12: "DDR5",
    }
    module_types = {
        0x01: "RDIMM",
        0x02: "UDIMM",
        0x03: "SO-DIMM",
        0x04: "LRDIMM",
    }

    def __init__(self):
        self.info = self._get_dimm_info()

    @staticmethod
    def _clean_str(val):
        """Clean and validate string attribute values"""
        if not val:
            return ""
        val = str(val).strip("\x00 \t\r\n")
        if val.lower() in [
            "unknown",
            "not specified",
            "none",
            "not provided",
            "no dimm",
            "-",
        ]:
            return ""
        return val

    @staticmethod
    def _get_dimm_slots_total():
        """Get total number of physical memory slots from DMI sysfs entries"""
        entries = glob.glob("/sys/firmware/dmi/entries/17-*")
        if entries:
            return len(entries)
        return None

    def _get_from_decode_dimms(self):
        """Extract DIMM information using decode-dimms tool"""
        if not shutil.which("decode-dimms"):
            return None
        stdout, _, returncode = syscommand("decode-dimms", ignore_errors=True)
        if returncode != 0 or "Decoding EEPROM:" not in stdout:
            return None

        installed = []
        mapping = [
            ("Guessing DIMM is in", "Slot"),
            ("Size", "Size"),
            ("Fundamental Memory type", "Type"),
            ("Module Type", "Form Factor"),
            ("Maximum module speed", "Speed"),
            ("Module Manufacturer", "Manufacturer"),
            ("DRAM Manufacturer", "DRAM Manufacturer"),
            ("Part Number", "Part Number"),
            ("Module Nominal Voltage", "Voltage"),
            ("Ranks", "Rank"),
        ]
        blocks = stdout.split("Decoding EEPROM: ")
        for block in blocks[1:]:
            raw_dimm = {}
            for line in block.splitlines():
                if "---===" in line or not line.strip():
                    continue
                parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
                if len(parts) == 2:
                    raw_dimm[parts[0].strip()] = parts[1].strip()

            dimm = {}
            for src, dst in mapping:
                val = self._clean_str(raw_dimm.get(src))
                if val:
                    dimm[dst] = val
            if dimm:
                installed.append(dimm)

        if not installed:
            return None

        return {
            "dimm_count": len(installed),
            "slots_total": self._get_dimm_slots_total(),
            "dimms_details": installed,
        }

    def _get_from_sysfs_eeprom(
        self,
    ):  # pylint: disable=too-many-locals,too-many-branches
        """Extract DIMM information from I2C EEPROMs in sysfs"""
        paths = sorted(
            glob.glob("/sys/bus/i2c/devices/*-005[0-7]/eeprom")
            + glob.glob("/sys/bus/i2c/drivers/*/*/eeprom")
        )
        seen = set()
        installed = []
        for path in paths:
            try:
                realpath = os.path.realpath(path)
                if realpath in seen:
                    continue
                seen.add(realpath)
                with open(realpath, "rb") as file:
                    data = file.read(512)
                if len(data) < 128:
                    continue
                dram_byte = data[2]
                dram_type = self.dram_types.get(dram_byte)
                if not dram_type:
                    continue
                dimm = {"Type": dram_type}
                mod_byte = data[3] & 0x0F
                if mod_byte in self.module_types:
                    dimm["Form Factor"] = self.module_types[mod_byte]

                addr_match = re.search(r"(\d+)-005([0-7])", realpath)
                if addr_match:
                    dimm["Slot"] = f"Slot {int(addr_match.group(2)) + 1}"

                part_no = ""
                if dram_byte == 0x0C and len(data) >= 349:
                    part_no = (
                        data[329:349]
                        .decode("latin1", errors="replace")
                        .strip("\x00 \t\r\n")
                    )
                elif dram_byte == 0x0B and len(data) >= 146:
                    part_no = (
                        data[128:146]
                        .decode("latin1", errors="replace")
                        .strip("\x00 \t\r\n")
                    )
                elif dram_byte == 0x12 and len(data) >= 551:
                    part_no = (
                        data[521:551]
                        .decode("latin1", errors="replace")
                        .strip("\x00 \t\r\n")
                    )
                if part_no:
                    dimm["Part Number"] = part_no

                if dram_byte == 0x0C and len(data) >= 14:
                    cap_map = {
                        0: 256,
                        1: 512,
                        2: 1024,
                        3: 2048,
                        4: 4096,
                        5: 8192,
                        6: 16384,
                        7: 32768,
                    }
                    die_cap = cap_map.get(data[4] & 0x0F, 0)
                    width_map = {0: 4, 1: 8, 2: 16, 3: 32}
                    dev_width = width_map.get(data[12] & 0x07, 8)
                    ranks = ((data[12] >> 3) & 0x07) + 1
                    bus_width_map = {0: 8, 1: 16, 2: 32, 3: 64}
                    bus_width = bus_width_map.get(data[13] & 0x07, 64)
                    if dev_width > 0 and die_cap > 0:
                        total_mb = (die_cap // 8) * (bus_width // dev_width) * ranks
                        dimm["Size"] = f"{total_mb} MB"
                    dimm["Rank"] = str(ranks)

                installed.append(dimm)
            except OSError:
                continue

        if not installed:
            return None

        return {
            "dimm_count": len(installed),
            "slots_total": self._get_dimm_slots_total(),
            "dimms_details": installed,
        }

    def _get_from_edac(self):
        """Extract DIMM information from EDAC sysfs"""
        dimm_dirs = sorted(glob.glob("/sys/devices/system/edac/mc/mc*/dimm*"))
        if not dimm_dirs:
            return None
        installed = []
        for d in dimm_dirs:
            dimm = {}
            for fname, key in [
                ("dimm_label", "Slot"),
                ("size", "Size"),
                ("dimm_dev_type", "Type"),
                ("dimm_location", "Location"),
            ]:
                path = os.path.join(d, fname)
                if os.path.isfile(path):
                    try:
                        with open(path, encoding="utf-8", errors="replace") as file:
                            val = self._clean_str(file.read())
                            if val:
                                if key == "Size" and val.isdigit():
                                    val = f"{val} MB"
                                dimm[key] = val
                    except OSError:
                        continue
            if dimm and (dimm.get("Size") or dimm.get("Slot")):
                installed.append(dimm)
        if not installed:
            return None
        return {
            "dimm_count": len(installed),
            "slots_total": self._get_dimm_slots_total(),
            "dimms_details": installed,
        }

    def _get_dimm_info(self):
        """Gather DIMM and memory hardware information without root"""
        info = (
            self._get_from_decode_dimms()
            or self._get_from_sysfs_eeprom()
            or self._get_from_edac()
            or {}
        )

        if "slots_total" not in info or info["slots_total"] is None:
            slots_total = self._get_dimm_slots_total()
            if slots_total:
                info["slots_total"] = slots_total

        details = info.get("dimms_details", [])
        if "dimm_count" not in info and details:
            info["dimm_count"] = len(details)

        if info.get("slots_total") and info.get("dimm_count"):
            info["slots_total"] = max(info["slots_total"], info["dimm_count"])

        if details:
            types = []
            for d in details:
                if "Size" in d:
                    d["Size"] = _format_size_str(d["Size"])
                t = d.get("Type")
                if t and t not in types:
                    types.append(t)
            if types:
                info["ram_type"] = ", ".join(types)

        return info


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Memory Usage"
        self.lnxlink = lnxlink
        self.dimm_info = MemoryDIMMs().info

    def exposed_controls(self):
        """Exposes to home assistant"""
        att_template = "{{ value_json.get('attributes', {}) | tojson }}"
        return {
            "Memory Usage": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "%",
                "state_class": "measurement",
                "value_template": "{{ value_json.percent }}",
                "attributes_template": att_template,
            },
            "Memory Used": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.used }}",
                "attributes_template": att_template,
                "enabled": False,
            },
            "Memory Free": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.free }}",
                "attributes_template": att_template,
                "enabled": False,
            },
            "Memory Swap Usage": {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "%",
                "state_class": "measurement",
                "value_template": "{{ value_json.swap_percent }}",
                "attributes_template": att_template,
                "enabled": False,
            },
            "Memory Swap Used": {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.swap_used }}",
                "attributes_template": att_template,
                "enabled": False,
            },
            "Memory Swap Free": {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.swap_free }}",
                "attributes_template": att_template,
                "enabled": False,
            },
        }

    def get_info(self):
        """Gather information from the system"""
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        attributes = {}
        if (
            self.dimm_info.get("slots_total") is not None
            and self.dimm_info.get("dimm_count") is not None
        ):
            attributes[
                "DIMM Slots"
            ] = f"{self.dimm_info['dimm_count']}/{self.dimm_info['slots_total']}"
        elif self.dimm_info.get("slots_total") is not None:
            attributes["DIMM Slots"] = f"{self.dimm_info['slots_total']}"
        elif self.dimm_info.get("dimm_count") is not None:
            attributes["DIMM Slots"] = f"{self.dimm_info['dimm_count']}"

        if self.dimm_info.get("ram_type"):
            attributes["RAM Type"] = self.dimm_info["ram_type"]

        attributes["Total"] = _format_bytes(vmem.total)
        attributes["Swap Total"] = _format_bytes(swap.total)

        for idx, dimm in enumerate(self.dimm_info.get("dimms_details", []), start=1):
            attributes[f"DIMM {idx} details"] = dimm

        return {
            "percent": round(vmem.percent, 0),
            "used": round(vmem.used / 1024**2, 0),
            "free": round(vmem.free / 1024**2, 0),
            "swap_percent": round(swap.percent, 0),
            "swap_used": round(swap.used / 1024**2, 0),
            "swap_free": round(swap.free / 1024**2, 0),
            "attributes": attributes,
        }
