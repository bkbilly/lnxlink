"""Gets the network usage"""
from datetime import datetime
import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Network"
        self.time_old = datetime.now()
        self.recv_old = psutil.net_io_counters().bytes_recv
        self.sent_old = psutil.net_io_counters().bytes_sent

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Network Upload": {
                "type": "sensor",
                "icon": "mdi:access-point-network",
                "unit": "Mbit/s",
                "state_class": "measurement",
                "device_class": "data_rate",
                "value_template": "{{ value_json.upload }}",
            },
            "Network Download": {
                "type": "sensor",
                "icon": "mdi:access-point-network",
                "unit": "Mbit/s",
                "state_class": "measurement",
                "device_class": "data_rate",
                "value_template": "{{ value_json.download }}",
            },
        }

    def get_info(self):
        """Returns Mbps"""
        time_new = datetime.now()
        netio = psutil.net_io_counters()
        recv_new = netio.bytes_recv
        sent_new = netio.bytes_sent

        time_diff = (time_new - self.time_old).total_seconds()
        self.time_old = time_new

        recv_diff = recv_new - self.recv_old
        sent_diff = sent_new - self.sent_old
        self.recv_old = recv_new
        self.sent_old = sent_new

        recv_speed = max(0, round(recv_diff * 8 / time_diff / 1024 / 1024, 2))
        sent_speed = max(0, round(sent_diff * 8 / time_diff / 1024 / 1024, 2))

        return {
            "upload": sent_speed,
            "download": recv_speed,
        }
