import importlib.metadata
import time
import requests
import traceback


class Addon():

    def __init__(self, lnxlink):
        self.name = 'LNXlink'
        self.last_time = 0
        self.update_interval = 86400  # Check for updates every 24 hours
        version = importlib.metadata.version('lnxlink')
        self.message = {
          "installed_version": version,
          "latest_version": version,
          "release_summary": "",
          "release_url": "https://github.com/bkbilly/lnxlink/releases/latest",
        }

    def exposedControls(self):
        return {
            "Update": {
                "type": "update",
                "title": "LNXlink",
                "icon": "mdi:update",
                "device_class": "firmware",
                "entity_category": "diagnostic",
                "entity_picture": "https://github.com/bkbilly/lnxlink/raw/master/logo.png?raw=true",
            },
        }

    def getControlInfo(self):
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self._latest_version()
            self.last_time = cur_time

        return self.message

    def _latest_version(self):
        url = "https://api.github.com/repos/bkbilly/lnxlink/releases/latest"
        try:
            resp = requests.get(url=url).json()
            self.message['latest_version'] = resp['tag_name']
            self.message['release_summary'] = resp['body']
            self.message['release_url'] = resp['html_url']
        except:
            traceback.print_exc()
