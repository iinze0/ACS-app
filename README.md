# ACS-app

Air Crack Station as an app. Made by **Pakun & iinze0**.

This is the UI. The Kali terminal script lives in [iinze0/ACS](https://github.com/iinze0/ACS).

## What it does

- Lab rack for interface, BSSID, channel, capture file, and wordlist
- Monitor, capture, inject, and crack screens that fill commands from that rack
- Full aircrack-ng suite reference
- **Proxy** — pulls live proxy addresses from GitHub lists and builds a proxychains file

The browser does not transmit. Copy a command or download `acs.sh` and run it on Kali.

Authorized lab / pentest use only.

## Run on Kali

Do **not** use `sudo apt install npm`. Those packages 404 on the Kali mirror.

```bash
cd ~/ACS-app
bash setup-kali.sh
npm install
npm run dev
```

Then open http://127.0.0.1:8080

`setup-kali.sh` drops Node 22 into `/usr/local` from nodejs.org. If `node` is still the old command after that, run `hash -r`.
