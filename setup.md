---
description: Get started with LNXlink
---

# 🖥️ Setup

## Installation

Select the installation type you want:

{% tabs %}
{% tab title="System" %}
Install LNXlink with `pipx` and the required system dependencies. It will create an `lnxlink.yaml` file in the directory where you run the installer and guide you through the basic configuration setup:

{% code overflow="wrap" lineNumbers="true" %}
```bash
curl -L https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh | bash
```
{% endcode %}

You can manually update the configuration file `lnxlink.yaml` and restart the service with the use of systemctl:

{% code overflow="wrap" lineNumbers="true" %}
```bash
systemctl --user restart lnxlink.service  # For user installations
sudo systemctl restart lnxlink.service  # For root installations
```
{% endcode %}

Use the module selector whenever you want to enable or disable modules without editing YAML by hand:

```bash
lnxlink -m -c lnxlink.yaml
```

The selector updates the `modules` or `exclude` section in your config file, depending on which option creates the shorter list.
{% endtab %}

{% tab title="PyPI / pipx" %}
If your system dependencies are already installed, you can install LNXlink directly from PyPI:

```bash
pipx install lnxlink
lnxlink -sc lnxlink.yaml
```

Use `-s` to run only the setup workflow. After editing the generated configuration, start LNXlink with:

```bash
lnxlink -c lnxlink.yaml
```
{% endtab %}

{% tab title="AUR" %}
On Arch Linux and derivatives, install the AUR package:

```bash
yay -S python-lnxlink
# or
paru -S python-lnxlink
```

Create and edit the configuration file:

```bash
mkdir -p ~/.config/lnxlink
cp /usr/share/doc/python-lnxlink/config.yaml.example ~/.config/lnxlink/config.yaml
$EDITOR ~/.config/lnxlink/config.yaml
```

Enable and start the user service:

```bash
systemctl --user enable --now lnxlink
```
{% endtab %}

{% tab title="Docker" %}
{% hint style="info" %}
Some modules may not work yet.&#x20;
{% endhint %}

This command will download the LNXlink image and set up the configuration file:

{% code overflow="wrap" %}
```bash
docker run --network host -v ~/Documents/LNXlink/:/opt/lnxlink/config/ -it bkbillybk/lnxlink:latest
```
{% endcode %}

Create a docker compose file:

{% code title="docker-compose.yaml" %}
```yaml
services:
  lnxlink:
    image: bkbillybk/lnxlink:latest
    container_name: lnxlink
    restart: unless-stopped
    network_mode: host
    privileged: true
    stdin_open: true
    tty: true
    user: "1000:1000"  # UID:GID
    ports:
      - 8112:8112
    volumes:
      - ~/Documents/LNXlink/:/opt/lnxlink/config/
      - ~/.local/share/Steam/:/.local/share/Steam/
      - /var/run/reboot-required:/var/run/reboot-required:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/run/user/1000/bus:/var/run/user/1000/bus
      - /var/run/dbus/:/var/run/dbus/
      - /tmp/.X11-unix:/tmp/.X11-unix
      - /proc/:/proc/
      - /dev/:/dev/
    environment:
      - DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
      - DISPLAY=$DISPLAY
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```
{% endcode %}

Run docker compose image:

```bash
docker compose -f docker-compose.yaml up
```
{% endtab %}

{% tab title="Flatpak" %}
{% hint style="warning" %}
This is not easily maintained, so it might not be updated to the latest version. Also some modules are not fully supported.
{% endhint %}

Install and follow the setup instructions by running it. A new configuration file will be created at `~/Documents/LNXlink/config.yaml`.&#x20;

{% code lineNumbers="true" %}
```bash
flatpak install flathub io.github.bkbilly.lnxlink
flatpak run io.github.bkbilly.lnxlink
```
{% endcode %}

Some modules are not supported like `bluetooth`, `sys_updates`, `boot_select`.

You will also need to manually create a systemd service to start LNXlink on boot by creating a service file.

{% code title="/etc/systemd/system/lnxlink.service" %}
```toml
[Unit]
Description=LNXlink
After=network-online.target multi-user.target graphical.target
PartOf=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=5

ExecStart=flatpak run io.github.bkbilly.lnxlink

[Install]
WantedBy=default.target
```
{% endcode %}

This must be enabled to start on boot:

{% code lineNumbers="true" %}
```bash
sudo systemctl enable lnxlink.service
sudo systemctl daemon-reload
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
{% endtabs %}

### Run sudo commands

Some modules need to run specific commands as root. To fix this, allow only the required command to run without asking for a password:

```bash
# Edit the sudoers file:
sudo visudo
# Boot Select module (replace USER with your username):
USER ALL=(ALL) NOPASSWD: /usr/bin/efibootmgr

# WOL module:
USER ALL=(ALL) NOPASSWD: /usr/sbin/ethtool
```

## Uninstall

Remove LNXlink from your system.

{% tabs %}
{% tab title="User" %}
```bash
# Disables systemd service
systemctl --user disable lnxlink.service

# Remove systemd service
rm ~/.config/systemd/user/lnxlink.service

# Uninstall the package
pipx uninstall lnxlink
```
{% endtab %}

{% tab title="Root" %}
```bash
# Disables systemd service
sudo systemctl disable lnxlink.service

# Remove systemd service
sudo rm /etc/systemd/system/lnxlink.service

# Uninstall the package
pipx uninstall lnxlink
```
{% endtab %}
{% endtabs %}
