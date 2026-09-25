#!/usr/bin/env bash
# Install the ACS desktop app into the Kali application menu.
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "Installing python3-tk (not npm)..."
  sudo apt-get update
  sudo apt-get install -y python3-tk
fi

sudo install -d /usr/local/share/acs-app
sudo install -m 755 acs_app.py /usr/local/share/acs-app/acs_app.py
sudo tee /usr/local/bin/acs-app >/dev/null << 'EOF'
#!/bin/sh
exec python3 /usr/local/share/acs-app/acs_app.py "$@"
EOF
sudo chmod 755 /usr/local/bin/acs-app

sudo tee /usr/share/applications/acs-app.desktop >/dev/null << 'EOF'
[Desktop Entry]
Type=Application
Name=ACS
GenericName=Air Crack Station
Comment=Air Crack Station desktop app by Pakun and iinze0
Exec=pkexec /usr/local/bin/acs-app
Icon=network-wireless
Terminal=false
Categories=Network;System;
EOF

echo "Installed. Open ACS from the application menu, or run: acs-app"
