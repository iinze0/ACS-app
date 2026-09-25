import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function CommandBlock({
  code,
  label = "command",
}: {
  code: string;
  label?: string;
}) {
  const [ok, setOk] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setOk(true);
      setTimeout(() => setOk(false), 1400);
    } catch {
      /* ignore */
    }
  }
  return (
    <div className="overflow-hidden rounded-md border border-line bg-bg">
      <div className="flex items-center justify-between border-b border-line px-3 py-2">
        <span className="font-sans text-xs tracking-widest text-muted uppercase">{label}</span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex min-h-11 items-center gap-2 px-2 font-sans text-xs text-primary hover:text-fg"
        >
          {ok ? <Check className="size-4" /> : <Copy className="size-4" />}
          {ok ? "copied" : "copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-3 text-xs leading-relaxed whitespace-pre-wrap text-primary sm:text-sm">
        {code}
      </pre>
    </div>
  );
}

export function Field({
  label,
  value,
  onChange,
  placeholder,
  mono = true,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
}) {
  return (
    <label className="flex min-h-11 flex-col gap-1">
      <span className="font-sans text-[0.7rem] tracking-widest text-muted uppercase">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          "min-h-11 rounded-md border border-line bg-bg px-3 text-sm text-fg outline-none",
          "placeholder:text-muted/60 focus:border-primary",
          mono && "font-mono",
        )}
      />
    </label>
  );
}

export function PrimaryBtn({
  children,
  onClick,
  href,
  download,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  href?: string;
  download?: string;
}) {
  const cls =
    "inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-primary px-4 font-sans text-sm font-semibold text-bg hover:opacity-90";
  if (href) {
    return (
      <a className={cls} href={href} download={download}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" onClick={onClick} className={cls}>
      {children}
    </button>
  );
}
