# ACS-app

Desktop app for Air Crack Station. Made by **Pakun & iinze0**.

This is a window you open on Kali. It is not a website and it does not use npm.

The terminal script is still [iinze0/ACS](https://github.com/iinze0/ACS).

## Install

```bash
cd ~/ACS-app
git pull
sudo bash install.sh
```

Then open **ACS** from the application menu.

Or run it once without installing:

```bash
sudo python3 acs_app.py
```

If that says Tk is missing:

```bash
sudo apt-get update
sudo apt-get install -y python3-tk
```

Do not install `npm`. That package is broken on the Kali mirror and this app does not need it.

Authorized lab / pentest use only.
