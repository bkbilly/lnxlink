import subprocess
import jc


class Addon():
    def __init__(self, lnxlink):
        self.name = 'Battery'

    def exposedControls(self):
        return {
            "Battery": {
                "type": "sensor",
                "icon": "mdi:battery",
                "unit": "%",
                "device_class": "battery",
                "value_template": "{{ value_json.status }}",
                "enabled": False,
            },
        }


    def getControlInfo(self):
        stdout = subprocess.run(
            'upower --dump',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        upower_json = jc.parse('upower', stdout)

        devices = {'status': None}
        for device in upower_json:
            if 'detail' in device:
                if 'percentage' in device['detail']:
                    name = ''.join([
                        device.get('vendor', ''),
                        device.get('model', ''),
                    ]).strip()
                    if name != "":
                        devices[name] = device['detail']['percentage']
                        if devices['status'] is None:
                            devices['status'] = device['detail']['percentage']
        return devices
