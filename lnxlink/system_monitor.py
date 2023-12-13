"""Monitors for shutdown/sleep events"""

import threading
import signal
import logging

from pydbus import SystemBus
from gi.repository import GLib

logger = logging.getLogger("lnxlink")


class MonitorSuspend:
    """Monitor DBUS for Suspend and Shutdown events"""

    def __init__(self, callback):
        try:
            bus = SystemBus()
            proxy = bus.get("org.freedesktop.login1", "/org/freedesktop/login1")
            proxy.PrepareForShutdown.connect(callback)
            proxy.PrepareForSleep.connect(callback)
        except Exception as err:
            logger.error("Can't connect D-Bus: %s", err)
        self.loop = GLib.MainLoop()
        self.timer1 = threading.Thread(target=self.loop.run)

    def start(self):
        """Start the timer of the thread"""
        self.timer1.start()

    def stop(self):
        """Stop the timer of the thread"""
        self.loop.quit()
        self.timer1.join()


class GracefulKiller:
    """Monitor Signal Termination"""

    def __init__(self, callback):
        """Checks for termination signals"""
        self.kill_now = False
        self.callback = callback
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """Stop the app gracefully"""
        logger.info("stopped gracefully")
        self.callback(1)
        self.kill_now = True
