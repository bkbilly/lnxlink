from dbus_idle import IdleMonitor


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Idle'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:timer-sand'
        self.unit = 's'
        self.state_class = 'total_increasing'
        self.device_class = 'duration'

    def getInfo(self):
        monitor = IdleMonitor.get_monitor()
        idle_ms = monitor.get_dbus_idle()
        idle_sec = round(idle_ms / 1000, 0)
        return idle_sec
