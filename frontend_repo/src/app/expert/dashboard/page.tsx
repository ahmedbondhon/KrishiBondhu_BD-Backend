"use client";
import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CheckCircle2, Inbox, Timer } from "lucide-react";
import { ChartCard, Donut, HBars, TrendChart } from "@/components/charts";
import { Stat } from "@/components/stat";
import { ConfidenceBadge, LinkButton, Skeleton, UrgencyBadge } from "@/components/ui";
import { listCases } from "@/lib/api";
import { CROP_COLOR, cropMix, dailyCounts } from "@/lib/analytics";
import { CROPS } from "@/lib/data";
import { timeAgo } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

export default function ExpertDashboard() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user)!;
  const { data, isLoading } = useQuery({ queryKey: ["cases", "expert"], queryFn: () => listCases("expert") });

  const m = useMemo(() => {
    const all = data ?? [];
    const pending = all.filter((c) => c.status === "needs_expert_review");
    const mine = all.filter((c) => c.status === "under_review");
    const done = all.filter((c) => c.expert_reply);
    const urgent = [...pending, ...mine].filter((c) => c.diagnosis.urgency === "high" || c.diagnosis.confidence_level === "low");
    const dec = (k: string) => done.filter((c) => c.expert_reply!.decision === k).length;
    return { all, pending, mine, done, urgent, daily: dailyCounts(all, 14), mix: cropMix(all), dec: { a: dec("approved_ai"), c: dec("corrected_ai"), r: dec("rejected_ai") } };
  }, [data]);

  if (isLoading || !data) return <div className="space-y-4"><Skeleton className="!h-10 w-64" /><div className="grid gap-4 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="!h-28 !rounded-card" />)}</div></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><p className="text-ink-soft">{L("স্বাগতম", "Welcome")}</p><h1 className="text-[1.75rem] md:text-[2.1rem]">{user.name}</h1></div>
        <LinkButton href="/expert/cases" size="md"><Inbox size={19} />{L("কেস তালিকা খুলুন", "Open case queue")}</LinkButton>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label={L("নতুন কেস", "New cases")} value={m.pending.length} icon={<Inbox size={18} />} tone="sun" hint={L("এখনো কেউ নেয়নি", "Not yet picked up")} />
        <Stat label={L("পর্যালোচনায়", "In review")} value={m.mine.length} icon={<Timer size={18} />} tone="sky" />
        <Stat label={L("জরুরি / অনিশ্চিত", "Urgent / uncertain")} value={m.urgent.length} icon={<AlertTriangle size={18} />} tone="clay" hint={L("আগে দেখুন", "Review first")} />
        <Stat label={L("উত্তর দেওয়া", "Answered")} value={m.done.length} icon={<CheckCircle2 size={18} />} spark={m.daily.map((d) => d.value)} />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-line p-5"><h2 className="text-[1.1rem]">{L("আগে দেখুন", "Needs your attention")}</h2><Link href="/expert/cases" className="inline-flex items-center gap-1 text-[14.5px] font-semibold text-brand-700 hover:underline">{L("সব কেস", "All cases")}<ArrowRight size={15} /></Link></div>
          {m.urgent.length === 0 ? <p className="p-6 text-ink-soft">{L("এখন কোনো জরুরি কেস নেই।", "No urgent cases right now.")}</p> : (
            <ul className="divide-y divide-line">{m.urgent.map((c) => (
              <li key={c.id}><Link href={`/expert/cases/${c.id}`} className="flex items-center gap-3.5 p-4 transition hover:bg-canvas">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.image_url} alt="" className="h-14 w-14 shrink-0 rounded-xl object-cover" />
                <div className="min-w-0 flex-1"><p className="truncate font-display font-bold">{c.crop.emoji} {c.diagnosis.issue?.name_bn ?? L("শনাক্ত হয়নি", "Not identified")}</p><p className="text-[13.5px] text-ink-mute">{c.farmer_name} · {c.district} · {timeAgo(c.created_at, lang)}</p></div>
                <div className="hidden flex-col items-end gap-1 sm:flex"><UrgencyBadge urgency={c.diagnosis.urgency} /><ConfidenceBadge level={c.diagnosis.confidence_level} /></div>
              </Link></li>
            ))}</ul>
          )}
        </section>

        <div className="space-y-5">
          <ChartCard title={L("আপনার সিদ্ধান্ত", "Your decisions")} table={{ head: [L("সিদ্ধান্ত", "Decision"), L("সংখ্যা", "Count")], rows: [[L("সঠিক", "Approved"), m.dec.a], [L("সংশোধন", "Corrected"), m.dec.c], [L("বাতিল", "Rejected"), m.dec.r]] }}>
            <Donut center={m.done.length} centerLabel={L("পর্যালোচিত", "Reviewed")} parts={[{ label: L("সিস্টেম সঠিক", "AI approved"), value: m.dec.a, color: "#1F9D5C" }, { label: L("সংশোধিত", "Corrected"), value: m.dec.c, color: "#D99A00" }, { label: L("বাতিল", "Rejected"), value: m.dec.r, color: "#D9472F" }]} />
          </ChartCard>
          <ChartCard title={L("ফসল অনুযায়ী কেস", "Cases by crop")} table={{ head: [L("ফসল", "Crop"), L("কেস", "Cases")], rows: m.mix.map((x) => { const c = CROPS.find((k) => k.code === x.code)!; return [L(c.name_bn, c.name_en), x.value]; }) }}>
            <HBars rows={m.mix.map((x) => { const c = CROPS.find((k) => k.code === x.code)!; return { label: L(c.name_bn, c.name_en), value: x.value, color: CROP_COLOR[x.code], icon: c.emoji }; })} />
          </ChartCard>
        </div>
      </div>

      <ChartCard title={L("আসা কেস — গত ১৪ দিন", "Incoming cases — last 14 days")} table={{ head: [L("তারিখ", "Date"), L("কেস", "Cases")], rows: m.daily.map((d) => [d.date, d.value]) }}>
        <TrendChart data={m.daily} unit={L("কেস", "cases")} />
      </ChartCard>
    </div>
  );
}
