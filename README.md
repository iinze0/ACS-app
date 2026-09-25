# ACS-app — Air Crack Station

Python desktop client for **[ACS](https://github.com/iinze0/ACS)**.

[![release](https://img.shields.io/github/v/release/iinze0/ACS-app?style=flat-square)](https://github.com/iinze0/ACS-app/releases/latest)
[![license](https://img.shields.io/badge/license-MIT-0b7285?style=flat-square)](LICENSE)
[![python](https://img.shields.io/badge/python-3-3776ab?style=flat-square)](#install)

Made by [Pakun](https://github.com/brazyqueso) and [iinze0](https://github.com/iinze0)

Same station, in a window. Ships as a `.deb`, launches with `sudo ACS-app`, and checks GitHub for a newer package on start.

## Family

| Repo | Role |
|:-----|:-----|
| **[ACS](https://github.com/iinze0/ACS)** | Shell station |
| **[ACS-app](https://github.com/iinze0/ACS-app)** | This repo — Python desktop client |
| **[ACS-cpp](https://github.com/iinze0/ACS-cpp)** | Native C++ / GTK client |

## Install

Use `dpkg`. Installing a local `.deb` from `/tmp` with `apt` will fail.

```bash
wget -O /tmp/acs-app.deb https://github.com/iinze0/ACS-app/releases/download/v1.4.0/acs-app_1.4.0_all.deb
sudo dpkg -i /tmp/acs-app.deb
sudo ACS-app
```

One-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/iinze0/ACS-app/main/install-acs-app.sh | sudo bash
sudo ACS-app
```

```bash
dpkg -s acs-app | grep -E 'Version|Maintainer'
sudo apt purge acs-app    # uninstall
```

If the window reports missing Tk:

```bash
sudo apt-get install -y python3-tk
sudo ACS-app
```

## Launch

```bash
sudo ACS-app
```

Also available from **Applications → ACS**.

Prefer a native binary? Use **[ACS-cpp](https://github.com/iinze0/ACS-cpp)**.

## Disclaimer

Authorized lab and pentest use only. Run this only on networks you own or have written permission to test.

---

<p align="center">
  <a href="https://github.com/iinze0">iinze0</a> ·
  <a href="https://github.com/brazyqueso">Pakun</a> ·
  <a href="LICENSE">MIT</a>
</p>
