import { Download, Radio, ShieldAlert } from "lucide-react";
import { CommandBlock, Field, PrimaryBtn } from "@/components/acs/command-block";
import { useAcs } from "@/lib/session";
import {
  SUITE,
  autoMonitorScript,
  restoreScript,
  stationInstallScript,
  type SuiteTool,
} from "@/lib/tools";

function sessionOf() {
  const s = useAcs.getState();
  return {
    iface: s.iface,
    monIface: s.monIface,
    channel: s.channel,
    bssid: s.bssid,
    essid: s.essid,
    client: s.client,
    capFile: s.capFile,
    wordlist: s.wordlist,
    band: s.band,
  };
}

export function TargetStrip() {
  const s = useAcs();
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="iface" value={s.iface} onChange={(v) => s.patch({ iface: v })} placeholder="wlan0" />
      <Field label="monitor" value={s.monIface} onChange={(v) => s.patch({ monIface: v })} placeholder="wlan0mon" />
      <Field label="channel" value={s.channel} onChange={(v) => s.patch({ channel: v })} placeholder="6" />
      <Field label="band" value={s.band} onChange={(v) => s.patch({ band: v === "abg" ? "abg" : "bg" })} placeholder="bg | abg" />
      <Field label="BSSID" value={s.bssid} onChange={(v) => s.patch({ bssid: v })} placeholder="AA:BB:CC:DD:EE:FF" />
      <Field label="ESSID" value={s.essid} onChange={(v) => s.patch({ essid: v })} placeholder="lab-ap" />
      <Field label="client" value={s.client} onChange={(v) => s.patch({ client: v })} placeholder="optional STA MAC" />
      <Field label="cap / prefix" value={s.capFile} onChange={(v) => s.patch({ capFile: v })} placeholder="handshake.cap" />
      <Field
        label="wordlist"
        value={s.wordlist}
        onChange={(v) => s.patch({ wordlist: v })}
        placeholder="/usr/share/wordlists/rockyou.txt"
      />
    </div>
  );
}

export function StationView() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">session</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Lab rack</h2>
        <p className="max-w-2xl text-sm text-muted">
          Set the card, AP, and capture once. Every aircrack-ng command below fills from this rack. Lab /
          authorized pentest only — this console builds commands, it does not transmit.
        </p>
      </header>
      <TargetStrip />
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["01", "Monitor", "airmon-ng check kill + start"],
          ["02", "Capture", "airodump-ng lock channel"],
          ["03", "Crack", "handshake → aircrack-ng"],
        ].map(([n, t, d]) => (
          <div key={n} className="rounded-md border border-line bg-surface p-4">
            <div className="font-sans text-xs text-primary">{n}</div>
            <div className="font-sans text-lg font-semibold">{t}</div>
            <div className="text-xs text-muted">{d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function MonitorView() {
  const s = useAcs();
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">airmon-ng</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Auto monitor mode</h2>
        <p className="max-w-2xl text-sm text-muted">
          Unblocks rfkill, kills NetworkManager/wpa_supplicant, starts monitor mode, and names the new
          iface (usually wlan0mon). Run on Kali as root.
        </p>
      </header>
      <ol className="space-y-2 text-sm">
        {[
          "rfkill unblock wifi",
          `airmon-ng check kill`,
          `airmon-ng start ${s.iface || "wlan0"}`,
          `iw dev  → expect ${s.monIface || "wlan0mon"}`,
        ].map((step, i) => (
          <li key={step} className="flex gap-3 rounded-md border border-line bg-surface px-3 py-3">
            <span className="font-sans text-primary">0{i + 1}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
      <CommandBlock label="auto monitor" code={autoMonitorScript(s.iface)} />
      <CommandBlock label="restore managed" code={restoreScript(s.monIface)} />
    </div>
  );
}

export function CaptureView() {
  const scan = SUITE.find((t) => t.id === "airodump")!;
  const sess = {
    ...sessionOf(),
    bssid: "",
  };
  const locked = SUITE.find((t) => t.id === "airodump")!.build(sessionOf());
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">airodump-ng</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Capture</h2>
        <p className="max-w-2xl text-sm text-muted">
          Wide scan first, note BSSID + channel, then lock and write a cap. Handshake shows in the upper
          right of airodump once a 4-way lands.
        </p>
      </header>
      <TargetStrip />
      <CommandBlock label="wide scan" code={scan.build(sess)} />
      <CommandBlock label="lock AP + write cap" code={locked} />
      <CommandBlock label="wpaclean" code={SUITE.find((t) => t.id === "wpaclean")!.build(sessionOf())} />
    </div>
  );
}

export function InjectView() {
  const inject = SUITE.filter((t) => t.cat === "inject");
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">aireplay-ng</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Inject</h2>
        <p className="max-w-2xl text-sm text-muted">
          Deauth is for capturing a WPA handshake against a lab AP you own. WEP helpers (ARP replay,
          chopchop, fragmentation, caffe-latte) live here too.
        </p>
      </header>
      <TargetStrip />
      <div className="space-y-4">
        {inject.map((t) => (
          <ToolCard key={t.id} tool={t} />
        ))}
      </div>
    </div>
  );
}

export function CrackView() {
  const s = useAcs();
  const chain = `need monitor + target set

# 1 capture (leave running)
airodump-ng -c ${s.channel || "6"} --bssid ${s.bssid || "AP_BSSID"} -w ${s.capFile.replace(/\.cap$/i, "") || "handshake"} ${s.monIface || "wlan0mon"}

# 2 other terminal — short deauth
aireplay-ng --deauth 6 -a ${s.bssid || "AP_BSSID"}${s.client ? ` -c ${s.client}` : ""} ${s.monIface || "wlan0mon"}

# 3 when WPA handshake: appears, Ctrl-C dump, then
aircrack-ng -w ${s.wordlist} ${s.bssid ? `-b ${s.bssid} ` : ""}${s.capFile.replace(/\.cap$/i, "") || "handshake"}-01.cap`;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">aircrack-ng</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Crack</h2>
        <p className="max-w-2xl text-sm text-muted">
          Handshake chain for WPA/WPA2, PTW for WEP, plus besside / wesside / easside / airolib.
        </p>
      </header>
      <TargetStrip />
      <CommandBlock label="handshake chain" code={chain} />
      {SUITE.filter((t) => t.cat === "crack").map((t) => (
        <ToolCard key={t.id} tool={t} />
      ))}
    </div>
  );
}

function ToolCard({ tool }: { tool: SuiteTool }) {
  const s = useAcs();
  void s.iface;
  void s.monIface;
  void s.channel;
  void s.bssid;
  void s.essid;
  void s.client;
  void s.capFile;
  void s.wordlist;
  void s.band;
  return (
    <article className="rounded-md border border-line bg-surface p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-sans text-lg font-semibold">{tool.name}</h3>
        <span className="text-[0.7rem] tracking-widest text-muted uppercase">{tool.cat}</span>
      </div>
      <p className="mt-1 text-sm text-muted">{tool.blurb}</p>
      <p className="mt-2 text-xs text-dim">{tool.usage}</p>
      <div className="mt-3">
        <CommandBlock label={tool.bin} code={tool.build(sessionOf())} />
      </div>
    </article>
  );
}

export function SuiteView() {
  const cats = ["monitor", "capture", "inject", "crack", "ap", "crypto", "util"] as const;
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">aircrack-ng</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Full suite</h2>
        <p className="max-w-2xl text-sm text-muted">
          Every binary that ships with aircrack-ng, wired to your session rack.
        </p>
      </header>
      <TargetStrip />
      {cats.map((cat) => {
        const tools = SUITE.filter((t) => t.cat === cat);
        if (!tools.length) return null;
        return (
          <section key={cat} className="space-y-3">
            <h3 className="font-sans text-sm tracking-[0.2em] text-primary uppercase">{cat}</h3>
            <div className="space-y-3">
              {tools.map((t) => (
                <ToolCard key={t.id} tool={t} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export function InstallView() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">kali</p>
        <h2 className="font-sans text-3xl font-bold tracking-tight">Crack station install</h2>
        <p className="max-w-2xl text-sm text-muted">
          Pulls the full aircrack-ng suite plus hashcat, hcx tools, wifite, reaver/bully, john, crunch,
          macchanger, mdk4. Then download ACS and run it as root.
        </p>
      </header>
      <div className="flex flex-wrap gap-3">
        <PrimaryBtn href="/acs.sh" download="acs.sh">
          <Download className="size-4" />
          download acs.sh
        </PrimaryBtn>
      </div>
      <CommandBlock
        label="on kali"
        code={`sudo bash acs.sh
# option 1 = station install
# option 2 = auto monitor mode`}
      />
      <CommandBlock label="station apt" code={stationInstallScript()} />
      <div className="flex gap-3 rounded-md border border-warn/40 bg-raised p-4 text-sm text-warn">
        <ShieldAlert className="mt-0.5 size-5 shrink-0" />
        <p>
          Authorized networks only. Monitor mode drops your own Wi-Fi until you restore managed mode
          (option 3 in acs.sh).
        </p>
      </div>
      <div className="flex gap-3 rounded-md border border-line bg-surface p-4 text-sm text-muted">
        <Radio className="mt-0.5 size-5 shrink-0 text-primary" />
        <p>
          ACS does not run radios in this browser. Copy a command or run the downloaded menu on Kali.
        </p>
      </div>
    </div>
  );
}
