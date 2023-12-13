---
description: Get started with LNXlink
---

# 🖥 Setup

## Installation

Install system packages:

{% tabs %}
{% tab title="Debian Based" %}
{% code overflow="wrap" lineNumbers="true" %}
```bash
sudo apt install patchelf meson python3-pip libcairo2-dev libgirepository1.0-dev libdbus-glib-1-dev libglib2.0-dev
# Install modules dependencies
sudo apt install libasound2-dev upower xdotool xdg-utils python3-pyaudio
```
{% endcode %}
{% endtab %}

{% tab title="Red Hat Based" %}
{% code overflow="wrap" lineNumbers="true" %}
```bash
sudo dnf install python39-pip.noarch gcc cmake dbus-devel glib2-devel python39-devel alsa-lib-devel
```
{% endcode %}
{% endtab %}
{% endtabs %}

Prepare your system:

{% code overflow="wrap" lineNumbers="true" %}
```bash
sudo pip3 install -U pip
pip install pycairo PyGObject
```
{% endcode %}

Select the installation type you want:

{% tabs %}
{% tab title="Desktop" %}
Recommended installation if you have a graphical interface.

Install or Update LNXlink:

{% code overflow="wrap" lineNumbers="true" %}
```bash
# Install lnxlink package on the system
pip3 install -U lnxlink
# When asked, it's recommended to install as a user service.
lnxlink -c config.yaml
```
{% endcode %}

You can manually update the configuration file `config.yaml` and restart the service with the use of systemctl:

{% code overflow="wrap" lineNumbers="true" %}
```bash
systemctl --user restart lnxlink.service
```
{% endcode %}
{% endtab %}

{% tab title="Server" %}
The headless installation is used for linux environments that don't use a Graphical Interface like servers.

Install or Update LNXlink:

{% code overflow="wrap" lineNumbers="true" %}
```bash
# Install lnxlink package on the system
sudo pip3 install -U lnxlink
# When asked, it's recommended to answer false on install as a user service.
sudo lnxlink -c config.yaml
```
{% endcode %}

You can manually update the configuration file `config.yaml` and restart the service with the use of systemctl:

{% code overflow="wrap" lineNumbers="true" %}
```bash
sudo systemctl restart lnxlink.service
```
{% endcode %}
{% endtab %}

{% tab title="Development" %}
This installs LNXlink as a development platform which is helpful if you want to create your own changes or create a new module. Read on the Development section for more information.

{% code overflow="wrap" lineNumbers="true" %}
```bash
# Fork my repository and then download it
git clone https://github.com/bkbilly/lnxlink.git
# Install lnxlink as editable package
cd lnxlink
pip3 install -e .
# Run it manually
lnxlink -c config.yaml
```
{% endcode %}
{% endtab %}

{% tab title="VENV" %}
Newer versions of LNXlink don't allow installation of packages on the system, so a virtual environment can be used.

Install or Update LNXlink:

{% code overflow="wrap" lineNumbers="true" %}
```bash
# Install VirtualEnv package on the system
sudo pip3 install virtualenv --break-system-packages
# Install LNXlink on a virtual environment folder.
python3 -m venv lnxlink_venv
source lnxlink_venv/bin/activate
pip install lnxlink
lnxlink -c config.yaml
```
{% endcode %}

You can manually update the configuration file `config.yaml` and restart the service with the use of systemctl:

{% code overflow="wrap" lineNumbers="true" %}
```bash
systemctl --user restart lnxlink.service
```
{% endcode %}
{% endtab %}
{% endtabs %}

### Run sudo commands

Some commands needs to run as a root user, but it's not recommended to run LNXlink as a superuser. To fix this, you need to allow the command grub-reboot to run without asking for password:

```bash
# Edit the sudoers file:
sudo visudo
# Add this line at the end (replace USER with your username):
USER ALL=(ALL) NOPASSWD: /usr/sbin/grub-reboot
USER ALL=(ALL) NOPASSWD: /bin/systemctl
```

## Config

### Config file location

Your config file is located at the directory you were when you first run LNXlink. This can be anything you write like of the `config.yaml` that I suggested. You can find where it is from the systemd service:

{% tabs %}
{% tab title="Desktop" %}
```
cat ~/.config/systemd/user/lnxlink.service | grep -i ExecStart
```
{% endtab %}

{% tab title="Server" %}
```
cat /etc/systemd/lnxlink.service | grep -i ExecStart
```
{% endtab %}
{% endtabs %}

### Modules

By default all modules are automatically loaded. This happens when the modules section is empty like this:

```yaml
modules:
```

You should select the ones you want to load. All supported modules can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and the configuration should look like this:

```yaml
modules:
- notify
- camera_used
- idle
- keep_alive
- shutdown
- brightness
```

### Custom module

You can create custom modules and import them to your configuration with their full path. The name has to be unique so that it won't conflict with another python library.

Code examples can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and this is how to add the `mytest` module to your configuration.

```yaml
custom_modules:
- /home/user/mytest.py
```

3rd party custom modules:

* [https://github.com/PW999/lnxlink\_gpu\_nvidia\_settings](https://github.com/PW999/lnxlink\_gpu\_nvidia\_settings)
* [https://github.com/bkbilly/lnxlink/discussions/81](https://github.com/bkbilly/lnxlink/discussions/81)

### Exclude Modules

In case you have empty modules config which auto loads all the available modules, you can have this option that excludes modules from auto loading:

```yaml
exclude:
- screenshot
- webcam
```

## Uninstall

Remove LNXlink from your system.

{% tabs %}
{% tab title="Desktop" %}
```bash
# Disables systemd service
systemctl --user disable lnxlink.service

# Remove systemd service
rm ~/.config/systemd/user/lnxlink.service

# Uninstall the package
pip3 uninstall -U lnxlink
```
{% endtab %}

{% tab title="Server" %}
```bash
# Disables systemd service
sudo systemctl disable lnxlink.service

# Remove systemd service
sudo rm /etc/systemd/system/lnxlink.service

# Uninstall the package
sudo pip3 uninstall -U lnxlink
sudo pip3 uninstall lnxlink
```
{% endtab %}
{% endtabs %}
