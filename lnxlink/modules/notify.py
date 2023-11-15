"""Shows notifications"""
import logging
import notify2
import requests
from dbus.mainloop.glib import DBusGMainLoop

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Notify OSD"
        DBusGMainLoop(set_as_default=True)

    def start_control(self, topic, data):
        """Control system"""
        icon_url = data.get("iconUrl", "")
        icon = "notification-message-im"
        try:
            if "http" in icon_url:
                icon_ext = icon_url.split(".")[-1]
                img_data = requests.get(icon_url, timeout=3).content
                icon = f"/tmp/lnxlink_notification.{icon_ext}"
                with open(icon, "wb") as handler:
                    handler.write(img_data)
            elif icon_url != "":
                icon = icon_url
        except Exception as err:
            logger.error("Error downloading notification image: %s", err)

        # notify2
        notify2.init("Test")
        notify2.Notification(data["title"], data["message"], icon).show()
