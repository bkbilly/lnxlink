import notify2

class Addon():
    service = 'notify'
    name = 'Notify OSD'
    icon = None
    unit = None

    def startControl(self, topic, data):
        # notify2
        notify2.init("Test")
        notify2.Notification(
            data['title'],
            data['message'],
            "notification-message-im"
        ).show()

        print(topic, data)

