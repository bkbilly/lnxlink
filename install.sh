#!/bin/bash


run_pipx() {
    if [ "$system" == "nixos" ]; then
        nix-shell -p python311Packages.pipx --run "pipx $*"
    else
        pipx "$@"
    fi
}

is_lnxlink_managed_by_pipx() {
    find_pipx_lnxlink_binary_path >/dev/null
}

find_pipx_lnxlink_binary_path() {
    local pipx_home
    local pipx_binary
    if [[ "${PIPX_HOME+x}" == "x" ]]; then
        pipx_home="${PIPX_HOME:-$PWD}"
    elif [[ -d "$HOME/.local/pipx" ]]; then
        pipx_home="$HOME/.local/pipx"
    else
        pipx_home="${XDG_DATA_HOME:-$HOME/.local/share}/pipx"
    fi
    pipx_binary="$pipx_home/venvs/lnxlink/bin/lnxlink"
    [[ -x "$pipx_binary" ]] || return 1
    echo "$pipx_binary"
}



# Global
if [ -f /etc/debian_version ]; then
    installcommand='apt-get --yes install'
    system='debian/ubuntu'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo apt-get update
elif [ -d /etc/yum.repos.d ]; then
    installcommand='dnf install -y'
    system='redhat/fedora'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo dnf makecache
elif [ -d /etc/pacman.d ]; then
    installcommand='pacman -S --noconfirm'
    system='arch/manjaro'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo pacman -Sy
elif command -v apk >/dev/null 2>&1; then
    installcommand='apk add'
    system='alpine'
    sudo apk update
elif [ -f /etc/SuSE-release ]; then
    installcommand='zypper install -y'
    system='suse/opensuse'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo zypper refresh
elif [ -f /etc/gentoo-release ]; then
    installcommand='emerge'
    system='gentoo'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo emerge --sync
elif [ -f /etc/slackware-version ]; then
    installcommand='slackpkg install'
    system='slackware'
    echo -e "\e[35mSlackware detected. Ensure slackpkg is configured properly.\e[0m"
elif command -v xbps-install >/dev/null 2>&1; then
    installcommand='xbps-install -y'
    system='void'
    echo -e "\e[35mUpdating package manager...\e[0m"
    sudo xbps-install -Sy
elif command -v nix-env >/dev/null 2>&1; then
    installcommand='nix-env -i'
    system='nixos'
    echo -e "\e[35mNote: Installing with nix-env. Consider using flakes or home-manager for better control.\e[0m"
else
    echo -e '\e[31mError: System type not recognized. Aborting.\e[0m'
    exit 1
fi


if [ "$system" != "nixos" ]; then
    # Installing system packages
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "\e[31mPython3 not found, installing from $system package manager:\e[0m"
        sudo $installcommand python3
    fi
    if ! command -v pipx >/dev/null 2>&1; then
        echo -e "\e[31mPIPX not found, installing from $system package manager:\e[0m"
        if [ "$system" == "arch/manjaro" ]; then
            sudo $installcommand python-pipx
            pipx ensurepath
        else
            sudo $installcommand pipx
            pipx ensurepath
        fi
    fi


    echo -e "\e[35mInstalling system dependencies...\e[0m"
    sudo $installcommand gcc cmake
    if [ "$system" == "debian/ubuntu" ]; then
        sudo $installcommand python3-dev libasound2-dev portaudio19-dev python3-pyaudio
    elif [ "$system" == "redhat/fedora" ]; then
        sudo $installcommand kernel-headers python3-devel alsa-lib-devel portaudio-devel python3-pyaudio
    elif [ "$system" == "alpine" ]; then
        sudo $installcommand linux-headers python3-dev musl-dev
    elif [ "$system" == "arch/manjaro" ]; then
        sudo $installcommand linux-headers python-pyaudio portaudio python-pyaudio
    elif [ "$system" == "suse/opensuse" ]; then
        sudo $installcommand python3-devel gcc-c++ make
    elif [ "$system" == "gentoo" ]; then
        sudo $installcommand dev-lang/python dev-python/pip dev-util/cmake
    elif [ "$system" == "void" ]; then
        sudo $installcommand python3-devel base-devel
    fi


    echo -e "\e[35mInstalling extra packages...\e[0m"
    sudo $installcommand xdotool xdg-utils swayidle

    # Manual Steps
    if [ "$system" == "alpine" ]; then
        echo -e "\e[31mManual steps needed for alpine...\e[0m"
        echo "# Edit the file: ~/.local/share/pipx/venvs/lnxlink/pyvenv.cfg"
        echo "# Set the value from false to true, to import also system packages, that possibly were installed after venv creation:"
        echo "include-system-site-packages = true"
        echo "Run this command:"
        echo "pipx inject lnxlink dbus-idle"
    fi
fi


# Install LNXlink
LNX_CONFIG_PATH=""

if is_lnxlink_managed_by_pipx; then
    echo -e "\e[31mUpgrading LNXlink...\e[0m"
    run_pipx upgrade lnxlink
    PIPX_STATUS=$?
    if [ "$PIPX_STATUS" -ne 0 ]; then
        echo -e '\e[31mError: lnxlink upgrade failed. Aborting.\e[0m'
        exit "$PIPX_STATUS"
    fi
else
    echo -e "\e[35mInstalling LNXlink...\e[0m"
    if [ "$system" == "nixos" ]; then
        run_pipx install lnxlink
        PIPX_STATUS=$?
        if [ "$PIPX_STATUS" -eq 0 ]; then
            run_pipx ensurepath
            PIPX_STATUS=$?
        fi
    else
        run_pipx install lnxlink
        PIPX_STATUS=$?
    fi
    if [ "$PIPX_STATUS" -ne 0 ]; then
        echo -e '\e[31mError: lnxlink installation failed. Aborting.\e[0m'
        exit "$PIPX_STATUS"
    fi
    LNX_CONFIG_PATH=$(pwd)/lnxlink.yaml
fi

LNX_PATH=$(find_pipx_lnxlink_binary_path)
LNX_EXIT_STATUS=$?
if [ "$LNX_PATH" == "" ] || [ "$LNX_EXIT_STATUS" -ne 0 ]; then
    echo -e '\e[31mError: pipx did not install the lnxlink executable. Aborting.\e[0m'
    exit 1
fi
if [ "$LNX_CONFIG_PATH" != "" ]; then
    "$LNX_PATH" -sc lnxlink.yaml
fi


# Done
echo -e "\e[35m\n\n\nInstallation Summary:\e[0m"
echo -e "\e[35m---------------------\e[0m"
echo -e "\e[35mSystem Type: $system\e[0m"
echo -e "\e[35mLNXlink Path: $LNX_PATH\e[0m"
if [ "$LNX_CONFIG_PATH" != "" ]; then
    echo -e "\e[35mLNXlink Config Created At: $LNX_CONFIG_PATH\e[0m"
fi
echo -e "\e[35m---------------------\e[0m"
echo -e "\e[35m\n\nAll done!\nEnjoy\e[0m"
