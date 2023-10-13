"""Selects the OS to boot from on GRUB at the next restart"""
import re
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Boot Select"
        self.lnxlink = lnxlink
        self.options = self._get_grub_entries()

    def get_info(self):
        """Gather information from the system"""
        stdout, _, _ = syscommand("grub-editenv list")
        nextentry_pattern = re.compile(r"^next_entry=(\d+)")
        nextentry_match = re.match(nextentry_pattern, stdout)
        entry_ind = 0
        if nextentry_match:
            entry_ind = int(nextentry_match.group(1))

        return self.options[entry_ind]

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
        ind = self.options.index(data)
        syscommand(f"sudo grub-reboot {ind}")

    def _get_grub_entries(self):
        """Get the grub entities in the correct order"""
        menu_pattern = re.compile("^menuentry '([^']*)'")
        submenu_pattern = re.compile("^submenu '([^']*)'")

        grub_entries = []

        with open("/boot/grub/grub.cfg", encoding="UTF-8") as file:
            for line in file.readlines():
                menu_entry_match = re.match(menu_pattern, line)
                if menu_entry_match:
                    grub_entry = menu_entry_match.group(1)
                    grub_entries.append(grub_entry)

                submenu_entry_match = re.match(submenu_pattern, line)
                if submenu_entry_match:
                    grub_entry = submenu_entry_match.group(1)
                    grub_entries.append(grub_entry)

        return grub_entries
