#!/bin/bash

# Global
basedir=/opt/lnxlink

# Installing with apt-get
echo -e "\e[35mLooking for GIT...\e[0m"
if [ -z $(which git) ]; then
    echo -e "\e[31mGit not found, installing from apt-get:\e[0m"
    sudo apt-get --yes --force-yes install git
fi


echo -e "\e[35mLooking for Python3...\e[0m"
if [ -z $(which python3) ]; then
    echo -e "\e[31mPython3 not found, installing from apt-get:\e[0m"
    sudo apt-get --yes --force-yes install python3
fi

echo -e "\e[35mLooking for PIP3...\e[0m"
if [ -z $(which pip3) ]; then
    echo -e "\e[31mPIP3 not found, installing from apt-get:\e[0m"
    sudo apt-get --yes --force-yes install python3-pip
fi


# Download from GitHub
if [ ! -d $basedir ]; then
    echo -e "\e[35mDownloading from GitHub...\e[0m"
    sudo git clone https://github.com/bkbilly/lnxlink.git $basedir
    cp $basedir/config_temp.yaml $basedir/config.yaml
else
    echo -e "\e[35mAlready exists, updating...\e[0m"
    sudo git -C $basedir pull origin master
fi

# Install Python requirements
echo -e "\e[35mInstalling Python requirements...\e[0m"
sudo pip3 install -r $basedir/requirements.txt
sudo apt install python3-alsaaudio

# Install as a service
echo -e "\e[35mInstalling as a service...\e[0m"
mkdir -p ~/.config/systemd/user/
cp $basedir/autostart/lnxlink.service ~/.config/systemd/user/lnxlink.service
chmod +x ~/.config/systemd/user/lnxlink.service
systemctl --user enable lnxlink.service
systemctl --user start lnxlink.service


# Done
echo -e "\n\n\nAll done!"
echo "Enjoy!!!"
