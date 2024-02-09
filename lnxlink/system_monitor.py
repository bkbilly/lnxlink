"""Monitors for shutdown/sleep events"""

import threading
import signal
import logging
import traceback

from .modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class MonitorSuspend:
    """Monitor DBUS for Suspend and Shutdown events"""

    def __init__(self, callback):
        self.use = False
        self._requirements()
        if self.lib["dbus"] is None:
            logger.error("Can't use DBus for system monitor")
            return
        try:
            dbus_loop = self.lib["dbus-loop"].mainloop.glib.DBusGMainLoop(
                set_as_default=True
            )  # integrate into main loob
            bus = self.lib["dbus"].SystemBus(
                mainloop=dbus_loop
            )  # connect to dbus system wide
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
            self.loop = self.lib["glib"].repository.GLib.MainLoop()
            self.timer1 = threading.Thread(target=self.loop.run)
            self.use = True
        except Exception as err:
            logger.error(
                "Can't use DBus: %s, %s",
                err,
                traceback.format_exc(),
            )

    def _requirements(self):
        dbus = import_install_package("dbus-python", ">=1.3.2", "dbus")
        if dbus is None:
            self.lib = {"dbus": dbus}
            return
        self.lib = {
            "dbus": dbus,
            "dbus-loop": import_install_package(
                "dbus-python", ">=1.3.2", "dbus.mainloop.glib"
            ),
            "cairo": import_install_package("pycairo", ">=1.24.0", "cairo"),
            "glib": import_install_package(
                "PyGObject", ">=3.44.0", "gi.repository.GLib"
            ),
        }

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
