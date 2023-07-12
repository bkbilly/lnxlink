import subprocess
import re


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Keep Alive'
        self.keepalive = 'OFF'

    def exposedControls(self):
        return {
            "Keep Alive": {
                "type": "switch",
                "icon": "mdi:mouse-variant",
            }
        }

    def getControlInfo(self):
        enabled_list = []

        # Check if Gnome Idle Time is active
        stdout_dim = subprocess.run(
            'gsettings get org.gnome.desktop.session idle-delay',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        stdout_suspend = subprocess.run(
            'gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        if stdout_dim != '':
            disabled_dim = '0' == stdout_dim.split()[1]
            if disabled_dim and stdout_suspend != '':
                enabled_list.append('nothing' in stdout_suspend)

        # Check if DPMS is active
        stdout_xset = subprocess.run(
            'xset q',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        xset_pattern = re.compile(r"Standby: (\d+)\s+Suspend: (\d+)\s+Off: (\d+)")
        xset_match = re.findall(xset_pattern, stdout_xset)
        for nums in xset_match:
            enabled_list.append(all(num != '0' for num in nums))
            if enabled_list[-1]:
                enabled_list.append('DPMS is Enabled' in stdout_xset)

        return any(enabled_list)


    def startControl(self, topic, data):
        if data.lower() == 'off':
            subprocess.run(
                'gsettings set org.gnome.desktop.session idle-delay 600',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            subprocess.run(
                'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "suspend"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            subprocess.run(
                'xset +dpms',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        elif data.lower() == 'on':
            subprocess.run(
                'gsettings set org.gnome.desktop.session idle-delay 0',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            subprocess.run(
                'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "nothing"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            subprocess.run(
                'xset -dpms',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)


print(Addon("").startControl("", "off"))
