"use client";
import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, ArrowRight, Bell, Camera, CheckCircle2, ClipboardList, Cloud, Hourglass, Lock, MapPin, Stethoscope, Store } from "lucide-react";
import { CaseRow } from "@/components/case-row";
import { ChartCard, Donut, TrendChart } from "@/components/charts";
import { Stat } from "@/components/stat";
import { Badge, LinkButton, Skeleton } from "@/components/ui";
import { listCases, listFarms, listNotifications } from "@/lib/api";
import { avgConfidence, CROP_COLOR, cropMix, dailyCounts } from "@/lib/analytics";
import { CROPS } from "@/lib/data";
import { flags } from "@/lib/flags";
import { toBn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

export default function Dashboard() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user)!;
  const { data: cases, isLoading } = useQuery({ queryKey: ["cases", "mine", user.name], queryFn: () => listCases("mine", user.name) });
  const { data: notes } = useQuery({ queryKey: ["notifications"], queryFn: listNotifications });
  const { data: farms } = useQuery({ queryKey: ["farms"], queryFn: listFarms });
  const reply = notes?.find((n) => !n.read && n.case_id);
  const n = (x: number | string) => (lang === "bn" ? toBn(x) : x);

  const m = useMemo(() => {
    const all = cases ?? [];
    const daily = dailyCounts(all, 14);
    return {
      all, daily,
      waiting: all.filter((c) => c.status === "needs_expert_review" || c.status === "under_review").length,
      replied: all.filter((c) => c.status === "response_received").length,
      avg: Math.round(avgConfidence(all) * 100),
      mix: cropMix(all),
    };
  }, [cases]);

  const h = new Date().getHours();
  const greet = h < 12 ? L("শুভ সকাল", "Good morning") : h < 17 ? L("শুভ অপরাহ্ন", "Good afternoon") : L("শুভ সন্ধ্যা", "Good evening");

  return (
    <div className="space-y-6">
      <div><p className="text-ink-soft">{greet}</p><h1 className="text-[1.75rem] md:text-[2.1rem]">{user.name}</h1></div>

      {reply && (
        <Link href={`/farmer/cases/${reply.case_id}`} className="flex items-center gap-3 rounded-card bg-sky-50 p-4 text-sky-700 ring-1 ring-inset ring-sky-100 transition hover:bg-sky-100">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-sky-500 text-white"><Bell size={19} /></span>
          <span className="min-w-0 flex-1"><span className="block font-display font-bold">{reply.title_bn}</span><span className="block truncate text-[15px]">{reply.body_bn}</span></span>
          <ArrowRight size={18} className="shrink-0" />
        </Link>
      )}

      {/* Primary action */}
      <section className="rows-texture relative overflow-hidden rounded-sheet bg-canopy p-6 text-white md:p-8">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/25 blur-3xl" aria-hidden />
        <div className="relative grid items-center gap-6 md:grid-cols-[1fr_auto]">
          <div>
            <h2 className="text-[1.6rem] leading-tight md:text-[2.1rem]">{L("ফসলে কিছু অস্বাভাবিক দেখছেন?", "Seeing something odd on your crop?")}</h2>
            <p className="mt-1.5 max-w-lg text-brand-100">{L("একটি ছবি তুলুন। বাংলায় সহজ পরামর্শ পাবেন, দরকার হলে বিশেষজ্ঞও দেখবেন।", "Take one photo. Get simple Bangla advice, with an expert if needed.")}</p>
            <div className="mt-5 flex flex-wrap items-center gap-2.5">
              <LinkButton href="/farmer/diagnose" variant="accent" size="lg"><Camera size={22} />{L("ছবি তুলে পরীক্ষা করুন", "Check with a photo")}</LinkButton>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {CROPS.map((c) => <Link key={c.id} href={`/farmer/diagnose?crop=${c.code}`} className="inline-flex min-h-[38px] items-center gap-1.5 rounded-full bg-white/10 px-3.5 text-[14.5px] font-semibold text-white ring-1 ring-inset ring-white/15 hover:bg-white/20">{c.emoji} {L(c.name_bn, c.name_en)}</Link>)}
            </div>
          </div>
          <div className="hidden h-36 w-36 place-items-center rounded-full bg-white/8 ring-1 ring-white/15 md:grid"><Camera size={54} className="text-lime-400" strokeWidth={1.6} /></div>
        </div>
      </section>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label={L("মোট পরীক্ষা", "Total checks")} value={n(m.all.length)} icon={<ClipboardList size={18} />} spark={m.daily.map((d) => d.value)} hint={L("গত ১৪ দিন", "Last 14 days")} />
        <Stat label={L("বিশেষজ্ঞের অপেক্ষায়", "Awaiting expert")} value={n(m.waiting)} icon={<Hourglass size={18} />} tone="sun" />
        <Stat label={L("বিশেষজ্ঞ উত্তর দিয়েছেন", "Expert replies")} value={n(m.replied)} icon={<Stethoscope size={18} />} tone="sky" />
        <Stat label={L("গড় নিশ্চয়তা", "Avg. confidence")} value={`${n(m.avg)}%`} icon={<Activity size={18} />} />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
        <section>
          <div className="mb-3 flex items-center justify-between"><h2 className="text-xl">{L("সাম্প্রতিক পরীক্ষা", "Recent checks")}</h2><Link href="/farmer/cases" className="inline-flex items-center gap-1 font-semibold text-brand-700 hover:underline">{L("সব দেখুন", "See all")}<ArrowRight size={16} /></Link></div>
          {isLoading ? <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="!h-[96px] !rounded-card" />)}</div> : m.all.length ? (
            <div className="space-y-3">{m.all.slice(0, 4).map((c) => <CaseRow key={c.id} c={c} href={`/farmer/cases/${c.id}`} />)}</div>
          ) : <div className="card p-8 text-center text-ink-soft">{L("এখনো কোনো পরীক্ষা নেই। উপরের বোতামে চাপ দিয়ে শুরু করুন।", "No checks yet. Tap the button above to start.")}</div>}
        </section>

        <div className="space-y-5">
          <ChartCard title={L("কোন ফসলে কত পরীক্ষা", "Checks by crop")} table={{ head: [L("ফসল", "Crop"), L("সংখ্যা", "Count")], rows: m.mix.map((x) => [L(CROPS.find((c) => c.code === x.code)!.name_bn, CROPS.find((c) => c.code === x.code)!.name_en), x.value]) }}>
            <Donut center={m.all.length} centerLabel={L("মোট", "Total")} parts={m.mix.map((x) => { const c = CROPS.find((k) => k.code === x.code)!; return { label: L(c.name_bn, c.name_en), value: x.value, color: CROP_COLOR[x.code], icon: c.emoji }; })} />
          </ChartCard>
          <section className="card p-5">
            <h2 className="mb-3 flex items-center gap-2 text-[1.1rem]"><MapPin size={18} className="text-brand-600" />{L("আমার ক্ষেত", "My fields")}</h2>
            {farms?.[0] ? (
              <ul className="space-y-2">{farms[0].crops.map((cc, i) => <li key={i} className="flex items-center gap-3 rounded-xl bg-canvas p-3"><span className="text-2xl">{cc.crop.emoji}</span><span className="flex-1 leading-tight"><span className="block font-semibold">{L(cc.crop.name_bn, cc.crop.name_en)}</span><span className="text-[13.5px] text-ink-mute">{farms[0].name}</span></span><Badge tone="brand">{cc.stage}</Badge></li>)}</ul>
            ) : <Skeleton className="!h-16" />}
          </section>
        </div>
      </div>

      <ChartCard title={L("গত ১৪ দিনে পরীক্ষা", "Checks over the last 14 days")} sub={L("আপনার সব ফসল মিলিয়ে", "Across all your crops")} table={{ head: [L("তারিখ", "Date"), L("পরীক্ষা", "Checks")], rows: m.daily.map((d) => [d.date, d.value]) }}>
        <TrendChart data={m.daily} unit={L("পরীক্ষা", "checks")} />
      </ChartCard>

      <section className="grid gap-3 sm:grid-cols-2">
        {[{ I: Cloud, bn: "আবহাওয়া ও বন্যা সতর্কতা", en: "Weather and flood alerts", on: flags.climate }, { I: Store, bn: "বাজারদর ও বিক্রির সুযোগ", en: "Market prices and selling", on: flags.market }].map(({ I, bn, en, on }) => (
          <Link key={bn} href="/farmer/more" className="card flex items-center gap-3 p-4"><span className="grid h-11 w-11 place-items-center rounded-xl bg-slate-100 text-slate-500"><I size={22} /></span><span className="flex-1 font-semibold">{L(bn, en)}</span>{!on ? <Badge tone="neutral" icon={<Lock size={12} />}>{L("শীঘ্রই", "Soon")}</Badge> : <CheckCircle2 className="text-brand-600" />}</Link>
        ))}
      </section>
    </div>
  );
}
