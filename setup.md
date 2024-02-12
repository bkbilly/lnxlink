---
description: Get started with LNXlink
---

# 🖥 Setup

## Installation

Select the installation type you want:

{% tabs %}
{% tab title="Normal" %}
Install LNXlink and it's dependencies. It will create a `config.yaml` file and it will guide you through the basic configuration setup:

{% code overflow="wrap" lineNumbers="true" %}
```bash
curl -L https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh | bash
```
{% endcode %}

You can manually update the configuration file `config.yaml` and restart the service with the use of systemctl:

{% code overflow="wrap" lineNumbers="true" %}
```bash
systemctl --user restart lnxlink.service  # For user installations
sudo systemctl restart lnxlink.service  # For root installations
```
{% endcode %}
{% endtab %}

{% tab title="Docker" %}
Docker is not recommended for desktop environments because it limits many modules which can't run properly. You can download LNXlink image and setup the config directory:

{% code overflow="wrap" %}
```bash
docker run --network host -v ~/config_lnxlink/:/opt/lnxlink/config/ -it bkbillybk/lnxlink:latest
```
{% endcode %}

You can also run as a docker compose image by creating a `docker-compose.yaml` file:

```yaml
version: "3"
services:
  lnxlink:
    image: bkbillybk/lnxlink:latest
    container_name: lnxlink
    restart: unless-stopped
    network_mode: host
    privileged: true
    stdin_open: true
    tty: true
    volumes:
      - ~/config_lnxlink/:/opt/lnxlink/config/
      - /var/run/reboot-required:/var/run/reboot-required:ro
```

Run docker compose image:

```bash
docker compose -f docker-compose.yaml up
```
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

Some commands need to run as a root user. To fix this, you need to allow some of them to run without asking for password:

```bash
# Edit the sudoers file:
sudo visudo
# Add this line at the end (replace USER with your username):
USER ALL=(ALL) NOPASSWD: /usr/sbin/grub-reboot
USER ALL=(ALL) NOPASSWD: /bin/systemctl
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
pip3 uninstall -U lnxlink
```
{% endtab %}

{% tab title="Root" %}
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
