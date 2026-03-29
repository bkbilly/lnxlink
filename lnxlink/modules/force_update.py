"""Force an immediate poll of all modules on demand"""
import logging
import threading

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Force Update"
        self.lnxlink = lnxlink
        self._running = False

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Force Update": {
                "type": "button",
                "icon": "mdi:refresh",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if self._running:
            logger.warning(
                "Force Update already in progress, ignoring duplicate request"
            )
            return
        threading.Thread(target=self._poll_all, daemon=True).start()

    def _poll_all(self):
        """Poll every non-streaming addon that exposes get_info."""
        self._running = True
        logger.info("Force Update started")
        try:
            for service, addon in list(self.lnxlink.addons.items()):
                if not hasattr(addon, "get_info"):
                    logger.debug(
                        "Force Update skipping module with no get_info: %s", service
                    )
                    continue

                try:
                    self.lnxlink.run_module(addon.name, addon.get_info)
                except Exception as err:
                    logger.error(
                        "Force Update error polling module %s: %s", service, err
                    )
        finally:
            self._running = False
            logger.info("Force Update finished")
