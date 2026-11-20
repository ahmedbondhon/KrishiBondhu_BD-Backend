"use client";
import Link from "next/link";
import { ButtonHTMLAttributes, ReactNode, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, CircleHelp, Clock, Loader2, Sprout, Volume2, VolumeX, WifiOff, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { speakBn, stopSpeech } from "@/lib/speech";
import { useApp, useL } from "@/store/app";
import type { CaseStatus, Level, Urgency } from "@/types";

/* ------------------------------ brand ------------------------------ */

export function Logo({ light = false, size = 36, className }: { light?: boolean; size?: number; className?: string }) {
  const L = useL();
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span className="grid place-items-center rounded-[11px] bg-canopy text-lime-400 ring-1 ring-white/10" style={{ width: size, height: size }}>
        <Sprout size={size * 0.58} strokeWidth={2.3} />
      </span>
      <span>
        <span className={cn("block font-display text-[19px] font-extrabold leading-[1.3]", light ? "text-white" : "text-ink")}>{L("কৃষিবন্ধু", "KrishiBondhu")}</span>
        <span className={cn("block text-[12px] leading-tight", light ? "text-brand-200" : "text-ink-mute")}>{L("বাংলাদেশ", "Bangladesh")}</span>
      </span>
    </span>
  );
}

/* ----------------------------- buttons ----------------------------- */

type Variant = "primary" | "secondary" | "soft" | "ghost" | "danger" | "dark" | "accent";
type Size = "sm" | "md" | "lg";
const variants: Record<Variant, string> = {
  primary: "bg-brand-600 text-white shadow-cta hover:bg-brand-700 active:translate-y-px",
  secondary: "bg-white text-ink ring-1 ring-inset ring-line-strong hover:bg-brand-50",
  soft: "bg-brand-50 text-brand-700 hover:bg-brand-100",
  ghost: "text-ink-soft hover:bg-brand-50",
  danger: "bg-clay-500 text-white hover:bg-clay-600",
  dark: "bg-canopy text-white hover:bg-canopy-2",
  accent: "bg-lime-400 text-canopy hover:bg-lime-300 shadow-[0_8px_20px_-8px_rgba(196,233,75,.7)]",
};
const sizes: Record<Size, string> = { sm: "min-h-[38px] px-3.5 text-[14.5px]", md: "min-h-[46px] px-5 text-[16px]", lg: "min-h-[56px] px-7 text-[17.5px]" };
const base = "inline-flex items-center justify-center gap-2 rounded-ctl font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

export function Button({ variant = "primary", size = "md", loading, className, children, ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size; loading?: boolean }) {
  return (
    <button {...p} disabled={p.disabled || loading} className={cn(base, variants[variant], sizes[size], className)}>
      {loading && <Loader2 className="animate-spin" size={18} />}
      {children}
    </button>
  );
}

export function LinkButton({ href, variant = "primary", size = "md", className, children }: { href: string; variant?: Variant; size?: Size; className?: string; children: ReactNode }) {
  return <Link href={href} className={cn(base, variants[variant], sizes[size], className)}>{children}</Link>;
}

/* ------------------------------ badges ------------------------------ */

type Tone = "brand" | "sun" | "clay" | "sky" | "neutral" | "dark";
const tones: Record<Tone, string> = {
  brand: "bg-brand-50 text-brand-700 ring-brand-200",
  sun: "bg-sun-50 text-sun-700 ring-sun-100",
  clay: "bg-clay-50 text-clay-700 ring-clay-100",
  sky: "bg-sky-50 text-sky-700 ring-sky-100",
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
  dark: "bg-white/10 text-white ring-white/15",
};
export function Badge({ tone = "neutral", icon, children, className }: { tone?: Tone; icon?: ReactNode; children: ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[13.5px] font-semibold ring-1 ring-inset", tones[tone], className)}>{icon}{children}</span>;
}

/* Status chips combine icon + word + colour so colour is never the only signal */
export function ConfidenceBadge({ level, score }: { level: Level; score?: number }) {
  const L = useL();
  const m = {
    high: { tone: "brand" as Tone, icon: <CheckCircle2 size={14} />, t: L("উচ্চ নিশ্চয়তা", "High confidence") },
    medium: { tone: "sun" as Tone, icon: <CircleHelp size={14} />, t: L("মাঝারি নিশ্চয়তা", "Medium confidence") },
    low: { tone: "clay" as Tone, icon: <AlertTriangle size={14} />, t: L("কম নিশ্চয়তা", "Low confidence") },
  }[level];
  return <Badge tone={m.tone} icon={m.icon}>{m.t}{score !== undefined && <span className="opacity-70">· {Math.round(score * 100)}%</span>}</Badge>;
}

export function UrgencyBadge({ urgency }: { urgency: Urgency }) {
  const L = useL();
  const m = {
    low: { tone: "brand" as Tone, icon: <CheckCircle2 size={14} />, t: L("জরুরি নয়", "Not urgent") },
    medium: { tone: "sun" as Tone, icon: <Clock size={14} />, t: L("২৪ ঘণ্টায় দেখুন", "Check within 24h") },
    high: { tone: "clay" as Tone, icon: <AlertTriangle size={14} />, t: L("এখনই ব্যবস্থা নিন", "Act now") },
    unknown: { tone: "neutral" as Tone, icon: <CircleHelp size={14} />, t: L("অনিশ্চিত", "Unknown") },
  }[urgency];
  return <Badge tone={m.tone} icon={m.icon}>{m.t}</Badge>;
}

export function StatusBadge({ status }: { status: CaseStatus }) {
  const L = useL();
  const m: Record<CaseStatus, [string, Tone]> = {
    draft: [L("খসড়া", "Draft"), "neutral"],
    diagnosed: [L("ফলাফল প্রস্তুত", "Result ready"), "brand"],
    needs_expert_review: [L("বিশেষজ্ঞের অপেক্ষায়", "Awaiting expert"), "sun"],
    under_review: [L("পর্যালোচনায়", "In review"), "sky"],
    response_received: [L("উত্তর এসেছে", "Reply received"), "brand"],
    closed: [L("বন্ধ", "Closed"), "neutral"],
  };
  return <Badge tone={m[status][1]}>{m[status][0]}</Badge>;
}

/* ------------------------------ layout bits ------------------------------ */

export function PageHeader({ title, sub, actions }: { title: ReactNode; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-[1.65rem] md:text-[2rem]">{title}</h1>
        {sub && <p className="mt-1 max-w-2xl text-ink-soft">{sub}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-brand-700" role="status">
      <Loader2 className="animate-spin" size={24} />
      {label && <span>{label}</span>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-5", className)} aria-hidden />;
}

export function EmptyState({ icon, title, body, action }: { icon: ReactNode; title: string; body: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-600">{icon}</div>
      <h3 className="text-xl">{title}</h3>
      <p className="max-w-sm text-ink-soft">{body}</p>
      {action}
    </div>
  );
}

export function LangToggle({ dark = false, className }: { dark?: boolean; className?: string }) {
  const lang = useApp((s) => s.lang);
  const setLang = useApp((s) => s.setLang);
  const seg = (v: "bn" | "en", text: string) => (
    <button
      onClick={() => setLang(v)}
      aria-pressed={lang === v}
      className={cn("min-w-[40px] rounded-full px-2.5 py-1 text-[13.5px] font-semibold transition", lang === v ? (dark ? "bg-white text-canopy" : "bg-canopy text-white") : dark ? "text-white/70 hover:text-white" : "text-ink-soft hover:text-ink")}
    >
      {text}
    </button>
  );
  return <div role="group" aria-label="Language" className={cn("inline-flex rounded-full p-0.5 ring-1 ring-inset", dark ? "ring-white/25" : "bg-white ring-line-strong", className)}>{seg("bn", "বাং")}{seg("en", "EN")}</div>;
}

export function Segmented<T extends string>({ value, onChange, options, label }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; label: string }) {
  return (
    <div role="tablist" aria-label={label} className="inline-flex flex-wrap gap-1 rounded-ctl bg-white p-1 ring-1 ring-inset ring-line-strong">
      {options.map((o) => (
        <button key={o.value} role="tab" aria-selected={value === o.value} onClick={() => onChange(o.value)} className={cn("min-h-[36px] rounded-lg px-3.5 text-[14.5px] font-semibold transition", value === o.value ? "bg-canopy text-white" : "text-ink-soft hover:bg-brand-50")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Avatar({ name, size = 36, dark }: { name: string; size?: number; dark?: boolean }) {
  return (
    <span className={cn("grid shrink-0 place-items-center rounded-full font-display font-bold", dark ? "bg-lime-400 text-canopy" : "bg-brand-100 text-brand-800")} style={{ width: size, height: size, fontSize: size * 0.42 }}>
      {Array.from(name.trim())[0] ?? "?"}
    </span>
  );
}

export function Drawer({ open, onClose, title, children, footer }: { open: boolean; onClose: () => void; title: string; children: ReactNode; footer?: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const L = useL();
  useEffect(() => {
    if (!open) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    ref.current?.focus();
    return () => window.removeEventListener("keydown", k);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-canopy/50 backdrop-blur-[2px]" onClick={onClose}>
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()} className="flex h-full w-full max-w-xl animate-rise flex-col bg-white shadow-pop outline-none">
        <div className="flex items-start justify-between gap-3 border-b border-line p-5">
          <h2 className="text-xl">{title}</h2>
          <button onClick={onClose} className="grid h-9 w-9 shrink-0 place-items-center rounded-full hover:bg-brand-50" aria-label={L("বন্ধ করুন", "Close")}><X size={20} /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
        {footer && <div className="border-t border-line p-4">{footer}</div>}
      </div>
    </div>
  );
}

/* ------------------------------ behaviour ------------------------------ */

export function AudioButton({ text, className, variant = "dark" }: { text: string; className?: string; variant?: Variant }) {
  const L = useL();
  const [on, setOn] = useState(false);
  const [unsupported, setUnsupported] = useState(false);
  useEffect(() => () => void stopSpeech(), []);
  return (
    <div className={className}>
      <Button
        variant={variant}
        size="lg"
        aria-pressed={on}
        onClick={() => {
          if (on) { stopSpeech(); setOn(false); return; }
          const ok = speakBn(text, () => setOn(false));
          setUnsupported(!ok);
          setOn(ok);
        }}
      >
        {on ? <VolumeX size={22} /> : <Volume2 size={22} />}
        {on ? L("থামান", "Stop") : L("বাংলায় শুনুন", "Listen in Bangla")}
      </Button>
      {unsupported && <p className="hint text-clay-600">{L("এই ব্রাউজারে ভয়েস চলছে না। Chrome ব্যবহার করে দেখুন।", "Voice is not supported in this browser. Try Chrome.")}</p>}
    </div>
  );
}

export function OfflineBanner() {
  const L = useL();
  const [off, setOff] = useState(false);
  useEffect(() => {
    const u = () => setOff(!navigator.onLine);
    u();
    window.addEventListener("online", u);
    window.addEventListener("offline", u);
    return () => { window.removeEventListener("online", u); window.removeEventListener("offline", u); };
  }, []);
  if (!off) return null;
  return (
    <div role="status" className="flex items-center gap-2 bg-sun-500 px-4 py-2 text-[14.5px] font-semibold text-canopy">
      <WifiOff size={18} />
      {L("ইন্টারনেট নেই। আপনার তথ্য সংরক্ষিত আছে, সংযোগ ফিরলে পাঠানো যাবে।", "You are offline. Your data is saved and can be sent when you reconnect.")}
    </div>
  );
}

/** Animated leaf with a scanning line — the signature visual of the diagnosis flow. */
export function LeafScan({ className, caption }: { className?: string; caption?: string }) {
  return (
    <div className={cn("relative mx-auto aspect-square w-full max-w-[320px]", className)}>
      <span className="absolute inset-4 rounded-full border border-lime-400/50 animate-ring" />
      <span className="absolute inset-4 rounded-full border border-lime-400/30 animate-ring [animation-delay:1.3s]" />
      <div className="absolute inset-9 overflow-hidden rounded-[28px] bg-canopy-2 ring-1 ring-white/15">
        <svg viewBox="0 0 200 200" className="h-full w-full" aria-hidden>
          <path d="M100 18C162 52 172 138 100 186 28 138 38 52 100 18Z" fill="#40B476" />
          <path d="M100 28V180M100 62l-30 28M100 82l34 22M100 112l-28 26" stroke="#136540" strokeWidth="2" fill="none" />
          {[[78, 72], [124, 98], [86, 130], [112, 152]].map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r={8 - i * 0.8} fill="#6b3a1d" opacity=".85" />
              <circle cx={x} cy={y} r={14 - i} fill="none" stroke="#C4E94B" strokeWidth="1.6" strokeDasharray="3 3" />
            </g>
          ))}
        </svg>
        <span className="absolute inset-x-0 h-0.5 animate-scan bg-lime-300 shadow-[0_0_18px_6px_rgba(196,233,75,.55)]" />
      </div>
      {caption && <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-white px-3.5 py-1 text-[13.5px] font-semibold text-canopy shadow-pop">{caption}</span>}
    </div>
  );
}
