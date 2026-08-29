"""Setup the configuration file"""

import copy
import errno
import logging
import os
import shutil
import subprocess
import time
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

import beaupy
import yaml

from lnxlink.consts import CONFIGTEMP, SERVICEHEADLESS, SERVICEUSER
from lnxlink.modules import get_modules_info

logger = logging.getLogger("lnxlink")


def setup_logger(config_path, log_level):
    """Configure file logging."""
    logging.basicConfig(level=log_level)
    try:
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        log_path = Path(config_path).expanduser()
        file_handler = RotatingFileHandler(
            log_path / "lnxlink.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=1,
        )
        start_sec = str(int(time.time()))[-4:]
        log_formatter = logging.Formatter(
            "%(asctime)s ["
            + start_sec
            + ":%(threadName)s.%(module)s.%(funcName)s.%(lineno)d] [%(levelname)s]  %(message)s"
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    except Exception as err:
        logger.error("Can't log to file: %s", err)


def setup_config(config_path):
    """Setup and create config file"""
    try:
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "wb") as config:
            config.write(CONFIGTEMP.encode())
        logger.info("Created new template: %s", config_path)
    except OSError as err:
        if err.errno in {errno.EACCES, errno.EPERM, errno.EROFS}:
            logger.error(
                "Could not create configuration file %s because of permission "
                "issues.",
                config_path,
            )
        else:
            logger.error("Could not create configuration file %s: %s", config_path, err)
        return False
    return True


def setup_mqtt(config_path):
    """Interactive MQTT configuration wizard"""
    with open(config_path, encoding="UTF-8") as file:
        config = yaml.safe_load(file)

    transport_options = ["mqtt", "homeassistant_api", "auto"]
    transport_descriptions = {
        "mqtt": "Direct MQTT broker connection",
        "homeassistant_api": "Home Assistant HTTP/WebSocket API",
        "auto": "Try MQTT first, fall back to Home Assistant API",
    }
    current = config["mqtt"].get("transport", "mqtt")
    print("\n=== MQTT Configuration ===")
    print("Select transport method:")
    for num, opt in enumerate(transport_options, 1):
        marker = " *" if opt == current else ""
        print(f"  {num}) {opt} - {transport_descriptions[opt]}{marker}")

    choice = input(f" Transport [{current}]: ").strip()
    if choice in ("1", "2", "3"):
        config["mqtt"]["transport"] = transport_options[int(choice) - 1]
    elif choice in transport_options:
        config["mqtt"]["transport"] = choice
    elif choice == "":
        config["mqtt"]["transport"] = current
    else:
        print(f"Invalid choice, keeping current: {current}")
        config["mqtt"]["transport"] = current

    transport = config["mqtt"]["transport"]

    _prompt_general_mqtt_settings(config)

    if transport in ("mqtt", "auto"):
        _prompt_mqtt_broker(config)

    if transport in ("homeassistant_api", "auto"):
        _prompt_homeassistant_api(config)

    if _write_config(config_path, config):
        print("\nMQTT configuration saved successfully.")
    print(f" Transport: {config['mqtt']['transport']}")
    print(
        f" MQTT Topic prefix for monitoring: {config['mqtt']['prefix']}"
        f"/{config['mqtt']['clientId']}/..."
    )
    if transport in ("homeassistant_api", "auto"):
        print(f" Home Assistant URL: {config['mqtt']['homeassistant']['url']}")


def setup_systemd(config_path):
    """Install as a system service"""
    # Check how systemd is installed
    installed_as = _get_service_user()

    if installed_as == 0:
        # Service not found or not running
        logger.info("SystemD service not found or it's not running...")
        user_service = _query_true_false("Install as a user service?", True)
        sudo, cmd_user, systemd_service, service_location = _get_service_vars(
            user_service
        )

        # Install on SystemD
        Path(service_location).mkdir(parents=True, exist_ok=True)
        exec_cmd = f"{shutil.which('lnxlink')} -c {config_path}"
        service_text = systemd_service.format(exec_cmd=exec_cmd)
        service_path = f"{service_location}/lnxlink.service"
        command_prefix = [sudo] if sudo else []
        try:
            with open(service_path, "w", encoding="UTF-8") as config:
                config.write(service_text)
        except PermissionError:
            subprocess.run(
                [*command_prefix, "tee", service_path],
                input=service_text,
                text=True,
                stdout=subprocess.DEVNULL,
                check=True,
            )

        systemctl_scope = [cmd_user] if cmd_user else []
        subprocess.run(
            [*command_prefix, "chmod", "+x", service_path],
            check=True,
        )
        subprocess.run(
            [*command_prefix, "systemctl", *systemctl_scope, "daemon-reload"],
            check=True,
        )
        subprocess.run(
            [
                *command_prefix,
                "systemctl",
                *systemctl_scope,
                "enable",
                "lnxlink.service",
            ],
            check=True,
        )


def setup_modules(config_path):
    """Asks user which modules to include in the configuration"""
    with open(config_path, encoding="UTF-8") as file:
        config = yaml.safe_load(file)

    modules = get_modules_info(config["modules"], config["exclude"])
    options = [
        f"[bold]{module['name']}[/bold] - [dim]{module['description']}[/dim]"
        for module in modules
    ]
    initial_ticked = [num for num, module in enumerate(modules) if module["is_enabled"]]
    selected_formatted = beaupy.select_multiple(
        options, ticked_indices=initial_ticked, pagination=True, page_size=18
    )
    selected_names = [
        opt.split(" - ")[0].replace("[bold]", "").replace("[/bold]", "")
        for opt in selected_formatted
    ]
    all_module_names = [module["name"] for module in modules]
    unselected_names = [name for name in all_module_names if name not in selected_names]

    if len(selected_names) == 0:
        return
    print("You selected:", selected_names)
    if len(selected_names) < len(unselected_names):
        config["exclude"] = None
        config["modules"] = selected_names
    else:
        config["exclude"] = unselected_names
        config["modules"] = None

    _write_config(config_path, config)


def read_config(config_path):
    """Reads the config file and prepares module names for import"""
    with open(config_path, encoding="utf8") as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)

    conf["config_path"] = config_path

    if conf.get("modules") is not None:
        conf["modules"] = [x.lower().replace("-", "_") for x in conf["modules"]]

    if os.environ.get("LNXLINK_MQTT_PREFIX") not in [None, ""]:
        conf["mqtt"]["prefix"] = os.environ.get("LNXLINK_MQTT_PREFIX")
    if os.environ.get("LNXLINK_MQTT_CLIENTID") not in [None, ""]:
        conf["mqtt"]["clientId"] = os.environ.get("LNXLINK_MQTT_CLIENTID")
    if os.environ.get("LNXLINK_MQTT_SERVER") not in [None, ""]:
        conf["mqtt"]["server"] = os.environ.get("LNXLINK_MQTT_SERVER")
    if os.environ.get("LNXLINK_MQTT_PORT") not in [None, ""]:
        conf["mqtt"]["port"] = int(os.environ.get("LNXLINK_MQTT_PORT"))

    pref_topic = f"{conf['mqtt']['prefix']}/{conf['mqtt']['clientId']}"
    conf["pref_topic"] = pref_topic.lower()
    if os.environ.get("LNXLINK_MQTT_USER") not in [None, ""]:
        conf["mqtt"]["auth"]["user"] = os.environ.get("LNXLINK_MQTT_USER")
    if os.environ.get("LNXLINK_MQTT_PASS") not in [None, ""]:
        conf["mqtt"]["auth"]["pass"] = os.environ.get("LNXLINK_MQTT_PASS")

    if os.environ.get("LNXLINK_HOMEASSISTANT_URL") not in [None, ""]:
        conf["mqtt"]["homeassistant"]["url"] = os.environ.get(
            "LNXLINK_HOMEASSISTANT_URL"
        )
    if os.environ.get("LNXLINK_HOMEASSISTANT_TOKEN") not in [None, ""]:
        conf["mqtt"]["homeassistant"]["token"] = os.environ.get(
            "LNXLINK_HOMEASSISTANT_TOKEN"
        )

    return conf


def add_settings(config, name, settings, replace_empty=False):
    """Add missing configuration to yaml file"""
    if not isinstance(config.get("settings"), dict):
        config["settings"] = {}
    sys_conf = copy.deepcopy(config)
    sys_conf["settings"][name] = settings
    missing_keys = _check_missing(sys_conf, config, [], [], replace_empty)

    if len(missing_keys) > 0:
        try:
            with open(config["config_path"], encoding="utf8") as file:
                new_config = yaml.load(file, Loader=yaml.FullLoader)
            for keys, value in missing_keys:
                new_config = _add_nested(new_config, keys, value, replace_empty)
                config = _add_nested(config, keys, value, replace_empty)
                key_path = ".".join(keys)
                logger.info("Adding missing configuration option: %s", key_path)
            success_write = _write_config(config["config_path"], new_config)
            if not success_write:
                manual_insert = {}
                for keys, value in missing_keys:
                    manual_insert = _add_nested(manual_insert, keys, value)
                manual_yaml = yaml.dump(
                    manual_insert,
                    default_flow_style=False,
                    sort_keys=False,
                ).rstrip()
                logger.error(
                    "Can't write to config file, manual add this: \n%s", manual_yaml
                )

        except Exception as err:
            logger.error(
                "Couldn't edit configuration (%s): %s",
                err,
                traceback.format_exc(),
            )
    return config


def validate_config(config_path):
    """Inform user of missing configuration values"""
    with open(config_path, encoding="utf8") as file:
        user_conf = yaml.load(file, Loader=yaml.FullLoader)
    sys_conf = yaml.safe_load(CONFIGTEMP)

    missing_keys = _check_missing(sys_conf, user_conf, [], [])
    for keys, value in missing_keys:
        key_path = ".".join(keys)
        user_conf = _add_nested(user_conf, keys, value)
        logger.info("Adding missing configuration option: %s", key_path)

    if len(missing_keys) > 0:
        success_write = _write_config(config_path, user_conf)
        if not success_write:
            manual_insert = {}
            for keys, value in missing_keys:
                manual_insert = _add_nested(manual_insert, keys, value)
            manual_yaml = yaml.dump(
                manual_insert,
                default_flow_style=False,
                sort_keys=False,
            ).rstrip()
            logger.error(
                "Can't write to config file, manual add this: \n%s", manual_yaml
            )


def _write_config(config_path, config):
    """Write config changes to disk and report permission issues clearly."""
    try:
        with open(config_path, "w", encoding="UTF-8") as file:
            file.write(yaml.dump(config, default_flow_style=False, sort_keys=False))
        return True
    except OSError as err:
        if err.errno in {errno.EACCES, errno.EPERM, errno.EROFS}:
            logger.error(
                "Could not update configuration file %s because of permission issues.",
                config_path,
            )
        else:
            logger.error("Could not update configuration file %s: %s", config_path, err)
    return False


def _check_missing(sys_conf, user_conf, missing, dirpath, replace_empty=False):
    """Recursive method that returns a list of missing dictionary keys"""
    if isinstance(sys_conf, dict):
        for key, value in sys_conf.items():
            check_path = dirpath + [key]
            if isinstance(user_conf, dict) and key in user_conf:
                if (
                    replace_empty
                    and not isinstance(value, dict)
                    and user_conf[key] in [None, ""]
                    and value not in [None, ""]
                ):
                    missing.append([check_path, value])
                else:
                    _check_missing(
                        value, user_conf[key], missing, check_path, replace_empty
                    )
            else:
                missing.append([check_path, value])
    return missing


def _add_nested(dct, keys, value, replace_empty=False):
    """
    Adds a nested dictionary item based on a list of keys to an existing dictionary.

    Args:
    dct (dict): The original dictionary to be modified.
    keys (list): A list of keys representing the nested structure.
    value (any): The value to be set at the innermost level.

    Returns:
    dict: The modified dictionary with the new nested item added.
    """
    current_level = dct
    for key in keys[:-1]:
        # Create a new dictionary at the current key if it does not exist
        if key not in current_level or not isinstance(current_level[key], dict):
            current_level[key] = {}
        current_level = current_level[key]

    # Set the value at the innermost level
    if keys[-1] not in current_level or (
        replace_empty
        and current_level[keys[-1]] in [None, ""]
        and value not in [None, ""]
    ):
        current_level[keys[-1]] = value
    return dct


def _query_true_false(question, default="false"):
    """Force user to answer yes or no questions"""
    valid = {
        "true": True,
        "t": True,
        "yes": True,
        True: True,
        "false": False,
        "f": False,
        "no": False,
        False: False,
    }

    if default is True:
        prompt = "(True/False) [True]"
    elif default is False or default is None:
        prompt = "(True/False) [False]"
    else:
        raise ValueError(f"invalid default answer: {default}")

    while True:
        choice = input(f" {question} {prompt}: ").lower()
        if default is not None and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        logger.info("Please respond with 'true' or 'false' (or 't' or 'f').")


def _prompt_general_mqtt_settings(config):
    """Prompt for general MQTT/LNXlink settings (prefix, clientId, discovery, LWT, clear_on_off)"""
    mqtt = config["mqtt"]
    print("\n--- General Settings ---")
    mqtt["prefix"] = input(f" Topic prefix [{mqtt['prefix']}]: ") or mqtt["prefix"]
    mqtt["clientId"] = input(f" Client ID [{mqtt['clientId']}]: ") or mqtt["clientId"]
    mqtt["discovery"]["enabled"] = _query_true_false(
        "Enable MQTT auto-discovery", mqtt["discovery"]["enabled"]
    )
    if mqtt["discovery"]["enabled"]:
        mqtt["discovery"]["prefix"] = (
            input(f" Discovery prefix [{mqtt['discovery']['prefix']}]: ")
            or mqtt["discovery"]["prefix"]
        )
    mqtt["lwt"]["enabled"] = _query_true_false(
        "Enable Last Will and Testament (LWT)", mqtt["lwt"]["enabled"]
    )
    if mqtt["lwt"]["enabled"]:
        mqtt["lwt"]["qos"] = (
            input(f" LWT QoS level [{mqtt['lwt']['qos']}]: ") or mqtt["lwt"]["qos"]
        )
        mqtt["lwt"]["qos"] = int(mqtt["lwt"]["qos"])
    mqtt["clear_on_off"] = _query_true_false(
        "Clear sensor values on power-off", mqtt["clear_on_off"]
    )


def _prompt_mqtt_broker(config):
    """Prompt for direct MQTT broker settings"""
    mqtt = config["mqtt"]
    print("\n--- MQTT Broker Settings ---")
    mqtt["server"] = input(f" MQTT server [{mqtt['server']}]: ") or mqtt["server"]
    mqtt["port"] = input(f" MQTT port [{mqtt['port']}]: ") or mqtt["port"]
    mqtt["port"] = int(mqtt["port"])
    mqtt["auth"]["user"] = (
        input(f" MQTT username [{mqtt['auth']['user']}]: ") or mqtt["auth"]["user"]
    )
    mqtt["auth"]["pass"] = (
        input(f" MQTT password [{mqtt['auth']['pass']}]: ") or mqtt["auth"]["pass"]
    )
    mqtt["auth"]["tls"] = _query_true_false("Enable TLS", mqtt["auth"]["tls"])
    if mqtt["auth"]["tls"]:
        mqtt["auth"]["ca_certs"] = (
            input(f" CA certs file [{mqtt['auth']['ca_certs']}]: ")
            or mqtt["auth"]["ca_certs"]
        )
        mqtt["auth"]["certfile"] = (
            input(f" Client cert file [{mqtt['auth']['certfile']}]: ")
            or mqtt["auth"]["certfile"]
        )
        mqtt["auth"]["keyfile"] = (
            input(f" Client key file [{mqtt['auth']['keyfile']}]: ")
            or mqtt["auth"]["keyfile"]
        )


def _prompt_homeassistant_api(config):
    """Prompt for Home Assistant API settings"""
    ha = config["mqtt"]["homeassistant"]
    print("\n--- Home Assistant API Settings ---")
    ha["url"] = (
        input(f" Home Assistant URL [{ha['url'] or 'e.g. http://192.168.1.1:8123'}]: ")
        or ha["url"]
    )
    current_token = ha.get("token", "")
    token_display = current_token[:10] + "..." if current_token else ""
    ha["token"] = (
        input(f" Token or path to token file [{token_display}]: ") or current_token
    )
    ha["timeout"] = (
        input(f" HTTP timeout in seconds [{ha['timeout']}]: ") or ha["timeout"]
    )
    ha["timeout"] = int(ha["timeout"])
    ha["verify_ssl"] = _query_true_false("Verify SSL certificates", ha["verify_ssl"])
    ha["subscribe_commands"] = _query_true_false(
        "Subscribe to commands via WebSocket", ha["subscribe_commands"]
    )


def _get_service_user():
    """Install as a user service"""
    installed_as = 0
    for num, cmd_user in enumerate(["--user", ""], start=1):
        cmd = f"systemctl {cmd_user} is-enabled lnxlink.service"
        stdout = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            check=False,
        ).stdout.decode("UTF-8")
        result = stdout.strip()
        if result in ["enabled"]:
            _, _, _, service_location = _get_service_vars(num)
            if os.path.exists(f"{service_location}/lnxlink.service"):
                installed_as = num
    return installed_as


def _get_service_vars(user_service):
    """Return service commands based on installation type"""
    if user_service is True or user_service == 1:
        sudo = ""
        cmd_user = "--user"
        systemd_service = SERVICEUSER
        service_location = f"{os.path.expanduser('~')}/.config/systemd/user"
    else:
        sudo = "sudo"
        cmd_user = ""
        systemd_service = SERVICEHEADLESS
        service_location = "/etc/systemd/system"
    return sudo, cmd_user, systemd_service, service_location
