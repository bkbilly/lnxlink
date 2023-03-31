import notify2
import requests
from dbus.mainloop.glib import DBusGMainLoop


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Notify OSD'
        DBusGMainLoop(set_as_default=True)

    def startControl(self, topic, data):
        iconUrl = data.get('iconUrl', '')
        icon = 'notification-message-im'
        if 'http' in iconUrl:
            iconExt = iconUrl.split('.')[-1]
            icon = f"/tmp/lnxlink_notification.{iconExt}"
            img_data = requests.get(iconUrl).content
            with open(icon, 'wb') as handler:
                handler.write(img_data)
        elif iconUrl != '':
            icon = iconUrl

        # notify2
        notify2.init("Test")
        notify2.Notification(
            data['title'],
            data['message'],
            icon
        ).show()
