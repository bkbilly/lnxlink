"""Monitors for shutdown/sleep events"""

import threading
import signal
import logging

import dbus
from dbus.mainloop.glib import DBusGMainLoop

logger = logging.getLogger("lnxlink")

try:
    import pgi

    pgi.install_as_gi()
except ImportError:
    logger.error("Can't use PGI, so GI is used instead...")

from gi.repository import GLib


class MonitorSuspend:
    """Monitor DBUS for Suspend and Shutdown events"""

    def __init__(self, callback):
        dbus_loop = DBusGMainLoop(set_as_default=True)  # integrate into main loob
        bus = dbus.SystemBus(mainloop=dbus_loop)  # connect to dbus system wide
        bus.add_signal_receiver(  # defince the signal to listen to
            callback,  # name of callback function
            "PrepareForSleep",  # singal name
            "org.freedesktop.login1.Manager",  # interface
            "org.freedesktop.login1",  # bus name
        )
        bus.add_signal_receiver(  # defince the signal to listen to
            callback,  # name of callback function
            "PrepareForShutdown",  # singal name
            "org.freedesktop.login1.Manager",  # interface
            "org.freedesktop.login1",  # bus name
        )
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
