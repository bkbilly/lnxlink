"""Choose which operating system to load on the next boot"""
import os
import re
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Boot Select"
        self.lnxlink = lnxlink

        if which("efibootmgr") is None:
            raise SystemError("System command 'efibootmgr' not found")

        _, stderr, returncode = syscommand("sudo -n efibootmgr", ignore_errors=True)
        if returncode != 0:
            raise SystemError(
                f"Boot Select permission issue: {stderr}\n"
                "Please add the following to /etc/sudoers using 'sudo visudo':\n"
                f"{self._get_username()} ALL=(ALL) NOPASSWD: /usr/bin/efibootmgr"
            )

        self.boot_entries = self._get_boot_entries()
        if not self.boot_entries:
            raise SystemError("No EFI boot entries found")

        self.options = [entry["label"] for entry in self.boot_entries]

    def get_info(self):
        """Gather information from the system"""
        stdout, _, returncode = syscommand("sudo -n efibootmgr", ignore_errors=True)
        if returncode != 0:
            return ""

        # Get BootNext value
        bootnext_pattern = re.compile(r"^BootNext:\s*([0-9A-Fa-f]{4})")
        for line in stdout.split("\n"):
            match = bootnext_pattern.match(line)
            if match:
                boot_num = match.group(1)
                # Find the corresponding label
                for entry in self.boot_entries:
                    if entry["num"] == boot_num:
                        return entry["label"]

        # If no BootNext is set, return the current boot order's first entry
        bootorder_pattern = re.compile(r"^BootOrder:\s*([0-9A-Fa-f,]+)")
        for line in stdout.split("\n"):
            match = bootorder_pattern.match(line)
            if match:
                first_boot = match.group(1).split(",")[0]
                for entry in self.boot_entries:
                    if entry["num"] == first_boot:
                        return entry["label"]

        return ""

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Boot Select": {
                "type": "select",
                "icon": "mdi:harddisk-plus",
                "options": self.options,
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        boot_num = None
        for entry in self.boot_entries:
            if entry["label"] == data:
                boot_num = entry["num"]
                break

        if boot_num:
            syscommand(f"sudo -n efibootmgr --bootnext {boot_num}")

    def _get_boot_entries(self):
        """Get all EFI boot entries"""
        stdout, _, returncode = syscommand("sudo -n efibootmgr", ignore_errors=True)
        if returncode != 0:
            return []

        boot_entries = []
        entry_pattern = re.compile(r"^Boot([0-9A-Fa-f]{4})\*?\s+(.+)$")

        for line in stdout.split("\n"):
            match = entry_pattern.match(line)
            if match:
                boot_num = match.group(1)
                full_label = match.group(2).strip()

                if "\t" in full_label:
                    label = full_label.split("\t")[0].strip()
                elif "HD(" in full_label:
                    label = full_label.split("HD(")[0].strip()
                elif "PciRoot(" in full_label:
                    label = full_label.split("PciRoot(")[0].strip()
                else:
                    label = full_label

                label_with_num = f"{label} ({boot_num})"
                boot_entries.append({"num": boot_num, "label": label_with_num})

        return boot_entries

    def _get_username(self):
        """Get the current username"""
        return os.getenv("USER", os.getenv("USERNAME", "user"))
