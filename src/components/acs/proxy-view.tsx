import { useState } from "react";
import { Loader2, Shield } from "lucide-react";
import { CommandBlock } from "@/components/acs/command-block";
import { pullProxies, type ProxyKind } from "@/lib/proxies.functions";
import { cn } from "@/lib/utils";

type ChainMode = "dynamic_chain" | "strict_chain" | "random_chain";

const KINDS: { id: ProxyKind; label: string }[] = [
  { id: "socks5", label: "SOCKS5" },
  { id: "socks4", label: "SOCKS4" },
  { id: "http", label: "HTTP" },
];

const MODES: { id: ChainMode; label: string }[] = [
  { id: "dynamic_chain", label: "Dynamic" },
  { id: "strict_chain", label: "Strict" },
  { id: "random_chain", label: "Random" },
];

function confFor(kind: ProxyKind, mode: ChainMode, proxies: string[]) {
  const lines = [
    "# ACS proxy chain — IPs pulled from GitHub",
    mode,
    ...(mode === "random_chain" ? [`chain_len = ${proxies.length}`] : []),
    "proxy_dns",
    "tcp_read_time_out 15000",
    "tcp_connect_time_out 8000",
    "[ProxyList]",
    ...proxies.map((p) => {
      const [ip, port] = p.split(":");
      return `${kind} ${ip} ${port}`;
    }),
  ];
  return lines.join("\n");
}

export function ProxyView() {
  const [kind, setKind] = useState<ProxyKind>("socks5");
  const [mode, setMode] = useState<ChainMode>("dynamic_chain");
  const [count, setCount] = useState("8");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [proxies, setProxies] = useState<string[]>([]);

  async function pull() {
    setBusy(true);
    setError("");
    try {
      const n = Number(count);
      const result = await pullProxies({
        data: { kind, count: Number.isFinite(n) ? n : 8 },
      });
      setTotal(result.total);
      setProxies(result.proxies);
      if (result.total === 0) {
        setError("GitHub lists came back empty. Try again.");
      }
    } catch (err) {
      setProxies([]);
      setTotal(0);
      setError(err instanceof Error ? err.message : "Could not reach GitHub");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="font-sans text-xs tracking-[0.25em] text-primary uppercase">anonymity</p>
        <h2 className="flex items-center gap-2 font-sans text-3xl font-bold tracking-tight">
          <Shield className="size-7 text-primary" />
          Proxy chain
        </h2>
        <p className="max-w-2xl text-sm text-muted">
          Pulls live proxy addresses from public GitHub lists, then builds a proxychains file. Free
          proxies die often — dynamic mode skips the dead ones.
        </p>
      </header>

      <div className="grid gap-4 rounded-md border border-line bg-surface p-4">
        <div className="flex flex-wrap gap-2">
          {KINDS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setKind(item.id)}
              className={cn(
                "min-h-11 rounded-md px-4 font-sans text-sm",
                kind === item.id ? "bg-primary text-bg" : "border border-line text-fg",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {MODES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setMode(item.id)}
              className={cn(
                "min-h-11 rounded-md px-4 font-sans text-sm",
                mode === item.id ? "bg-primary text-bg" : "border border-line text-fg",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
        <label className="flex max-w-xs flex-col gap-1">
          <span className="font-sans text-xs tracking-widest text-muted uppercase">hops</span>
          <input
            inputMode="numeric"
            value={count}
            onChange={(e) => setCount(e.target.value.replace(/[^\d]/g, "").slice(0, 2))}
            className="min-h-11 rounded-md border border-line bg-bg px-3 font-mono text-sm text-fg outline-none focus:border-primary"
          />
        </label>
        <button
          type="button"
          onClick={pull}
          disabled={busy}
          className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-primary px-4 font-sans text-sm font-semibold text-bg disabled:opacity-60 sm:w-auto"
        >
          {busy ? <Loader2 className="size-4 animate-spin" /> : null}
          {busy ? "Pulling from GitHub" : "Pull proxies"}
        </button>
        {error ? <p className="text-sm text-warn">{error}</p> : null}
        {total > 0 ? (
          <p className="text-sm text-muted">
            {total.toLocaleString()} unique addresses on GitHub. Chain uses {proxies.length}.
          </p>
        ) : null}
      </div>

      {proxies.length > 0 ? (
        <>
          <ul className="grid gap-2 sm:grid-cols-2">
            {proxies.map((p) => (
              <li
                key={p}
                className="rounded-md border border-line bg-surface px-3 py-3 font-mono text-sm text-fg"
              >
                {p}
              </li>
            ))}
          </ul>
          <CommandBlock label="~/.acs/proxychains.conf" code={confFor(kind, mode, proxies)} />
        </>
      ) : null}
    </div>
  );
}
