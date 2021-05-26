#!/usr/bin/env python3

import yaml
import paho.mqtt.client as mqtt
import time
import signal
import threading
import json
import modules
import traceback


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


class LNXlink():
    client = mqtt.Client()
    pref_topic = 'lnxlink'

    def __init__(self, config_path):
        self.config = self.read_config(config_path)
        self.setup_mqtt()
        self.Addons = {}
        for service, addon in modules.modules.items():
            self.Addons[addon.service] = addon()

    def monitor_run(self):
        if self.config['monitoring'] is not None:
            for service in self.config['monitoring']:
                try:
                    addon = self.Addons[service]
                    subtopic = addon.name.lower().replace(' ', '/')
                    topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"
                    pub_data = addon.getInfo()
                    # print(topic, pub_data, type(pub_data))
                    if type(pub_data) in [dict, list]:
                        pub_data = json.dumps(pub_data)
                    self.client.publish(topic, payload=pub_data)
                except Exception as e:
                    traceback.print_exc()

    def monitor_run_thread(self):
        self.monitor_run()

        self.monitor = threading.Timer(5.0, self.monitor_run_thread)
        self.monitor.start()

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
        print("Connected with result code " + str(rc))
        client.subscribe(f"{self.pref_topic}/commands/#")
        if self.config['mqtt']['lwt']['enabled']:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config['mqtt']['lwt']['connectMsg'],
                qos=self.config['mqtt']['lwt']['qos'],
                retain=self.config['mqtt']['lwt']['retain']
            )
        if self.config['mqtt']['discovery']['enabled']:
            self.setup_discovery()

    def disconnect(self):
        print("Disconnected.")
        if self.config['mqtt']['lwt']['enabled']:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config['mqtt']['lwt']['disconnectMsg'],
                qos=self.config['mqtt']['lwt']['qos'],
                retain=self.config['mqtt']['lwt']['retain']
            )
        try:
            self.monitor.cancel()
        except Exception as e:
            pass
        self.client.disconnect()

    def on_message(self, client, userdata, msg):
        topic = msg.topic.replace(f"{self.pref_topic}/commands/", "")
        message = msg.payload
        try:
            message = json.loads(message)
        except Exception as e:
            traceback.print_exc()

        select_service = topic.split('/')
        control = self.Addons.get(select_service[0])
        if select_service[0] in self.config['control'] and control is not None:
            try:
                control.startControl(select_service, message)
                self.monitor_run()
            except Exception as e:
                traceback.print_exc()

    def setup_discovery(self):
        if self.config['monitoring'] is not None:
            for service in self.config['monitoring']:
                discovery_template = {
                    "availability": {
                        "topic": f"{self.pref_topic}/lwt",
                        "payload_available": "ON",
                        "payload_not_available": "OFF",
                    },
                    "device": {
                        "identifiers": [self.config['mqtt']['clientId']],
                        "name": self.config['mqtt']['clientId'],
                        "model": self.config['mqtt']['prefix'],
                        "manufacturer": "LNXLink 0.3"
                    },
                    "name": "DESKTOP-1N85K9V CPU Usage",
                    "unique_id": "desktop-1n85k9v_cpu_usage",
                    "icon": "mdi:speedometer",
                }
                addon = self.Addons[service]
                subtopic = addon.name.lower().replace(' ', '/')
                topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"

                discovery_template['name'] = addon.name.lower().replace(' ', '_')
                discovery_template['unique_id'] = f"{self.config['mqtt']['clientId']}_{service}"
                discovery_template['state_topic'] = topic
                if service == 'cpu':
                    discovery_template['icon'] = "mdi:speedometer"
                    discovery_template['unit_of_measurement'] = "%"
                    self.client.publish(
                        f"homeassistant/sensor/lnxlink/{discovery_template['unique_id']}/config",
                        payload=json.dumps(discovery_template),
                        retain=False
                    )
                elif service == 'memory':
                    discovery_template['icon'] = "mdi:memory"
                    discovery_template['unit_of_measurement'] = "%"
                    self.client.publish(
                        f"homeassistant/sensor/lnxlink/{discovery_template['unique_id']}/config",
                        payload=json.dumps(discovery_template),
                        retain=False
                    )
                elif service == 'network':
                    discovery_template['icon'] = "mdi:access-point-network"
                    discovery_template['unit_of_measurement'] = "Mbit/s"
                    discovery_template['json_attributes_topic'] = topic
                    discovery_template['name'] = f"{addon.name.lower().replace(' ', '_')}_download"
                    discovery_template['unique_id'] = f"{self.config['mqtt']['clientId']}_{service}_download"
                    discovery_template['value_template'] = "{{ value_json.download }}"
                    self.client.publish(
                        f"homeassistant/sensor/lnxlink/{discovery_template['unique_id']}/config",
                        payload=json.dumps(discovery_template),
                        retain=False
                    )
                    discovery_template['name'] = f"{addon.name.lower().replace(' ', '_')}_upload"
                    discovery_template['unique_id'] = f"{self.config['mqtt']['clientId']}_{service}_upload"
                    discovery_template['value_template'] = "{{ value_json.upload }}"
                    self.client.publish(
                        f"homeassistant/sensor/lnxlink/{discovery_template['unique_id']}/config",
                        payload=json.dumps(discovery_template),
                        retain=False
                    )
            if 'shutdown' in self.config['control']:
                discovery_template = {
                    "availability": {
                        "topic": f"{self.pref_topic}/lwt",
                        "payload_available": "ON",
                        "payload_not_available": "OFF",
                    },
                    "device": {
                        "identifiers": [self.config['mqtt']['clientId']],
                        "name": self.config['mqtt']['clientId'],
                        "model": self.config['mqtt']['prefix'],
                        "manufacturer": "LNXLink 0.3"
                    },
                    "name": "Shutdown",
                    "unique_id": f"{self.config['mqtt']['clientId']}_shutdown",
                    "icon": "mdi:power",
                    "command_topic": f"{self.pref_topic}/commands/shutdown",
                    "state_topic": f"{self.pref_topic}/lwt",
                    "payload_off": "OFF",
                    "payload_on": "ON",
                }
                self.client.publish(
                    f"homeassistant/switch/lnxlink/{discovery_template['unique_id']}/config",
                    payload=json.dumps(discovery_template),
                    retain=False
                )



if __name__ == '__main__':
    lnxlink = LNXlink('config.yaml')
    lnxlink.monitor_run_thread()

    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(1)
    lnxlink.disconnect()
