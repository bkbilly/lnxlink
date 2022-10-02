#!/usr/bin/env python3

import yaml
import sys

def query_true_false(question, default="false"):
    valid = {"true": True, "t": True, "yes": True, True: True, "false": False, "f": False, "no": False, False:False}

    if default == True:
        prompt = "(True/False) [True]"
    elif default == False or default is None:
        prompt = "(True/False) [False]"
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = input(f" {question} {prompt}: ").lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'true' or 'false' (or 't' or 'f').")


# config_file = 'config_temp.yaml'
config_file = sys.argv[1]
with open(config_file) as f:
    y = yaml.safe_load(f)

    # Print config
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

    # Change default values
    y['mqtt']['discovery']['enabled'] = query_true_false("Enable MQTT automatic discovery", y['mqtt']['discovery']['enabled'])
    y['mqtt']['server'] = input(f" MQTT server [{y['mqtt']['server']}]: ") or y['mqtt']['server']
    y['mqtt']['port'] = input(f" MQTT port [{y['mqtt']['port']}]: ") or y['mqtt']['port']
    y['mqtt']['port'] = int(y['mqtt']['port'])
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
