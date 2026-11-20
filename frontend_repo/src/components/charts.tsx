"use client";
import { ReactNode, useEffect, useId, useRef, useState } from "react";
import { Table2, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

/** Card wrapper that offers a table view of every chart (accessibility + the aqua contrast relief rule). */
export function ChartCard({ title, sub, children, table, className, action }: { title: string; sub?: string; children: ReactNode; table?: { head: string[]; rows: (string | number)[][] }; className?: string; action?: ReactNode }) {
  const L = useL();
  const [asTable, setAsTable] = useState(false);
  return (
    <section className={cn("card p-5", className)}>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0"><h2 className="text-[1.1rem]">{title}</h2>{sub && <p className="text-[14px] text-ink-mute">{sub}</p>}</div>
        <div className="flex items-center gap-1">
          {action}
          {table && (
            <button onClick={() => setAsTable(!asTable)} className="grid h-9 w-9 place-items-center rounded-ctl text-ink-mute hover:bg-brand-50 hover:text-ink" aria-label={asTable ? L("চার্ট দেখুন", "Show chart") : L("টেবিল দেখুন", "Show as table")} aria-pressed={asTable}>
              {asTable ? <BarChart3 size={18} /> : <Table2 size={18} />}
            </button>
          )}
        </div>
      </div>
      {asTable && table ? (
        <div className="overflow-x-auto">
          <table className="w-full text-[14.5px]"><thead><tr>{table.head.map((h) => <th key={h} className="th !px-2">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-line">{table.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="px-2 py-2">{c}</td>)}</tr>)}</tbody></table>
        </div>
      ) : children}
    </section>
  );
}

/* ---------------------------- sparkline ---------------------------- */
export function Sparkline({ data, color = "#1F9D5C", width = 96, height = 32 }: { data: number[]; color?: string; width?: number; height?: number }) {
  const id = useId();
  const max = Math.max(1, ...data);
  const step = width / Math.max(1, data.length - 1);
  const pts = data.map((v, i) => [i * step, height - 3 - (v / max) * (height - 8)] as const);
  const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const last = pts[pts.length - 1];
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden>
      <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor={color} stopOpacity=".22" /><stop offset="1" stopColor={color} stopOpacity="0" /></linearGradient></defs>
      <path d={`${d} L${width},${height} L0,${height} Z`} fill={`url(#${id})`} />
      <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {last && <circle cx={last[0]} cy={last[1]} r="3" fill={color} stroke="#fff" strokeWidth="2" />}
    </svg>
  );
}

/* ---------------------------- trend (area + crosshair) ---------------------------- */
export function TrendChart({ data, color = "#1F9D5C", unit }: { data: { label: Date; value: number }[]; color?: string; unit: string }) {
  const id = useId();
  const lang = useApp((s) => s.lang);
  const [hover, setHover] = useState<number | null>(null);
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(640);
  // Render at the real pixel width so text stays crisp and the height stays sensible on every screen
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const set = () => setW(Math.max(260, Math.round(el.clientWidth || 640)));
    set();
    const ro = new ResizeObserver(set);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const H = W < 480 ? 172 : 212;
  const P = { l: 28, r: 10, t: 12, b: 26 };
  const max = Math.max(3, ...data.map((d) => d.value));
  const top = Math.ceil(max / 2) * 2;
  const x = (i: number) => P.l + (i * (W - P.l - P.r)) / Math.max(1, data.length - 1);
  const y = (v: number) => P.t + (1 - v / top) * (H - P.t - P.b);
  const line = data.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(" ");
  const fmt = (d: Date, long = false) => d.toLocaleDateString(lang === "bn" ? "bn-BD" : "en-GB", long ? { day: "numeric", month: "long" } : { day: "numeric", month: "short" });
  const every = Math.ceil(data.length / Math.max(2, Math.floor(W / 96)));
  const h = hover !== null ? data[hover] : null;
  return (
    <div ref={box} className="relative">
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="block touch-pan-y" role="img" aria-label={unit}
        onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); const px = ((e.clientX - r.left) / r.width) * W; setHover(Math.max(0, Math.min(data.length - 1, Math.round(((px - P.l) / (W - P.l - P.r)) * (data.length - 1))))); }}
        onPointerLeave={() => setHover(null)}>
        <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor={color} stopOpacity=".2" /><stop offset="1" stopColor={color} stopOpacity="0" /></linearGradient></defs>
        {[0, top / 2, top].map((t) => (<g key={t}><line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#E1E8E3" strokeWidth="1" /><text x={P.l - 6} y={y(t) + 4} textAnchor="end" fontSize="11.5" fill="#66776E">{t}</text></g>))}
        <path d={`${line} L${x(data.length - 1)},${y(0)} L${x(0)},${y(0)} Z`} fill={`url(#${id})`} />
        <path d={line} fill="none" stroke={color} strokeWidth="2.25" strokeLinejoin="round" strokeLinecap="round" />
        {data.map((d, i) => (data.length - 1 - i) % every === 0 && <text key={i} x={x(i)} y={H - 7} textAnchor={i === data.length - 1 ? "end" : i === 0 ? "start" : "middle"} fontSize="11.5" fill="#66776E">{fmt(d.label)}</text>)}
        {hover !== null && (<g><line x1={x(hover)} x2={x(hover)} y1={P.t} y2={y(0)} stroke="#0E1F18" strokeOpacity=".25" strokeDasharray="3 3" /><circle cx={x(hover)} cy={y(data[hover].value)} r="5" fill={color} stroke="#fff" strokeWidth="2" /></g>)}
      </svg>
      {h && hover !== null && (
        <div className="pointer-events-none absolute top-0 rounded-ctl bg-canopy px-3 py-1.5 text-[13.5px] text-white shadow-pop" style={{ left: x(hover), transform: `translateX(${hover > data.length * 0.65 ? "calc(-100% - 10px)" : "10px"})` }}>
          <span className="block text-white/70">{fmt(h.label, true)}</span><span className="font-bold">{h.value} {unit}</span>
        </div>
      )}
    </div>
  );
}

/* ---------------------------- donut ---------------------------- */
export function Donut({ parts, center, centerLabel }: { parts: { label: string; value: number; color: string; icon?: string }[]; center: string | number; centerLabel: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const total = parts.reduce((s, p) => s + p.value, 0) || 1;
  const R = 52, C = 2 * Math.PI * R;
  let acc = 0;
  return (
    <div className="flex flex-wrap items-center gap-6">
      <div className="relative h-[150px] w-[150px] shrink-0">
        <svg viewBox="0 0 140 140" className="-rotate-90" role="img" aria-label={centerLabel}>
          <circle cx="70" cy="70" r={R} fill="none" stroke="#EEF3EF" strokeWidth="16" />
          {parts.map((p, i) => {
            const len = (p.value / total) * C;
            const gap = parts.filter((q) => q.value > 0).length > 1 ? 2.5 : 0; // 2px surface gap between segments
            const el = <circle key={p.label} cx="70" cy="70" r={R} fill="none" stroke={p.color} strokeWidth={hover === i ? 19 : 16} strokeDasharray={`${Math.max(0, len - gap)} ${C}`} strokeDashoffset={-acc} strokeLinecap="butt" onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)} style={{ transition: "stroke-width .15s" }} />;
            acc += len;
            return el;
          })}
        </svg>
        <div className="absolute inset-0 grid place-content-center text-center">
          <span className="font-display text-3xl font-extrabold leading-none">{hover !== null ? parts[hover].value : center}</span>
          <span className="mt-1 text-[12.5px] text-ink-mute">{hover !== null ? parts[hover].label : centerLabel}</span>
        </div>
      </div>
      <ul className="min-w-[160px] flex-1 space-y-2">
        {parts.map((p, i) => (
          <li key={p.label} onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)} className="flex items-center gap-2.5 text-[15px]">
            <span className="h-3 w-3 shrink-0 rounded-[4px]" style={{ background: p.color }} aria-hidden />
            <span className="flex-1">{p.icon} {p.label}</span>
            <span className="font-bold tabular-nums">{p.value}</span>
            <span className="w-10 text-right text-[13.5px] tabular-nums text-ink-mute">{Math.round((p.value / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------------------------- horizontal bars ---------------------------- */
export function HBars({ rows }: { rows: { label: string; value: number; color: string; icon?: string }[] }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <ul className="space-y-3">
      {rows.map((r) => (
        <li key={r.label}>
          <div className="mb-1 flex items-baseline justify-between gap-3 text-[15px]"><span className="truncate">{r.icon} {r.label}</span><span className="font-bold tabular-nums">{r.value}</span></div>
          <div className="h-2.5 rounded-full bg-[#EEF3EF]"><div className="h-full rounded-r-full rounded-l-sm" style={{ width: `${(r.value / max) * 100}%`, background: r.color }} /></div>
        </li>
      ))}
    </ul>
  );
}

/* ---------------------------- confidence gauge ---------------------------- */
export function Gauge({ score, level }: { score: number; level: "high" | "medium" | "low" }) {
  const color = level === "high" ? "#1F9D5C" : level === "medium" ? "#D99A00" : "#D9472F";
  const R = 56, arc = Math.PI * R;
  return (
    <div className="relative mx-auto w-[168px]" role="meter" aria-valuenow={Math.round(score * 100)} aria-valuemin={0} aria-valuemax={100}>
      <svg viewBox="0 0 140 80" className="w-full" aria-hidden>
        <path d="M14 70A56 56 0 0 1 126 70" fill="none" stroke="#EEF3EF" strokeWidth="13" strokeLinecap="round" />
        <path d="M14 70A56 56 0 0 1 126 70" fill="none" stroke={color} strokeWidth="13" strokeLinecap="round" strokeDasharray={`${arc * score} ${arc}`} style={{ transition: "stroke-dasharray .9s cubic-bezier(.2,.8,.2,1)" }} />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center"><span className="font-display text-[2rem] font-extrabold leading-none">{Math.round(score * 100)}<span className="text-lg">%</span></span></div>
    </div>
  );
}
