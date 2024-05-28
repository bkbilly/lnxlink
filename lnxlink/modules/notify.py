"""Shows notifications"""
import time
import logging
import requests
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Notify OSD"
        self.lnxlink = lnxlink
        self._requirements()
        self.lib["dbus"].mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.urgencies = {
            "low": self.lib["notify2"].URGENCY_LOW,
            "normal": self.lib["notify2"].URGENCY_NORMAL,
            "critical": self.lib["notify2"].URGENCY_CRITICAL,
        }

    def _requirements(self):
        self.lib = {
            "dbus": import_install_package(
                "dbus-python", ">=1.3.2", "dbus.mainloop.glib"
            ),
            "notify2": import_install_package("notify2", ">=0.3.1"),
        }

    def start_control(self, topic, data):
        """Control system"""
        icon_url = data.get("iconUrl")
        sound_url = data.get("sound")
        timeout = data.get("timeout")
        urgency = data.get("urgency")
        icon_path = icon_url
        sound_path = sound_url
        if icon_url is not None and icon_url.startswith("http"):
            try:
                img_data = requests.get(icon_url, timeout=3).content
                icon_path = f"/tmp/lnxlink_icon.{int(time.time())}"
                with open(icon_path, "wb") as handler:
                    handler.write(img_data)
            except Exception as err:
                logger.error("Error downloading notification image: %s", err)
        if sound_url is not None and sound_url.startswith("http"):
            try:
                sound_data = requests.get(sound_url, timeout=3).content
                sound_path = f"/tmp/lnxlink_sound.{int(time.time())}"
                with open(sound_path, "wb") as handler:
                    handler.write(sound_data)
            except Exception as err:
                logger.error("Error downloading notification sound: %s", err)

        # notify2
        self.lib["notify2"].init("LNXlink")
        notify = self.lib["notify2"].Notification(
            summary=data["title"],
            message=data["message"],
            icon=f"{self.lnxlink.path}/logo.png",
        )
        if icon_path is not None:
            notify.set_hint("image-path", icon_path)
            logger.info("Setting notification icon to %s", sound_path)
        if sound_path is not None:
            if "/" in sound_path:
                notify.set_hint("sound-file", sound_path)
            else:
                notify.set_hint("sound-name", sound_path)
            logger.info("Setting notification sound to %s", sound_path)
        if isinstance(timeout, int):
            notify.set_timeout(timeout)
            logger.info("Setting notification timeout to %s", timeout)
        if urgency in self.urgencies:
            notify.set_urgency(self.urgencies[urgency])
            logger.info("Setting notification urgency to %s", urgency)
        notify.show()
