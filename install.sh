#!/bin/bash

# Global
basedir=/opt/lnxlink
if [ -f /etc/debian_version ]; then
    installcommand='apt-get --yes --force-yes install'
    system='debian/ubuntu'
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
echo -e "\e[35mLooking for Python3...\e[0m"
if [ -z $(which python3) ]; then
    echo -e "\e[31mPython3 not found, installing from $system package manager:\e[0m"
    sudo $installcommand python3
fi

echo -e "\e[35mLooking for PIP3...\e[0m"
if [ -z $(which pip3) ]; then
    echo -e "\e[31mPIP3 not found, installing from $system package manager:\e[0m"
    if [ system=='arch/manjaro' ]; then
        sudo $installcommand python-pip
    else
        sudo $installcommand python3-pip
    fi
fi

echo -e "\e[35mInstalling system dependencies...\e[0m"
if [ "$system" == "redhat/fedora" ]; then
    # python3-devel and  needed on fedora to install evdev (a dependency of pynput)
    sudo $installcommand kernel-headers-$(uname -r) python3-devel gcc
fi
if [ system != 'debian/ubuntu' ]; then
    echo -e "\n\n\e[31mSystem dependencies might not be correct...\e[0m"
fi
sudo $installcommand patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev


# Install Python requirements
echo -e "\e[35mInstalling LNXlink from PyPi...\e[0m"
sudo pip3 install -U lnxlink


# Done
echo -e "\n\n\nAll done!"
echo "Enjoy!!!"
