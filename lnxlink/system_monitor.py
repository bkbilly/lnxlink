"""Monitors for shutdown/sleep events"""

import threading
import signal
import logging
import traceback

from lnxlink.modules.scripts.helpers import import_install_package

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
            bus = self.lib["dbus"].connection.SystemMessageBus()

            proxy = bus.get_proxy(
                service_name="org.freedesktop.login1",
                object_path="/org/freedesktop/login1",
                interface_name="org.freedesktop.login1.Manager",
            )
            proxy.PrepareForSleep.connect(callback)
            proxy.PrepareForShutdown.connect(callback)

            self.loop = self.lib["dbus-loop"].loop.EventLoop()
            self.timer1 = threading.Thread(target=self.loop.run, daemon=True)
            self.use = True
        except Exception as err:
            logger.error(
                "Can't use DBus: %s, %s",
                err,
                traceback.format_exc(),
            )

    def _requirements(self):
        import_install_package("PyGObject", ">=3.44.0", "gi")
        dbus = import_install_package("dasbus", ">=1.7", "dasbus.connection")
        if dbus is None:
            self.lib = {"dbus": dbus}
            return
        self.lib = {
            "dbus": dbus,
            "dbus-loop": import_install_package("dasbus", ">=1.7", "dasbus.loop"),
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
