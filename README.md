# ACS — Air Crack Station

**Made by Pakun & iinze0**

This is the desktop app.

## Install (use dpkg — apt /tmp will fail)

```bash
wget -O /tmp/acs-app.deb https://github.com/iinze0/ACS-app/releases/download/v1.2.0/acs-app_1.2.0_all.deb
sudo dpkg -i /tmp/acs-app.deb
sudo ACS-app
```

One-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/iinze0/ACS-app/main/install-acs-app.sh | sudo bash
sudo ACS-app
```

You should see **v1.2.0** and **Made by Pakun & iinze0**.

```bash
dpkg -s acs-app | grep Version
```

Uninstall: `sudo apt purge acs-app`

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
