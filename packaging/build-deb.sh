#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VER="$(tr -d '[:space:]' < "$ROOT/VERSION")"
PKG="/tmp/acs-app-deb-build/acs-app_${VER}_all"
rm -rf /tmp/acs-app-deb-build
mkdir -p "$PKG/DEBIAN" "$PKG/usr/bin" "$PKG/usr/lib/acs-app" \
  "$PKG/usr/share/applications" "$PKG/usr/share/pixmaps" \
  "$PKG/usr/share/doc/acs-app" "$PKG/var/lib/acs-app"
install -m 0755 "$ROOT/acs_app.py" "$PKG/usr/lib/acs-app/acs_app.py"
install -m 0644 "$ROOT/acs.svg" "$PKG/usr/share/pixmaps/acs-app.svg"
cat > "$PKG/usr/bin/ACS-app" << 'EOF'
#!/bin/sh
if [ "$(id -u)" -ne 0 ]; then
  if command -v pkexec >/dev/null 2>&1; then
    exec pkexec /usr/bin/ACS-app "$@"
  fi
  exec sudo /usr/bin/ACS-app "$@"
fi
exec python3 /usr/lib/acs-app/acs_app.py "$@"
EOF
chmod 0755 "$PKG/usr/bin/ACS-app"
ln -sf ACS-app "$PKG/usr/bin/acs-app"
cat > "$PKG/usr/share/applications/acs-app.desktop" << 'EOF'
[Desktop Entry]
Name=ACS
GenericName=Air Crack Station
Comment=ACS desktop app. Made by Pakun & iinze0.
Exec=pkexec /usr/bin/ACS-app
Icon=acs-app
Terminal=false
Type=Application
Categories=System;Security;Network;
Keywords=acs;kali;aircrack;pentest;pakun;iinze0;
EOF
cat > "$PKG/usr/share/doc/acs-app/copyright" << EOF
ACS app — Air Crack Station
Made by Pakun & iinze0
https://github.com/iinze0/ACS-app
EOF
sed "s/^Version:.*/Version: ${VER}/" "$ROOT/packaging/DEBIAN/control" > "$PKG/DEBIAN/control"
install -m 0755 "$ROOT/packaging/DEBIAN/postinst" "$PKG/DEBIAN/postinst"
install -m 0755 "$ROOT/packaging/DEBIAN/prerm" "$PKG/DEBIAN/prerm"
install -m 0755 "$ROOT/packaging/DEBIAN/postrm" "$PKG/DEBIAN/postrm"
SIZE="$(du -sk "$PKG" | awk '{print $1}')"
sed -i "s/^Installed-Size:.*/Installed-Size: ${SIZE}/" "$PKG/DEBIAN/control"
mkdir -p "$ROOT/apt"
dpkg-deb --root-owner-group --build "$PKG" "$ROOT/apt/acs-app_${VER}_all.deb"
cp -f "$ROOT/apt/acs-app_${VER}_all.deb" "$ROOT/acs-app_${VER}_all.deb"
(
  cd "$ROOT/apt"
  dpkg-scanpackages -m . /dev/null > Packages
  gzip -9c Packages > Packages.gz
  cat > Release << EOF
Origin: ACS
Label: ACS app
Suite: stable
Codename: stable
Architectures: all
Components: main
Description: ACS app — Air Crack Station
EOF
)
echo "built $ROOT/apt/acs-app_${VER}_all.deb"
