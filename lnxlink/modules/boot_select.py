import subprocess
import re


class Addon():

    def __init__(self, lnxlink=None):
        self.name = 'Boot Select'
        self.options = self._get_grub_entries()

    def getControlInfo(self):
        stdout = subprocess.run(
            'grub-editenv list',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        nextentry_pattern = re.compile(r"^next_entry=(\d+)")
        nextentry_match = re.match(nextentry_pattern, stdout)
        entry_ind = 0
        if nextentry_match:
            entry_ind = int(nextentry_match.group(1))

        return self.options[entry_ind]

    def exposedControls(self):
        return {
            "Boot Select": {
                "type": "select",
                "icon": "mdi:harddisk-plus",
                "options": self.options,
            }
        }

    def startControl(self, topic, data):
        ind = self.options.index(data)
        subprocess.call(f"sudo grub-reboot {ind}", timeout=2, shell=True)

    def _get_grub_entries(self):
        menu_pattern = re.compile("^menuentry '([^']*)'")
        submenu_pattern = re.compile("^submenu '([^']*)'")

        grub_entries = []

        with open('/boot/grub/grub.cfg') as f:
            for line in f.readlines():
                menu_entry_match = re.match(menu_pattern, line)
                if menu_entry_match:
                    grub_entry = menu_entry_match.group(1)
                    grub_entries.append(grub_entry)

                submenu_entry_match = re.match(submenu_pattern, line)
                if submenu_entry_match:
                    grub_entry = submenu_entry_match.group(1)
                    grub_entries.append(grub_entry)

        return grub_entries
