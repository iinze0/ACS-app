# ACS — Air Crack Station

**Made by Pakun & iinze0**

This is the desktop app.

## Install (use dpkg — apt /tmp will fail)

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

You should see **v1.4.0** and **Made by Pakun & iinze0**.

```bash
dpkg -s acs-app | grep Version
```

Uninstall: `sudo apt purge acs-app`

## C++ app

The native build is on GitHub too: [iinze0/ACS-cpp](https://github.com/iinze0/ACS-cpp)

```bash
wget -O /tmp/acs-cpp.deb https://github.com/iinze0/ACS-cpp/releases/download/v1.0.0/acs-cpp_1.0.0_amd64.deb
sudo dpkg -i /tmp/acs-cpp.deb
sudo ACS-cpp
```

If the window says Tk is missing:

```bash
sudo apt-get install -y python3-tk
sudo ACS-app
```

## Launch

```bash
sudo ACS-app
```

Also: **Applications → ACS**

Authorized lab / pentest use only. On launch, the app checks GitHub and installs a newer package by itself.

```
github.com/iinze0
github.com/iinze0/ACS-app
```
