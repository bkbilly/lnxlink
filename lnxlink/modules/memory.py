import psutil


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Memory Usage'

    def exposedControls(self):
        return {
            "Memory Usage": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "%",
                "state_class": "measurement",
                "value_template": "{{ value_json.percent }}",
            },
            "Memory Used": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.used }}",
                "enabled": False,
            },
            "Memory Available": {
                "type": "sensor",
                "icon": "mdi:memory",
                "unit": "MB",
                "state_class": "measurement",
                "device_class": "data_size",
                "value_template": "{{ value_json.available }}",
                "enabled": False,
            },
        }

    def getControlInfo(self):
        vmem = psutil.virtual_memory()
        return {
            "percent": vmem.percent,
            "used": round(vmem.used / 1024 ** 2, 0),
            "available": round(vmem.available / 1024 ** 2, 0),
        }
