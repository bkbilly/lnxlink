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
else
    echo 'Warning! System type not recognized. Trying apt package manager.'
    installcommand='apt-get --yes --force-yes install'
    system='debian/ubuntu'
fi

# Installing with apt-get
echo -e "\e[35mLooking for GIT...\e[0m"
if [ -z $(which git) ]; then
    echo -e "\e[31mGit not found, installing from $system package manager:\e[0m"
    sudo $installcommand git
fi


echo -e "\e[35mLooking for Python3...\e[0m"
if [ -z $(which python3) ]; then
    echo -e "\e[31mPython3 not found, installing from $system package manager:\e[0m"
    sudo $installcommand python3
fi

echo -e "\e[35mLooking for PIP3...\e[0m"
if [ -z $(which pip3) ]; then
    echo -e "\e[31mPIP3 not found, installing from $system package manager:\e[0m"
    sudo $installcommand python3-pip
fi


# Download from GitHub
if [ ! -d $basedir ]; then
    echo -e "\e[35mDownloading from GitHub...\e[0m"
    sudo git clone https://github.com/bkbilly/lnxlink.git $basedir
    sudo cp $basedir/config_temp.yaml $basedir/config.yaml
else
    echo -e "\e[35mAlready exists, updating...\e[0m"
    sudo git -C $basdir stash
    sudo git -C $basedir pull origin master
fi

# Install Python requirements
echo -e "\e[35mInstalling Python requirements...\e[0m"
if [ "$system" == "redhat/fedora" ]; then
    # python3-devel and  needed on fedora to install evdev (a dependency of pynput)
    sudo $installcommand kernel-headers-$(uname -r) python3-devel gcc
fi
sudo $installcommand python3-alsaaudio
sudo pip3 install -r $basedir/requirements.txt

# User config
echo -e "\e[35mUser configuration setup...\e[0m"
sudo $basedir/config.py $basedir/config.yaml

echo -e "\e[35mChoose type of service to install...\e[0m"
read -p "Headless service [y/N]: " -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Install as a system service
    echo -e "\e[35mInstalling as a headless service...\e[0m"
    sudo cp $basedir/autostart/lnxlink_headless.service /etc/systemd/system/lnxlink.service
    sudo chmod +x /etc/systemd/system/lnxlink.service
    sudo systemctl enable lnxlink.service
    sudo systemctl restart lnxlink.service
else
    # Install as a user service
    echo -e "\e[35mInstalling as a user service...\e[0m"
    mkdir -p ~/.config/systemd/user/
    cp $basedir/autostart/lnxlink_user.service ~/.config/systemd/user/lnxlink.service
    chmod +x ~/.config/systemd/user/lnxlink.service
    systemctl --user enable lnxlink.service
    systemctl --user restart lnxlink.service
fi


# Done
echo -e "\n\n\nAll done!"
echo "Enjoy!!!"
