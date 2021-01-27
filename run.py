#!/usr/bin/env python3

import yaml
import paho.mqtt.client as mqtt
import time
import signal
import notify2


import psutil
class AddonCPU():
    service = 'CPU Usage'
    icon = 'mdi:cpu'

    def getInfo(self):
        return psutil.cpu_percent()

import psutil
class AddonMemory():
    service = 'Memory Usage'
    icon = 'mdi:memory'

    def getInfo(self):
        return psutil.virtual_memory().percent


import psutil
from datetime import datetime
class AddonNetwork():
    service = 'Network Info'
    icon = 'mdi:network'

    def __init__(self):
        self.timeOld = datetime.now()
        self.sentOld = psutil.net_io_counters().bytes_sent
        self.recvOld = psutil.net_io_counters().bytes_recv

    def getInfo(self):
        timeNew = datetime.now()
        sentNew = psutil.net_io_counters().bytes_sent
        recvNew = psutil.net_io_counters().bytes_recv


        timeDiff = (timeNew - self.timeOld).total_seconds()
        sentDiff = sentNew - self.sentOld
        recvDiff = recvNew - self.recvOld
        
        self.timeOld = timeNew
        self.sentOld = sentNew
        self.recvOld = recvNew

        sentBPS = round(sentDiff / timeDiff, 2)
        recvBPS = round(recvDiff / timeDiff, 2)

        return sentBPS, recvBPS

import mpris2
from dbus.mainloop.glib import DBusGMainLoop
from mpris2 import get_players_uri
from mpris2 import Player
class AddonMedia():
    service = 'Media Info'
    icon = 'mdi:media'


    def getInfo(self):
        DBusGMainLoop(set_as_default=True)
        players = []
        for uri in get_players_uri():
            player = Player(dbus_interface_info={'dbus_uri': uri})
            p_status = player.PlaybackStatus
            title = player.Metadata.get('xesam:title')
            artist = player.Metadata.get('xesam:artist')
            album = player.Metadata.get('xesam:album')
            if title is not None:
                artist_str = ''
                if artist is not None:
                    artist_str = ','.join(artist)
                players.append({
                    'status': p_status,
                    'title': str(title),
                    'artist': artist_str,
                    'album': '' if album is None else str(album)
                })
        return players



class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True


class LNXlink():
    client = mqtt.Client()
    pref_topic = 'lnxlink'

    def __init__(self, config_path):
        self.config = self.read_config(config_path)
        self.setup_mqtt()

    def setup_mqtt(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.username_pw_set(self.config['mqtt']['auth']['user'], self.config['mqtt']['auth']['pass'])
        self.client.connect(self.config['mqtt']['server'], self.config['mqtt']['port'], 60)
        self.client.loop_start()

    def read_config(self, config_path):
        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        if 'prefix' in config['mqtt'] and 'clientId' in config['mqtt']:
            self.pref_topic = f"{config['mqtt']['prefix']}/{config['mqtt']['clientId']}"
        self.pref_topic = self.pref_topic.lower()
        return config

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe(f"{self.pref_topic}/commands/#")
        client.publish(f"{self.pref_topic}/lwt", "ON")

    def disconnect(self):
        print("Disconnected.")
        self.client.publish(f"{self.pref_topic}/lwt", "OFF")
        self.client.disconnect()

    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))


# if __name__ == '__main__':
#     lnxlink = LNXlink('config.yaml')
#     killer = GracefulKiller()
#     while not killer.kill_now:
#         time.sleep(1)
#     lnxlink.disconnect()

a = AddonMedia().getInfo()
print(a)
# AddonCPU
# AddonMemory
# AddonNetwork
# AddonMedia
