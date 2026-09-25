#!/usr/bin/env bash
# Install Node from nodejs.org. Do not use apt install npm — Kali's mirror 404s.
set -euo pipefail
VER="${NODE_VER:-v22.23.3}"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) NODE_ARCH=x64 ;;
  aarch64|arm64) NODE_ARCH=arm64 ;;
  *) echo "unsupported arch: $ARCH"; exit 1 ;;
esac
TMP="$(mktemp -d)"
URL="https://nodejs.org/dist/${VER}/node-${VER}-linux-${NODE_ARCH}.tar.xz"
echo "downloading $URL"
curl -fL --retry 3 -o "$TMP/node.tar.xz" "$URL"
sudo tar -xJf "$TMP/node.tar.xz" -C /usr/local --strip-components=1
rm -rf "$TMP"
hash -r
echo "node $(node -v)"
echo "npm  $(npm -v)"
