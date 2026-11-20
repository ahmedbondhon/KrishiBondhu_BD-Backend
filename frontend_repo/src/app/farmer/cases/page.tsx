"use client";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Camera, ClipboardList, Search } from "lucide-react";
import { CaseRow } from "@/components/case-row";
import { EmptyState, LinkButton, PageHeader, Segmented, Skeleton } from "@/components/ui";
import { listCases } from "@/lib/api";
import { CROPS } from "@/lib/data";
import { cn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

export default function Cases() {
  const L = useL();
  const user = useApp((s) => s.user)!;
  const [f, setF] = useState<"all" | "open" | "done">("all");
  const [crop, setCrop] = useState("all");
  const [q, setQ] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["cases", "mine", user.name], queryFn: () => listCases("mine", user.name) });
  const list = useMemo(() => (data ?? []).filter((c) =>
    (f === "all" || (f === "open" ? ["needs_expert_review", "under_review"].includes(c.status) : ["response_received", "closed", "diagnosed"].includes(c.status))) &&
    (crop === "all" || c.crop.code === crop) &&
    (!q || (c.diagnosis.issue?.name_bn ?? "").includes(q) || c.case_number.includes(q))), [data, f, crop, q]);

  return (
    <div>
      <PageHeader title={L("পরীক্ষার ইতিহাস", "Check history")} sub={L("আপনার সব পরীক্ষা ও বিশেষজ্ঞের উত্তর এক জায়গায়।", "All your checks and expert replies in one place.")} actions={<LinkButton href="/farmer/diagnose" size="md"><Camera size={19} />{L("নতুন পরীক্ষা", "New check")}</LinkButton>} />
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Segmented value={f} onChange={setF} label={L("অবস্থা", "Status")} options={[{ value: "all", label: L("সব", "All") }, { value: "open", label: L("অপেক্ষমাণ", "Waiting") }, { value: "done", label: L("সম্পন্ন", "Done") }]} />
        <div className="flex gap-1.5">{[{ code: "all", bn: "সব ফসল", en: "All crops", emoji: "" }, ...CROPS].map((c) => { const on = crop === c.code; return <button key={c.code} aria-pressed={on} onClick={() => setCrop(c.code)} className={cn("min-h-[38px] rounded-full px-3.5 text-[14.5px] font-semibold ring-1 ring-inset", on ? "bg-brand-600 text-white ring-brand-600" : "bg-white text-ink-soft ring-line-strong hover:bg-brand-50")}>{c.emoji} {"name_bn" in c ? L(c.name_bn, c.name_en) : L(c.bn, c.en)}</button>; })}</div>
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs"><Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" size={17} /><input className="field !min-h-[40px] pl-9" placeholder={L("রোগের নাম বা কেস নম্বর", "Issue name or case no.")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={L("খুঁজুন", "Search")} /></div>
      </div>
      {isLoading ? <div className="space-y-3">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="!h-[96px] !rounded-card" />)}</div> : list.length === 0 ? (
        <EmptyState icon={<ClipboardList size={28} />} title={L("কিছু পাওয়া যায়নি", "Nothing here")} body={L("ফিল্টার বদলে দেখুন, অথবা একটি ফসলের ছবি তুলে নতুন পরীক্ষা করুন।", "Try different filters, or check a crop with a new photo.")} action={<LinkButton href="/farmer/diagnose"><Camera size={19} />{L("পরীক্ষা শুরু করুন", "Start a check")}</LinkButton>} />
      ) : <div className="grid gap-3 lg:grid-cols-2">{list.map((c) => <CaseRow key={c.id} c={c} href={`/farmer/cases/${c.id}`} />)}</div>}
    </div>
  );
}
