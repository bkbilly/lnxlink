#!/usr/bin/env python3

import yaml
import sys

# config_file = 'config_temp.yaml'
config_file = sys.argv[1]
with open(config_file) as f:
    y = yaml.safe_load(f)
    print('This will update the MQTT credentials and topics, these are the default topics:')
    print(" MQTT Topic prefix for for monitoring: {}/{}/{}/...".format(
        y['mqtt']['prefix'],
        y['mqtt']['clientId'],
        y['mqtt']['statsPrefix']
    ))
    print(" MQTT Topic prefix for for commands: {}/{}/commands/...".format(
        y['mqtt']['prefix'],
        y['mqtt']['clientId']
    ))

    print("\nLeave empty for default")

    y['mqtt']['server'] = input(f" MQTT server [{y['mqtt']['server']}]: ") or y['mqtt']['server']
    y['mqtt']['port'] = input(f" MQTT port [{y['mqtt']['port']}]: ") or y['mqtt']['port']
    y['mqtt']['auth']['user'] = input(f" MQTT username [{y['mqtt']['auth']['user']}]: ") or y['mqtt']['auth']['user']
    y['mqtt']['auth']['pass'] = input(f" MQTT password [{y['mqtt']['auth']['pass']}]: ") or y['mqtt']['auth']['pass']

    y['mqtt']['prefix'] = input(f" Change prefix [{y['mqtt']['prefix']}]: ") or y['mqtt']['prefix']
    y['mqtt']['clientId'] = input(f" Change clientId [{y['mqtt']['clientId']}]: ") or y['mqtt']['clientId']
    y['mqtt']['statsPrefix'] = input(f" Change statsPrefix [{y['mqtt']['statsPrefix']}]: ") or y['mqtt']['statsPrefix']

with open(config_file, 'w') as fw:
    fw.write(yaml.dump(y, default_flow_style=False, sort_keys=False))

print('\nAll changes have been saved.')
print(" MQTT Topic prefix for for monitoring: {}/{}/{}/...".format(
    y['mqtt']['prefix'],
    y['mqtt']['clientId'],
    y['mqtt']['statsPrefix']
))
print(" MQTT Topic prefix for for commands: {}/{}/commands/...".format(
    y['mqtt']['prefix'],
    y['mqtt']['clientId']
))
