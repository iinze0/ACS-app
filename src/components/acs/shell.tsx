import { useEffect } from "react";
import {
  Antenna,
  Download,
  KeyRound,
  LayoutGrid,
  Radio,
  Shield,
  Terminal,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAcs, type ViewId } from "@/lib/session";
import {
  CaptureView,
  CrackView,
  InjectView,
  InstallView,
  MonitorView,
  StationView,
  SuiteView,
} from "@/components/acs/views";
import { ProxyView } from "@/components/acs/proxy-view";

const NAV: { id: ViewId; label: string; icon: typeof Radio }[] = [
  { id: "station", label: "Station", icon: Radio },
  { id: "monitor", label: "Monitor", icon: Antenna },
  { id: "capture", label: "Capture", icon: Terminal },
  { id: "inject", label: "Inject", icon: Zap },
  { id: "crack", label: "Crack", icon: KeyRound },
  { id: "suite", label: "Suite", icon: LayoutGrid },
  { id: "proxy", label: "Proxy", icon: Shield },
  { id: "install", label: "Install", icon: Download },
];

export function AcsShell() {
  const view = useAcs((s) => s.view);
  const setView = useAcs((s) => s.setView);
  const iface = useAcs((s) => s.iface);
  const mon = useAcs((s) => s.monIface);
  const hydrate = useAcs((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <div className="acs-grid min-h-dvh bg-bg text-fg">
      <header className="sticky top-0 z-20 border-b border-line bg-bg/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-md border border-primary/40 bg-surface font-sans text-lg font-bold text-primary">
              ACS
            </div>
            <div>
              <div className="font-sans text-lg font-bold leading-none tracking-wide">Air Crack Station</div>
              <div className="text-[0.7rem] tracking-widest text-muted uppercase">
                Made by Pakun & iinze0
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[0.7rem] tracking-wider text-muted uppercase">
            <span className="rounded-sm border border-line px-2 py-1">iface {iface || "—"}</span>
            <span className="rounded-sm border border-line px-2 py-1">mon {mon || "—"}</span>
            <span className="rounded-sm border border-primary/40 px-2 py-1 text-primary">lab only</span>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 lg:flex-row">
        <nav
          className="flex gap-1 overflow-x-auto lg:w-48 lg:flex-col lg:overflow-visible"
          aria-label="ACS sections"
        >
          {NAV.map((item) => {
            const Icon = item.icon;
            const on = view === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setView(item.id)}
                className={cn(
                  "flex min-h-11 min-w-[7.5rem] items-center gap-2 rounded-md px-3 font-sans text-sm",
                  on
                    ? "bg-primary text-bg"
                    : "border border-line bg-surface text-fg hover:border-primary/50",
                )}
              >
                <Icon className="size-4 shrink-0" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <main className="min-w-0 flex-1 pb-16">
          {view === "station" && <StationView />}
          {view === "monitor" && <MonitorView />}
          {view === "capture" && <CaptureView />}
          {view === "inject" && <InjectView />}
          {view === "crack" && <CrackView />}
          {view === "suite" && <SuiteView />}
          {view === "proxy" && <ProxyView />}
          {view === "install" && <InstallView />}
        </main>
      </div>
    </div>
  );
}
