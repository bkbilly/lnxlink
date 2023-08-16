"""Gets CPU usage information"""
import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "CPU Usage"
        self.sensor_type = "sensor"
        self.icon = "mdi:speedometer"
        self.unit = "%"
        self.state_class = "measurement"

    def get_old_info(self):
        """Gather information from the system"""
        return psutil.cpu_percent()
