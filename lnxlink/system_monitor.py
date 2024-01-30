"""Monitors for shutdown/sleep events"""

import threading
import signal
import logging
import traceback

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

logger = logging.getLogger("lnxlink")


class MonitorSuspend:
    """Monitor DBUS for Suspend and Shutdown events"""

    def __init__(self, callback):
        self.use = False
        try:
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
            self.use = True
        except Exception as err:
            logger.error(
                "Can't use DBus: %s, %s",
                err,
                traceback.format_exc(),
            )

    def start(self):
        """Start the timer of the thread"""
        if self.use:
            self.timer1.start()

    def stop(self):
        """Stop the timer of the thread"""
        if self.use:
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
