"use client";
import { ReactNode, useState } from "react";
import { AlertTriangle, Ban, CheckCircle2, Clock, Leaf, ShieldAlert, Stethoscope } from "lucide-react";
import { AudioButton, Badge, ConfidenceBadge, Segmented, StatusBadge, UrgencyBadge } from "./ui";
import { Gauge } from "./charts";
import { cn, fmtDate, toBn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { CaseStatus, DiagnosisCase, Level } from "@/types";

export function Meter({ score, level }: { score: number; level: Level }) {
  const color = level === "high" ? "bg-brand-500" : level === "medium" ? "bg-sun-500" : "bg-clay-500";
  return (
    <div role="meter" aria-valuenow={Math.round(score * 100)} aria-valuemin={0} aria-valuemax={100} className="h-2.5 w-full overflow-hidden rounded-full bg-[#EEF3EF]">
      <div className={cn("h-full rounded-full transition-all duration-700", color)} style={{ width: `${Math.round(score * 100)}%` }} />
    </div>
  );
}

/** Banner that leads the result when the situation needs attention. */
export function AttentionBanner({ c }: { c: DiagnosisCase }) {
  const L = useL();
  const d = c.diagnosis;
  if (!d.issue)
    return <Banner tone="sun" icon={<AlertTriangle size={22} />} title={L("সিস্টেম নিশ্চিত নয়", "The system is not sure")} body={L("এটি নিশ্চিত রোগনির্ণয় নয়। আরও কাছ থেকে নতুন ছবি দিন অথবা বিশেষজ্ঞের পরামর্শ নিন।", "This is not a confirmed diagnosis. Retake a closer photo or ask an expert.")} />;
  if (d.urgency === "high")
    return <Banner tone="clay" icon={<AlertTriangle size={22} />} title={L("এখনই ব্যবস্থা নিন", "Act today")} body={L("সমস্যাটি দ্রুত ছড়াতে পারে। নিচের ধাপগুলো আজই করুন।", "This can spread quickly. Do the steps below today.")} />;
  return null;
}
function Banner({ tone, icon, title, body }: { tone: "sun" | "clay"; icon: ReactNode; title: string; body: string }) {
  return (
    <div role="alert" className={cn("flex items-start gap-3 rounded-card p-4 ring-1 ring-inset", tone === "clay" ? "bg-clay-50 text-clay-700 ring-clay-100" : "bg-sun-50 text-sun-700 ring-sun-100")}>
      <span className="mt-0.5 shrink-0">{icon}</span><div><p className="font-display text-lg font-bold">{title}</p><p>{body}</p></div>
    </div>
  );
}

export function CaseHero({ c }: { c: DiagnosisCase }) {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const d = c.diagnosis;
  const unsure = !d.issue;
  const pct = (n: number) => (lang === "bn" ? toBn(Math.round(n * 100)) : Math.round(n * 100)) + "%";
  return (
    <section className="card overflow-hidden">
      <div className="grid md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="relative min-h-[220px]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={c.image_url} alt={L("ফসলের ছবি", "Crop photo")} className="absolute inset-0 h-full w-full object-cover" />
          <span className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1 text-[13.5px] font-semibold shadow-card">{c.crop.emoji} {L(c.crop.name_bn, c.crop.name_en)} · {c.growth_stage}</span>
        </div>
        <div className="space-y-4 p-5 md:p-6">
          <div>
            <p className="text-[14px] text-ink-mute">{unsure ? L("ফলাফল", "Result") : d.confidence_level === "high" ? L("সম্ভাব্য সমস্যা", "Likely problem") : L("সম্ভবত — এখনো নিশ্চিত নয়", "Possibly — not confirmed yet")}</p>
            <h2 className="text-[1.6rem] leading-tight md:text-[1.9rem]">{unsure ? L("নিশ্চিতভাবে শনাক্ত করা যায়নি", "Could not be identified") : d.issue!.name_bn}</h2>
            {!unsure && <p className="text-ink-mute">{d.issue!.name_en}</p>}
          </div>
          <div className="flex flex-wrap gap-2"><ConfidenceBadge level={d.confidence_level} /><UrgencyBadge urgency={d.urgency} /><StatusBadge status={c.status} /></div>
          <div className="grid items-center gap-4 rounded-xl bg-canvas p-4 sm:grid-cols-[170px_1fr]">
            <Gauge score={d.confidence_score} level={d.confidence_level} />
            <div>
              <p className="mb-2 text-[14px] font-semibold text-ink-soft">{L("সিস্টেম আর কী কী ভেবেছে", "What else the system considered")}</p>
              <ul className="space-y-1.5">{d.candidates.map((x, i) => (
                <li key={i} className="grid grid-cols-[1fr_auto] items-center gap-x-3 text-[14.5px]"><span className="truncate">{x.name_bn}</span><span className="font-bold tabular-nums">{pct(x.probability)}</span>
                  <span className="col-span-2 mt-0.5 h-1.5 rounded-full bg-white"><span className={cn("block h-full rounded-full", i === 0 ? "bg-brand-500" : "bg-brand-200")} style={{ width: `${x.probability * 100}%` }} /></span></li>
              ))}</ul>
            </div>
          </div>
          {!unsure && <p className="text-[15.5px] text-ink-soft"><span className="font-semibold text-ink">{L("লক্ষণ: ", "Signs: ")}</span>{d.issue!.symptoms_bn}</p>}
          <p className="text-[12.5px] text-ink-mute">{L("মডেল সংস্করণ", "Model version")} {d.model_version} · {fmtDate(c.created_at, lang)}</p>
        </div>
      </div>
    </section>
  );
}

export function AdvisoryPanel({ c }: { c: DiagnosisCase }) {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const a = c.advisory;
  const [tab, setTab] = useState<"do" | "dont" | "prevent">("do");
  if (!a) return null;
  const lists = { do: a.immediate_actions_bn, dont: a.prohibited_actions_bn, prevent: a.prevention_bn };
  const head = {
    do: { icon: <CheckCircle2 className="text-brand-600" />, t: L("আজ যা করবেন", "Do today"), ring: "border-l-brand-500" },
    dont: { icon: <Ban className="text-clay-500" />, t: L("যা করবেন না", "Do not"), ring: "border-l-clay-500" },
    prevent: { icon: <Leaf className="text-brand-600" />, t: L("পরে ঝুঁকি কমাতে", "Prevent it next time"), ring: "border-l-sky-500" },
  }[tab];
  return (
    <section className="space-y-4">
      <div className="rows-texture flex flex-wrap items-center justify-between gap-4 rounded-card bg-canopy p-5 text-white">
        <div className="min-w-0"><p className="font-display text-xl font-bold">{L("পরামর্শটি শুনুন", "Hear the advice")}</p><p className="text-brand-100">{L("মাঠে গিয়ে সহজে শোনার জন্য বাংলায়।", "In Bangla, easy to follow in the field.")}</p></div>
        <AudioButton text={a.audio_text_bn} variant="accent" />
      </div>
      <div className="card p-5">
        <Segmented<"do" | "dont" | "prevent"> label={L("পরামর্শের ধরন", "Advice type")} value={tab} onChange={setTab} options={[{ value: "do", label: L("করণীয়", "Do") }, { value: "dont", label: L("বর্জনীয়", "Avoid") }, { value: "prevent", label: L("প্রতিরোধ", "Prevent") }]} />
        <h3 className="mt-4 flex items-center gap-2 text-xl">{head.icon}{head.t}</h3>
        <ol className="mt-3 space-y-2.5">
          {lists[tab].map((t, i) => (
            <li key={i} className={cn("flex gap-3 rounded-xl border-l-4 bg-canvas p-3.5 text-[17px]", head.ring)}>
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white text-[13px] font-bold shadow-card">{lang === "bn" ? toBn(i + 1) : i + 1}</span>{t}
            </li>
          ))}
        </ol>
      </div>
      <div className="flex items-start gap-3 rounded-card bg-sun-50 p-4 text-sun-700 ring-1 ring-inset ring-sun-100"><ShieldAlert className="mt-1 shrink-0" size={22} /><p className="font-semibold">{a.safety_warning_bn}</p></div>
      <p className="px-1 text-[13.5px] text-ink-mute">{L(`পরামর্শটি ${a.reviewed_by} যাচাই করেছেন · ${fmtDate(a.reviewed_at, lang)}`, `Advice reviewed by an agricultural expert · ${fmtDate(a.reviewed_at, lang)}`)}</p>
    </section>
  );
}

export function StatusTimeline({ status }: { status: CaseStatus }) {
  const L = useL();
  const steps = [
    { k: "needs_expert_review", bn: "জমা হয়েছে", en: "Submitted" },
    { k: "under_review", bn: "পর্যালোচনা", en: "In review" },
    { k: "response_received", bn: "উত্তর এসেছে", en: "Replied" },
    { k: "closed", bn: "বন্ধ", en: "Closed" },
  ];
  const idx = Math.max(0, steps.findIndex((s) => s.k === status));
  return (
    <ol className="flex items-start" aria-label={L("কেসের অবস্থা", "Case progress")}>
      {steps.map((s, i) => (
        <li key={s.k} className="flex flex-1 flex-col items-center text-center" aria-current={i === idx ? "step" : undefined}>
          <div className="flex w-full items-center">
            <span className={cn("h-0.5 flex-1", i === 0 ? "invisible" : i <= idx ? "bg-brand-500" : "bg-line-strong")} />
            <span className={cn("grid h-7 w-7 place-items-center rounded-full text-white", i < idx ? "bg-brand-600" : i === idx ? "bg-brand-600 ring-4 ring-brand-100" : "bg-line-strong")}>{i < idx ? <CheckCircle2 size={16} /> : i === idx ? <Clock size={14} /> : null}</span>
            <span className={cn("h-0.5 flex-1", i === steps.length - 1 ? "invisible" : i < idx ? "bg-brand-500" : "bg-line-strong")} />
          </div>
          <span className={cn("mt-1.5 px-0.5 text-[12.5px] font-semibold leading-tight", i <= idx ? "text-brand-700" : "text-ink-mute")}>{L(s.bn, s.en)}</span>
        </li>
      ))}
    </ol>
  );
}

export function ExpertReplyCard({ c }: { c: DiagnosisCase }) {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const r = c.expert_reply;
  if (!r) return null;
  const dec = { approved_ai: ["সিস্টেমের ফলাফল সঠিক", "System result confirmed", "brand"], corrected_ai: ["বিশেষজ্ঞ সংশোধন করেছেন", "Expert corrected it", "sun"], rejected_ai: ["সিস্টেমের ফলাফল সঠিক নয়", "System result rejected", "clay"] }[r.decision] as [string, string, "brand" | "sun" | "clay"];
  return (
    <section className="card overflow-hidden">
      <div className="flex items-center gap-3 bg-sky-50 px-5 py-3.5"><span className="grid h-9 w-9 place-items-center rounded-full bg-sky-500 text-white"><Stethoscope size={18} /></span><div className="leading-tight"><p className="font-display font-bold text-sky-700">{L("বিশেষজ্ঞের উত্তর", "Expert reply")}</p><p className="text-[13.5px] text-ink-mute">{r.expert_name} · {fmtDate(r.created_at, lang)}</p></div></div>
      <div className="space-y-3 p-5">
        <Badge tone={dec[2]}>{L(dec[0], dec[1])}</Badge>
        {r.corrected_issue_bn && <p className="font-display text-lg font-bold">{r.corrected_issue_bn}</p>}
        <p className="text-[17px]">{r.response_bn}</p>
        <div className="flex flex-wrap items-center gap-2"><UrgencyBadge urgency={r.urgency} />{r.follow_up_date && <span className="text-[14px] text-ink-soft">{L("ফলোআপ: ", "Follow-up: ")}{fmtDate(r.follow_up_date, lang)}</span>}</div>
        <AudioButton text={r.response_bn} variant="soft" className="pt-1" />
      </div>
    </section>
  );
}
