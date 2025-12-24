"""Send rich desktop notifications via notify.send_message"""
import os
import logging
import tempfile
import requests
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Notify"
        self.lnxlink = lnxlink
        self._requirements()
        self.notify = None

    def _requirements(self):
        self.lib = {
            "notify": import_install_package(
                "dbus-notification", ">=2025.10.1", "dbus_notification"
            ),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        image_url = (
            "https://raw.githubusercontent.com/bkbilly/lnxlink/6d844af/images/logo.png"
        )
        return {
            "notify": {
                "type": "notify",
                "entity_picture": image_url,
                "icon": "mdi:desktop-classic",
            },
        }

    # pylint: disable=too-many-locals, too-many-branches
    def start_control(self, topic, data):
        """Control system"""
        if isinstance(data, str):
            data = {
                "title": "LNXlink Notification",
                "message": data,
            }
        icon_url = data.get("iconUrl")
        sound_url = data.get("sound")
        icon_path = icon_url
        sound_path = sound_url
        if not os.path.exists("/tmp/lnxlink"):
            os.makedirs("/tmp/lnxlink")
        if icon_url is not None and icon_url.startswith("http"):
            try:
                with tempfile.NamedTemporaryFile(
                    prefix="lnxlink_icon_", delete=False, dir="/tmp/lnxlink"
                ) as icon_file:
                    img_data = requests.get(icon_url, timeout=3).content
                    icon_file.write(img_data)
                    icon_path = icon_file.name
            except Exception as err:
                logger.error("Error downloading notification image: %s", err)
        if sound_url is not None and sound_url.startswith("http"):
            try:
                with tempfile.NamedTemporaryFile(
                    prefix="lnxlink_sound_", delete=False, dir="/tmp/lnxlink"
                ) as sound_file:
                    sound_data = requests.get(sound_url, timeout=3).content
                    sound_file.write(sound_data)
                    sound_path = sound_file.name
            except Exception as err:
                logger.error("Error downloading notification sound: %s", err)

        urgencies = {
            "low": 0,
            "normal": 1,
            "critical": 2,
        }

        # Send notification
        if self.notify is None:
            self.notify = self.lib["notify"].DBusNotification(
                appname="LNXlink", callback=self.callback_action
            )
        if data.get("action") == "close":
            if data.get("id") is not None:
                self.notify.close(data.get("id"))
            else:
                self.notify.close_all()
        else:
            notification_id = self.notify.send(
                title=data["title"],
                message=data["message"],
                logo=f"{self.lnxlink.path}/logo.png",
                image=icon_path,
                sound=sound_path,
                actions=data.get("buttons", []),
                urgency=urgencies.get(data.get("urgency")),
                timeout=data.get("timeout", -1),
            )
            logger.debug("The notification %s was sent.", notification_id)
            self.lnxlink.run_module(self.name, {"id": notification_id})

    def callback_action(self, notification_type, notification):
        """Gather notification options and send to the MQTT broker"""
        if notification_type == "button":
            logger.info("Pressed notification button: %s", notification)
            self.lnxlink.run_module(f"{self.name}/button_press", notification, False)
