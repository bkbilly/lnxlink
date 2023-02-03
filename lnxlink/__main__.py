#!/usr/bin/env python3

import os
import yaml
import time
import threading
import json
import traceback
import importlib.metadata
import platform
import argparse
import paho.mqtt.client as mqtt
from . import modules
from . import config
from .system_monitor import MonitorSuspend, GracefulKiller

version = importlib.metadata.version(__package__ or __name__)


class LNXlink():
    client = mqtt.Client()
    pref_topic = 'lnxlink'

    def __init__(self, config_path):
        print(f"LNXLink {version} started: {platform.python_version()}")
        self.config = self.read_config(config_path)

        self.Addons = {}
        for service, addon in modules.parse_modules(self.config['modules']).items():
            self.Addons[addon.service] = addon(self)

        self.setup_mqtt()

    def monitor_run(self):
        if self.config['modules'] is not None:
            for service in self.config['modules']:
                addon = self.Addons[service]
                if hasattr(addon, 'getInfo'):
                    try:
                        subtopic = addon.name.lower().replace(' ', '/')
                        topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"
                        pub_data = addon.getInfo()
                        # print(topic, pub_data, type(pub_data))
                        if pub_data is None:
                            return
                        if type(pub_data) in [dict, list]:
                            pub_data = json.dumps(pub_data)
                        self.client.publish(
                            topic,
                            payload=pub_data,
                            retain=self.config['mqtt']['lwt']['retain']
                        )
                    except Exception as e:
                        print(f"Can't load addon: {service}")
                        traceback.print_exc()

    def monitor_run_thread(self):
        self.monitor_run()

        interval = self.config.get('update_interval', 5)
        self.monitor = threading.Timer(interval, self.monitor_run_thread)
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

        config['modules'] = [x.lower().replace('-', '_') for x in config['modules']]
        return config

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT with code {rc}")
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

    def disconnect(self, *args):
        print("Disconnected from MQTT.")
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

    def temp_connection_callback(self, status):
        if self.config['mqtt']['lwt']['enabled']:
            if status:
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config['mqtt']['lwt']['disconnectMsg'],
                    qos=self.config['mqtt']['lwt']['qos'],
                    retain=self.config['mqtt']['lwt']['retain']
                )
            else:
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config['mqtt']['lwt']['connectMsg'],
                    qos=self.config['mqtt']['lwt']['qos'],
                    retain=self.config['mqtt']['lwt']['retain']
                )

    def on_message(self, client, userdata, msg):
        topic = msg.topic.replace(f"{self.pref_topic}/commands/", "")
        message = msg.payload
        print(f"Message received: {topic}")
        try:
            message = json.loads(message)
        except Exception as e:
            message = message.decode()
            # print("String could not be converted to JSON")
            # traceback.print_exc()

        select_service = topic.split('/')
        addon = self.Addons.get(select_service[0])
        if select_service[0] in self.config['modules'] and addon is not None:
            if hasattr(addon, 'startControl'):
                try:
                    addon.startControl(select_service, message)
                    self.monitor_run()
                except Exception as e:
                    traceback.print_exc()

    def setup_discovery_monitoring(self, addon, service, discovery_template):
        subtopic = addon.name.lower().replace(' ', '/')
        state_topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"

        discovery = discovery_template.copy()
        discovery['name'] = addon.name.lower().replace(' ', '_')
        discovery['unique_id'] = f"{self.config['mqtt']['clientId']}_{service}"
        discovery['state_topic'] = state_topic
        if addon.getInfo.__annotations__.get('return') == dict:
            discovery['json_attributes_topic'] = state_topic
        if hasattr(addon, 'icon'):
            discovery['icon'] = addon.icon
        if hasattr(addon, 'unit'):
            discovery['unit_of_measurement'] = addon.unit
            if addon.unit == 'json':
                discovery['unit_of_measurement'] = ""
                discovery['value_template'] = "{{ value_json.status }}"
                discovery['json_attributes_template'] = "{{ value_json | tojson }}"
        if hasattr(addon, 'title'):
            discovery['title'] = addon.title
        if hasattr(addon, 'entity_picture'):
            discovery['entity_picture'] = addon.entity_picture
        if hasattr(addon, 'device_class'):
            discovery['device_class'] = addon.device_class
        if hasattr(addon, 'state_class'):
            discovery['state_class'] = addon.state_class

        sensor_type = getattr(addon, 'sensor_type', None)
        if sensor_type is not None:
            self.client.publish(
                f"homeassistant/{sensor_type}/lnxlink/{discovery['unique_id']}/config",
                payload=json.dumps(discovery),
                retain=self.config['mqtt']['lwt']['retain'])

    def setup_discovery_control(self, addon, service, control_name, options, discovery_template):
        subtopic = addon.name.lower().replace(' ', '/')
        state_topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"
        discovery = discovery_template.copy()
        discovery['name'] = control_name.lower().replace(' ', '_')
        discovery['unique_id'] = f"{self.config['mqtt']['clientId']}_{control_name}"
        discovery['enabled_by_default'] = options.get('enabled', True)
        discovery["command_topic"] = f"{self.pref_topic}/commands/{service}/{control_name}/"
        if 'value_template' in options:
            discovery["value_template"] = options['value_template']
        if 'icon' in options:
            discovery['icon'] = options.get('icon', '')


        if options['type'] == 'button':
            discovery['state_topic'] = f"{self.pref_topic}/lwt"
        elif options['type'] == 'switch':
            discovery["state_topic"] = state_topic
            discovery["payload_off"] = "OFF"
            discovery["payload_on"] = "ON"
        elif options['type'] == 'text':
            discovery["state_topic"] = state_topic
        elif options['type'] == 'number':
            discovery["state_topic"] = state_topic
            discovery["min"] = options.get('min', 1)
            discovery["max"] = options.get('max', 100)
        else:
            return
        self.client.publish(
            f"homeassistant/{options['type']}/lnxlink/{discovery['unique_id']}/config",
            payload=json.dumps(discovery),
            retain=self.config['mqtt']['lwt']['retain'])

    def setup_discovery(self):
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
                "manufacturer": f"LNXLink {version}"
            },
        }
        if self.config['modules'] is not None:
            for service in self.config['modules']:
                addon = self.Addons[service]
                if hasattr(addon, 'getInfo'):
                    try:
                        self.setup_discovery_monitoring(addon, service, discovery_template)
                    except Exception as e:
                        traceback.print_exc()
                if hasattr(addon, 'exposedControls'):
                    for control_name, options in addon.exposedControls().items():
                        try:
                            control_name = control_name.lower().replace(' ', '_')
                            self.setup_discovery_control(addon, service, control_name, options, discovery_template)
                        except Exception as e:
                            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        prog="LNX Link",
        description="Send system information to MQTT broker")
    parser.add_argument(
        "-c", "--config",
        help="Configuration file",
        default="/etc/config.yaml",
        required=True)
    args = parser.parse_args()

    config_file = os.path.abspath(args.config)
    config.setup_config(config_file)
    config.setup_systemd(config_file)
    lnxlink = LNXlink(config_file)
    lnxlink.monitor_run_thread()

    # Monitor for system changes (Shutdown/Suspend/Sleep)
    monitor_suspend = MonitorSuspend(lnxlink.temp_connection_callback)
    monitor_suspend.start()
    monitor_gracefulkiller = GracefulKiller(lnxlink.temp_connection_callback)
    while not monitor_gracefulkiller.kill_now:
        time.sleep(1)
    monitor_suspend.stop()
    lnxlink.disconnect()


if __name__ == '__main__':
    main()
