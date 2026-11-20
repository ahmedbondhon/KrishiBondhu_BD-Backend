"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Inbox, Search } from "lucide-react";
import { ConfidenceBadge, EmptyState, PageHeader, Segmented, Skeleton, StatusBadge, UrgencyBadge } from "@/components/ui";
import { listCases } from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { DiagnosisCase } from "@/types";

type Tab = "all" | "new" | "review" | "done";
const inTab = (c: DiagnosisCase, t: Tab) => t === "all" || (t === "new" ? c.status === "needs_expert_review" : t === "review" ? c.status === "under_review" : c.status === "response_received" || c.status === "closed");

export default function ExpertCases() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const { data, isLoading } = useQuery({ queryKey: ["cases", "expert"], queryFn: () => listCases("expert") });
  const [tab, setTab] = useState<Tab>("all");
  const [q, setQ] = useState("");
  const [crop, setCrop] = useState("all");
  const [urg, setUrg] = useState("all");

  const count = (t: Tab) => (data ?? []).filter((c) => inTab(c, t)).length;
  const rows = useMemo(() => {
    const order = { high: 0, unknown: 1, medium: 2, low: 3 } as const;
    return (data ?? [])
      .filter((c) => inTab(c, tab) && (crop === "all" || c.crop.code === crop) && (urg === "all" || c.diagnosis.urgency === urg))
      .filter((c) => !q || (c.farmer_name + c.case_number + c.district).toLowerCase().includes(q.toLowerCase()))
      .sort((a, b) => order[a.diagnosis.urgency] - order[b.diagnosis.urgency] || +new Date(b.created_at) - +new Date(a.created_at));
  }, [data, tab, q, crop, urg]);

  return (
    <div>
      <PageHeader title={L("কেস তালিকা", "Case queue")} sub={L("জরুরি ও অনিশ্চিত কেস উপরে দেখানো হয়।", "Urgent and uncertain cases are shown first.")} />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented value={tab} onChange={setTab} label={L("অবস্থা", "Status")} options={[{ value: "all", label: `${L("সব", "All")} ${count("all")}` }, { value: "new", label: `${L("নতুন", "New")} ${count("new")}` }, { value: "review", label: `${L("পর্যালোচনায়", "In review")} ${count("review")}` }, { value: "done", label: `${L("সম্পন্ন", "Done")} ${count("done")}` }]} />
        <div className="relative min-w-[220px] flex-1"><Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" size={17} /><input className="field !min-h-[42px] pl-9" placeholder={L("কৃষক, কেস নম্বর বা জেলা", "Farmer, case no. or district")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={L("খুঁজুন", "Search")} /></div>
        <select className="field !min-h-[42px] !w-auto" value={crop} onChange={(e) => setCrop(e.target.value)} aria-label={L("ফসল", "Crop")}><option value="all">{L("সব ফসল", "All crops")}</option><option value="potato">{L("আলু", "Potato")}</option><option value="tomato">{L("টমেটো", "Tomato")}</option><option value="chili">{L("মরিচ", "Chili")}</option></select>
        <select className="field !min-h-[42px] !w-auto" value={urg} onChange={(e) => setUrg(e.target.value)} aria-label={L("জরুরি মাত্রা", "Urgency")}><option value="all">{L("সব মাত্রা", "All urgency")}</option><option value="high">{L("উচ্চ", "High")}</option><option value="medium">{L("মাঝারি", "Medium")}</option><option value="unknown">{L("অনিশ্চিত", "Unknown")}</option></select>
      </div>

      {isLoading ? <Skeleton className="!h-72 !rounded-card" /> : rows.length === 0 ? <EmptyState icon={<Inbox size={28} />} title={L("কোনো কেস নেই", "No cases")} body={L("এই ফিল্টারে কোনো কেস মেলেনি। ফিল্টার বদলে দেখুন।", "No cases match these filters. Try changing them.")} /> : (
        <>
          <div className="card hidden overflow-x-auto scrollbar-thin md:block">
            <table className="w-full min-w-[820px]">
              <thead className="border-b border-line bg-canvas"><tr>{[L("ছবি", "Photo"), L("কেস", "Case"), L("কৃষক", "Farmer"), L("সিস্টেমের ফলাফল", "System result"), L("জরুরি", "Urgency"), L("অবস্থা", "Status")].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-line">
                {rows.map((c) => (
                  <tr key={c.id} className="transition hover:bg-canvas">
                    <td className="td">{/* eslint-disable-next-line @next/next/no-img-element */}<img src={c.image_url} alt="" className="h-12 w-12 rounded-lg object-cover" /></td>
                    <td className="td"><Link href={`/expert/cases/${c.id}`} className="font-semibold text-brand-700 hover:underline">{c.case_number}</Link><div className="text-[13px] text-ink-mute">{timeAgo(c.created_at, lang)}</div></td>
                    <td className="td">{c.farmer_name}<div className="text-[13px] text-ink-mute">{c.district}</div></td>
                    <td className="td">{c.crop.emoji} {c.diagnosis.issue?.name_bn ?? L("শনাক্ত হয়নি", "Not identified")}<div className="mt-1"><ConfidenceBadge level={c.diagnosis.confidence_level} score={c.diagnosis.confidence_score} /></div></td>
                    <td className="td"><UrgencyBadge urgency={c.diagnosis.urgency} /></td>
                    <td className="td"><StatusBadge status={c.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="space-y-3 md:hidden">{rows.map((c) => (
            <li key={c.id}><Link href={`/expert/cases/${c.id}`} className="card flex gap-3 p-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={c.image_url} alt="" className="h-16 w-16 shrink-0 rounded-xl object-cover" />
              <div className="min-w-0 flex-1"><p className="truncate font-display font-bold">{c.crop.emoji} {c.diagnosis.issue?.name_bn ?? L("শনাক্ত হয়নি", "Not identified")}</p><p className="text-[13px] text-ink-mute">{c.farmer_name} · {c.district} · {timeAgo(c.created_at, lang)}</p><div className="mt-1.5 flex flex-wrap gap-1.5"><UrgencyBadge urgency={c.diagnosis.urgency} /><StatusBadge status={c.status} /></div></div>
            </Link></li>
          ))}</ul>
        </>
      )}
    </div>
  );
}
