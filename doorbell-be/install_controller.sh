#!/bin/bash

SERVICE_NAME="doorbell-controller"
SERVICE_DESCRIPTION="Doorbell App Controller Service"
WORKING_DIR="$(pwd)"
VENV_DIR="${WORKING_DIR}/venv"

USER=$(whoami)
GROUP=$(id -gn $USER)

echo "Creating Python virtual environment..."
python3 -m venv --system-site-packages  ${VENV_DIR}

echo "Installing Python dependencies..."
${VENV_DIR}/bin/pip install -r ${WORKING_DIR}/doorbell_controller/requirements.txt

echo "Creating systemd service file..."
cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=${SERVICE_DESCRIPTION}
After=network.target NetworkManager.service wpa_supplicant.service
Wants=network-online.target

[Service]
Environment="PYTHONPATH=${WORKING_DIR}"
ExecStart=${VENV_DIR}/bin/python -m doorbell_controller
WorkingDirectory=${WORKING_DIR}
User=${USER}
Group=${GROUP}
SupplementaryGroups=gpio video
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/${SERVICE_NAME}.service /etc/systemd/system/

echo "Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service

echo "Checking service status..."
sudo systemctl status ${SERVICE_NAME}.service --no-pager

echo "Setup complete! Your doorbell controller is now installed as a service."
