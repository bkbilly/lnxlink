#!/usr/bin/env python3

import yaml
import paho.mqtt.client as mqtt
import time
import signal
import notify2


class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True


class LNXlink():
    client = mqtt.Client()

    def __init__(self, config_path):
        self.pref_topic = 'lnxlink'
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


if __name__ == '__main__':
    lnxlink = LNXlink('config.yaml')
    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(1)
    lnxlink.disconnect()
