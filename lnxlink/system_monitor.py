"""Monitors for shutdown/sleep events"""

import time
import threading
import signal
import logging
import traceback
from jeepney import MatchRule, DBus
from jeepney.io.blocking import open_dbus_connection, Proxy


logger = logging.getLogger("lnxlink")


class MonitorSuspend:
    """Monitor DBUS for Suspend and Shutdown events"""

    def __init__(self, callback):
        self.callback = callback
        self.use = False
        try:
            self.connection = open_dbus_connection(bus="SYSTEM")
            bus_proxy = Proxy(DBus(), self.connection)
            sleep_match = MatchRule(
                type="signal",
                interface="org.freedesktop.login1.Manager",
                member="PrepareForSleep",
                path="/org/freedesktop/login1",
            )
            bus_proxy.AddMatch(sleep_match)

            self.timer1 = threading.Thread(target=self.watch_loop, daemon=True)
            self.use = True
        except Exception as err:
            logger.error(
                "Can't use DBus: %s, %s",
                err,
                traceback.format_exc(),
            )

    def watch_loop(self):
        """Run the dbus check for new sleep messages"""
        errors = 0
        while True:
            try:
                message = self.connection.receive()
                self.callback(message.body[0])
                errors = 0
            except Exception as err:
                logger.error(
                    "DBus Error: %s, %s",
                    err,
                    traceback.format_exc(),
                )
                time.sleep(1)
                errors += 1
                if errors > 10:
                    break

    def start(self):
        """Start the timer of the thread"""
        if self.use:
            try:
                self.timer1.start()
            except Exception as err:
                logger.error(
                    "Can't start systemMonitor: %s, %s",
                    err,
                    traceback.format_exc(),
                )

    def stop(self):
        """Stop the timer of the thread"""
        if self.use:
            try:
                self.connection.close()
            except Exception as err:
                logger.error(
                    "Can't stop systemMonitor: %s, %s",
                    err,
                    traceback.format_exc(),
                )


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
