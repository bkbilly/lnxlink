#!/bin/bash

# Global
basedir=/opt/lnxlink
if [ -f /etc/debian_version ]; then
    installcommand='apt-get --yes --force-yes install'
    system='debian/ubuntu'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo apt-get update
elif [ -d /etc/yum.repos.d ]; then
    installcommand='dnf install -y'
    system='redhat/fedora'
elif [ -d /etc/pacman.d ]; then
    installcommand='pacman -S --noconfirm '
    system='arch/manjaro'
else
    echo 'Warning! System type not recognized. Trying apt package manager.'
    installcommand='apt-get --yes --force-yes install'
    system='debian/ubuntu'
fi

# Installing system packages
if [ -z $(which python3) ]; then
    echo -e "\e[31mPython3 not found, installing from $system package manager:\e[0m"
    sudo $installcommand python3
fi
if [ -z $(which pipx) ]; then
    echo -e "\e[31mPIPX not found, installing from $system package manager:\e[0m"
    sudo $installcommand pipx
    pipx ensurepath
fi


echo -e "\e[35mInstalling system dependencies...\e[0m"
if [ "$system" == "redhat/fedora" ]; then
    # python3-devel and  needed on fedora to install evdev (a dependency of pynput)
    sudo $installcommand kernel-headers-$(uname -r) python3-devel gcc
fi
if [ "$system" != 'debian/ubuntu' ]; then
    echo -e "\n\n\e[31mSystem dependencies might not be correct...\e[0m"
fi

if [[ $(pidof dbus-daemon) ]]; then
    echo -e "\e[35mFound dbus...\e[0m"
    sudo $installcommand patchelf meson libdbus-glib-1-dev libglib2.0-dev libcairo2-dev libgirepository1.0-dev
fi
sudo $installcommand libasound2-dev upower xdotool xdg-utils python3-pyaudio portaudio19-dev


# Install LNXlink
if [ -z $(which lnxlink) ]; then
    echo -e "\e[35mInstalling LNXlink...\e[0m"
    pipx install lnxlink
    lnxlink -sc config.yaml
else
    echo -e "\e[31mUpgrading LNXlink...\e[0m"
    pipx upgrade lnxlink
fi

# Done
echo -e "\e[35m\n\n\nAll done!\e[0m"
echo -e "\e[35mEnjoy!!!\e[0m"
