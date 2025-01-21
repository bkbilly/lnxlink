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
    sudo pacman -Sy
elif [ -z $(which apk) ]; then
    installcommand='apk add'
    system='alpine'
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
    if [ "$system" == "arch/manjaro" ]; then
        sudo $installcommand python-pipx
    else
        sudo $installcommand pipx
    fi
    pipx ensurepath
fi


echo -e "\e[35mInstalling system dependencies...\e[0m"
if [ "$system" == "redhat/fedora" ]; then
    sudo $installcommand gcc kernel-headers python3-devel
elif [ "$system" == "alpine" ]; then
    sudo $installcommand gcc linux-headers python3-dev musl-dev
elif [ "$system" == "arch/manjaro" ]; then
    sudo $installcommand gcc linux-headers
fi


if [[ $(pidof dbus-daemon) ]]; then
    echo -e "\e[35mFound dbus...\e[0m"
    sudo $installcommand patchelf meson cmake
    if [ "$system" == "redhat/fedora" ]; then
        sudo $installcommand dbus-glib-devel glib2-devel cairo-devel gobject-introspection-devel python3-gobject-devel cairo-gobject-devel
    elif [ "$system" == "alpine" ]; then
        sudo $installcommand py3-gobject3 py3-dasbus
    elif [ "$system" == "arch/manjaro" ]; then
        sudo $installcommand dbus-glib glib2-devel cairo gobject-introspection libgirepository
    else
        sudo $installcommand libdbus-glib-1-dev libglib2.0-dev libcairo2-dev libgirepository1.0-dev
    fi
fi


echo -e "\e[35mInstalling extra packages...\e[0m"
sudo $installcommand upower xdotool xdg-utils
if [ "$system" == "redhat/fedora" ]; then
    sudo $installcommand alsa-lib-devel portaudio-devel python3-pyaudio
elif [ "$system" == "arch/manjaro" ]; then
    sudo $installcommand python-pyaudio portaudio python-pyaudio
else
    sudo $installcommand libasound2-dev portaudio19-dev python3-pyaudio
fi


# Install LNXlink
if [ -z $(which lnxlink) ]; then
    echo -e "\e[35mInstalling LNXlink...\e[0m"
    pip install -U pipx
    pipx install lnxlink
    lnxlink -sc config.yaml
else
    echo -e "\e[31mUpgrading LNXlink...\e[0m"
    pipx upgrade lnxlink
fi


# Manual Steps
if [ "$system" == "alpine" ]; then
    echo -e "\e[31mManual steps needed for alpine...\e[0m"
    echo "# Edit the file: ~/.local/share/pipx/venvs/lnxlink/pyvenv.cfg"
    echo "# Set the value from false to true, to import also system packages, that possibly were installed after venv creation:"
    echo "include-system-site-packages = true"
    echo "Run this command:"
    echo "pipx inject lnxlink dbus-idle"
fi


# Done
echo -e "\e[35m\n\n\nAll done!\e[0m"
echo -e "\e[35mEnjoy!!!\e[0m"
