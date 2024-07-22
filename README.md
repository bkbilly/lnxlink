[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE.md)
[![OS - Linux](https://img.shields.io/badge/OS-Linux-blue?logo=linux&logoColor=white)]()
[![Python 3.7](https://img.shields.io/badge/Python-3.7-blue?logo=python&logoColor=white)]()
[![PyPI](https://img.shields.io/pypi/v/lnxlink?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/lnxlink/)
[![Last commit](https://img.shields.io/github/last-commit/bkbilly/lnxlink?color=blue&logo=github&logoColor=white)]()


# LNXlink
LNXlink is a Linux companion app that seamlessly integrates your system with external applications like Home Assistant.
It uses MQTT, a lightweight messaging protocol, to enable real-time data exchange and remote control capabilities.

With LNXlink, you can monitor your Linux machine's performance, execute commands remotely, and integrate it into your smart home ecosystem for centralized management.

# Key Features
 - **Sensor Monitoring:** Automatically or manually expose sensors that monitor and control the system remotely.
 - **Home Assistant:** Utilizes MQTT Autodiscovery to create entities in Home Assistant dashboard.
 - **Easy Installation:** No sudo privileges required for installation and operation, except for server environments.
 - **Expandable Architecture:** Automatically imports new modules and allows for the addition of custom modules.

![lnxlink_sensors2](https://github.com/user-attachments/assets/1b7f3fc2-4387-4cd1-8fcf-25d77137c3fe)

# Get started
To get started with LNXlink, follow these simple steps:
 - Download the LNXlink application and install it on your Linux machine: `pipx install lnxlink`
 - Follow the configuration instructions to setup LNXlink: `lnxlink -c lnxlink.yaml`
 - Install and configure on Home Assistant the [hass-mqtt-mediaplayer](https://github.com/bkbilly/hass-mqtt-mediaplayer) integration.
 - Enjoy real-time monitoring and control of your Linux machine from your Home Assistant dashboard.

For detailed installation instructions, please refer to the documentation page: [bkbilly.gitbook.io/lnxlink](https://bkbilly.gitbook.io/lnxlink).

# Benefits
 - **Cross-Platform Compatibility:** Runs on any Linux distribution, providing flexibility and wide-ranging compatibility.
 - **Enhanced System Insights:** Gain real-time insights into your Linux machine's performance by monitoring essential system metrics.
 - **Remote Command Execution:** Execute arbitrary commands directly from your Home Assistant dashboard, granting remote control over your Linux machine.
 - **Seamless Integration with Home Assistant:** Integrate your Linux machine into your smart home ecosystem for unified control and monitoring.
 - **Automate tasks:** Set up automated tasks to perform repetitive actions and save yourself time and effort.


# Support LNXlink's Development
To contribute to the development of LNXlink, you can sponsor the project through [GitHub Sponsors](https://github.com/sponsors/bkbilly) or [PayPal](https://www.paypal.com/paypalme/bkbillybk). Your support will help maintain the project, add new features, and fix bugs.
