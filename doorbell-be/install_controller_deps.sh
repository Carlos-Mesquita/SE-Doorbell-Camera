#!/bin/bash

check_apt_package() {
    local package_name="$1"
    if dpkg-query -W -f='${Status}' "$package_name" 2>/dev/null | grep -q "install ok installed"; then
        echo "✅ $package_name is already installed"
        return 0
    else
        echo "❌ $package_name is not installed"
        return 1
    fi
}

echo "Checking for required dependencies..."

check_apt_package "python3-dev"
python_dev_installed=$?

check_apt_package "python3-picamera2"
picamera_installed=$?

if [ "$python_dev_installed" -ne 0 ] || [ "$picamera_installed" -ne 0 ]; then
    echo "Updating apt..."
    sudo apt update

    if [ "$python_dev_installed" -ne 0 ]; then
        echo "Installing python3-dev..."
        sudo apt install -y python3-dev
    fi

    if [ "$picamera_installed" -ne 0 ]; then
        echo "Installing python3-picamera2..."
        sudo apt install -y python3-picamera2
    fi
fi

echo "Installing pip requirements..."
sudo pip3 install -r ./doorbell_controller/requirements.txt


echo "Checking and adding user to required groups..."
USER=$(whoami)
GROUP_CHANGES=0

if ! groups $USER | grep -q "\bgpio\b"; then
    echo "Adding user $USER to gpio group..."
    sudo usermod -a -G gpio $USER
    GROUP_CHANGES=1
fi

if ! groups $USER | grep -q "\bvideo\b"; then
    echo "Adding user $USER to video group..."
    sudo usermod -a -G video $USER
    GROUP_CHANGES=1
fi

if [ "$GROUP_CHANGES" -eq 1 ]; then
    echo ""
    echo "⚠️  IMPORTANT: Group permissions were updated  ⚠️"
    echo "=================================================="
    echo "Your user account was added to the gpio and/or video groups."
    echo "These changes won't take effect until you log out and log back in."
    echo ""
    echo "After logging back in, run: ./install_controller.sh"
    echo ""
else
    echo ""
    echo "✅  All dependencies successfully installed!  ✅"
    echo "=================================================="
    echo "Installing service now..."
    echo ""
    ./install_controller.sh
fi