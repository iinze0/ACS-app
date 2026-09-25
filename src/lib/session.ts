import { create } from "zustand";

export type ViewId =
  | "station"
  | "monitor"
  | "capture"
  | "inject"
  | "crack"
  | "suite"
  | "install"
  | "proxy";

export type Session = {
  iface: string;
  monIface: string;
  channel: string;
  bssid: string;
  essid: string;
  client: string;
  capFile: string;
  wordlist: string;
  band: "bg" | "abg";
};

type Store = Session & {
  view: ViewId;
  hydrated: boolean;
  setView: (v: ViewId) => void;
  patch: (p: Partial<Session>) => void;
  hydrate: () => void;
};

const defaults: Session = {
  iface: "wlan0",
  monIface: "wlan0mon",
  channel: "6",
  bssid: "",
  essid: "",
  client: "",
  capFile: "handshake.cap",
  wordlist: "/usr/share/wordlists/rockyou.txt",
  band: "bg",
};

function persist(s: Session) {
  try {
    localStorage.setItem("acs-session", JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

export const useAcs = create<Store>((set, get) => ({
  ...defaults,
  view: "station",
  hydrated: false,
  setView: (view) => set({ view }),
  patch: (p) => {
    set(p);
    const s = get();
    persist({
      iface: s.iface,
      monIface: s.monIface,
      channel: s.channel,
      bssid: s.bssid,
      essid: s.essid,
      client: s.client,
      capFile: s.capFile,
      wordlist: s.wordlist,
      band: s.band,
    });
  },
  hydrate: () => {
    if (get().hydrated) return;
    try {
      const raw = localStorage.getItem("acs-session");
      if (raw) set({ ...JSON.parse(raw), hydrated: true });
      else set({ hydrated: true });
    } catch {
      set({ hydrated: true });
    }
  },
}));
