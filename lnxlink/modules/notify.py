"""Shows notifications"""
import notify2
import requests
from dbus.mainloop.glib import DBusGMainLoop


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
        if "http" in icon_url:
            icon_ext = icon_url.split(".")[-1]
            icon = f"/tmp/lnxlink_notification.{icon_ext}"
            img_data = requests.get(icon_url, timeout=3).content
            with open(icon, "wb") as handler:
                handler.write(img_data)
        elif icon_url != "":
            icon = icon_url

        # notify2
        notify2.init("Test")
        notify2.Notification(data["title"], data["message"], icon).show()
