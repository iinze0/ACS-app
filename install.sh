#!/usr/bin/env bash
# ACS app — Made by Pakun & iinze0
# Installs the .deb already in this clone. Prefer install-acs-app.sh on a fresh machine.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo "Run:  sudo bash install.sh"
  echo "Then: sudo ACS-app"
  exit 1
fi
src_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER="$(tr -d '[:space:]' < "$src_dir/VERSION")"
DEB="$src_dir/apt/acs-app_${VER}_all.deb"
[[ -f $DEB ]] || { echo "Missing $DEB"; exit 1; }
dpkg -i "$DEB" || apt-get install -f -y
echo "ACS app installed. Made by Pakun & iinze0"
echo "  sudo ACS-app"
