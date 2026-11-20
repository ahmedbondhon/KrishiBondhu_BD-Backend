"use client";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, BadgeCheck, Camera, ThumbsUp } from "lucide-react";
import { ChartCard, Donut, HBars, TrendChart } from "@/components/charts";
import { Stat } from "@/components/stat";
import { Badge, PageHeader, Skeleton } from "@/components/ui";
import { listCases } from "@/lib/api";
import { avgConfidence, CROP_COLOR, confidenceMix, dailyCounts, topIssues } from "@/lib/analytics";
import { flags } from "@/lib/flags";
import { useL } from "@/store/app";

export default function AdminDashboard() {
  const L = useL();
  const { data, isLoading } = useQuery({ queryKey: ["cases", "expert"], queryFn: () => listCases("expert") });
  const m = useMemo(() => {
    const all = data ?? [];
    const reviewed = all.filter((c) => c.expert_reply);
    const agree = reviewed.filter((c) => c.expert_reply!.decision === "approved_ai").length;
    const fb = all.filter((c) => c.feedback);
    const dist = [...new Set(all.map((c) => c.district))].map((d) => ({ label: d, value: all.filter((c) => c.district === d).length })).sort((a, b) => b.value - a.value);
    return { all, reviewed, agree, helpful: fb.filter((c) => c.feedback!.helpful === "yes").length, fbN: fb.length, daily: dailyCounts(all, 14), conf: confidenceMix(all), top: topIssues(all), dist, avg: Math.round(avgConfidence(all) * 100) };
  }, [data]);

  if (isLoading || !data) return <div className="grid gap-4 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="!h-28 !rounded-card" />)}</div>;
  const week = m.daily.slice(-7).reduce((s, d) => s + d.value, 0);
  const prev = m.daily.slice(0, 7).reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-6">
      <PageHeader title={L("প্ল্যাটফর্ম ড্যাশবোর্ড", "Platform dashboard")} sub={L("পাইলট এলাকার পরীক্ষা, মান ও বিশেষজ্ঞ-সম্মতির সারসংক্ষেপ।", "Pilot-area checks, quality and expert agreement at a glance.")} />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label={L("মোট কেস", "Total cases")} value={m.all.length} icon={<Camera size={18} />} spark={m.daily.map((d) => d.value)} hint={L(`এ সপ্তাহে ${week} · আগে ${prev}`, `${week} this week · ${prev} before`)} />
        <Stat label={L("বিশেষজ্ঞের সাথে মিল", "Expert agreement")} value={m.reviewed.length ? `${Math.round((m.agree / m.reviewed.length) * 100)}%` : "—"} icon={<BadgeCheck size={18} />} tone="sky" hint={L(`${m.reviewed.length}টি পর্যালোচিত`, `${m.reviewed.length} reviewed`)} />
        <Stat label={L("কাজে লেগেছে", "Marked helpful")} value={m.fbN ? `${Math.round((m.helpful / m.fbN) * 100)}%` : "—"} icon={<ThumbsUp size={18} />} tone="sun" hint={L(`${m.fbN}টি মতামত`, `${m.fbN} responses`)} />
        <Stat label={L("গড় নিশ্চয়তা", "Avg. confidence")} value={`${m.avg}%`} icon={<Activity size={18} />} />
      </div>

      <ChartCard title={L("দৈনিক কেস", "Cases per day")} sub={L("গত ১৪ দিন, সব জেলা", "Last 14 days, all districts")} table={{ head: [L("তারিখ", "Date"), L("কেস", "Cases")], rows: m.daily.map((d) => [d.date, d.value]) }}>
        <TrendChart data={m.daily} unit={L("কেস", "cases")} />
      </ChartCard>

      <div className="grid gap-5 lg:grid-cols-3">
        <ChartCard title={L("মডেলের নিশ্চয়তা", "Model confidence")} table={{ head: [L("মাত্রা", "Level"), L("কেস", "Cases")], rows: m.conf.map((x) => [x.level, x.value]) }}>
          <Donut center={m.all.length} centerLabel={L("কেস", "cases")} parts={[{ label: L("উচ্চ", "High"), value: m.conf[0].value, color: "#1F9D5C" }, { label: L("মাঝারি", "Medium"), value: m.conf[1].value, color: "#D99A00" }, { label: L("কম", "Low"), value: m.conf[2].value, color: "#D9472F" }]} />
        </ChartCard>
        <ChartCard title={L("সবচেয়ে বেশি শনাক্ত সমস্যা", "Most detected problems")} table={{ head: [L("সমস্যা", "Problem"), L("কেস", "Cases")], rows: m.top.map((x) => [x.name, x.value]) }}>
          <HBars rows={m.top.map((x) => ({ label: x.name, value: x.value, color: CROP_COLOR[x.crop] }))} />
          <p className="hint">{L("রঙ = ফসল: নীল আলু, কমলা টমেটো, সবুজাভ নীল মরিচ", "Colour = crop: blue potato, orange tomato, aqua chili")}</p>
        </ChartCard>
        <ChartCard title={L("জেলা অনুযায়ী কেস", "Cases by district")} table={{ head: [L("জেলা", "District"), L("কেস", "Cases")], rows: m.dist.map((x) => [x.label, x.value]) }}>
          <HBars rows={m.dist.map((x) => ({ ...x, color: "#178049" }))} />
        </ChartCard>
      </div>

      <section className="card p-5">
        <h2 className="mb-4 text-[1.1rem]">{L("ফিচার ফ্ল্যাগ", "Feature flags")}</h2>
        <ul className="grid gap-3 sm:grid-cols-3">{[["ফসল পরীক্ষা", "Crop diagnosis", true], ["আবহাওয়া ও জলবায়ু", "Climate and weather", flags.climate], ["বাজারদর ও ক্রেতা", "Market and buyers", flags.market]].map(([b, e, on]) => (
          <li key={b as string} className="flex items-center justify-between rounded-xl bg-canvas p-3.5"><span className="font-semibold">{L(b as string, e as string)}</span><Badge tone={on ? "brand" : "neutral"}>{on ? L("চালু", "On") : L("বন্ধ", "Off")}</Badge></li>
        ))}</ul>
      </section>
    </div>
  );
}
