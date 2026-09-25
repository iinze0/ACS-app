import { createServerFn } from "@tanstack/react-start";

export type ProxyKind = "socks5" | "socks4" | "http";

const SOURCES: Record<ProxyKind, string[]> = {
  socks5: [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
  ],
  socks4: [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
  ],
  http: [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
  ],
};

const LINE = /^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})$/;

function shuffle<T>(items: T[]): T[] {
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = out[i];
    out[i] = out[j]!;
    out[j] = tmp!;
  }
  return out;
}

export const pullProxies = createServerFn({ method: "POST" })
  .validator((input: { kind?: string; count?: number }) => {
    const kind: ProxyKind =
      input?.kind === "socks4" || input?.kind === "http" ? input.kind : "socks5";
    const n = Number(input?.count ?? 8);
    const count = Number.isFinite(n) ? Math.min(40, Math.max(1, Math.floor(n))) : 8;
    return { kind, count };
  })
  .handler(async ({ data }) => {
    const seen = new Set<string>();
    const failed: string[] = [];
    for (const url of SOURCES[data.kind]) {
      try {
        const res = await fetch(url, {
          headers: { "user-agent": "acs-station" },
          signal: AbortSignal.timeout(20000),
        });
        if (!res.ok) {
          failed.push(url);
          continue;
        }
        const text = await res.text();
        for (const raw of text.split(/\r?\n/)) {
          const m = LINE.exec(raw.trim());
          if (m) seen.add(`${m[1]}:${m[2]}`);
        }
      } catch {
        failed.push(url);
      }
    }
    const all = shuffle([...seen]);
    return {
      kind: data.kind,
      total: all.length,
      proxies: all.slice(0, data.count),
      failed,
    };
  });
