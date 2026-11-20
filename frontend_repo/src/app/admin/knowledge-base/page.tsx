"use client";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Ban, CheckCircle2, Leaf, Search, Send, ShieldAlert, Upload } from "lucide-react";
import { Badge, Button, Drawer, PageHeader, Segmented, Skeleton } from "@/components/ui";
import { AdminArticle, ArticleStatus, listArticles } from "@/lib/api";
import { fmtDate } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

type Filter = "all" | ArticleStatus;

export default function KnowledgeBase() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const { data, isLoading } = useQuery({ queryKey: ["articles"], queryFn: listArticles });
  const [open, setOpen] = useState<AdminArticle | null>(null);
  const [local, setLocal] = useState<Record<string, ArticleStatus | "published">>({});
  const [f, setF] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const st = (a: AdminArticle) => local[a.id] ?? a.status;
  const badge = (s: ArticleStatus | "published") => ({ approved: ["অনুমোদিত", "Approved", "brand"], pending_review: ["পর্যালোচনায়", "In review", "sun"], draft: ["খসড়া", "Draft", "neutral"], published: ["প্রকাশিত", "Published", "sky"] } as const)[s];
  const rows = useMemo(() => (data ?? []).filter((a) => (f === "all" || st(a) === f) && (!q || (a.issue + a.crop).includes(q))), [data, f, q, local]); // eslint-disable-line react-hooks/exhaustive-deps
  const count = (s: Filter) => (data ?? []).filter((a) => s === "all" || st(a) === s).length;

  return (
    <div>
      <PageHeader title={L("পরামর্শ ভান্ডার", "Advisory content")} sub={L("কৃষকদের কাছে যাওয়া প্রতিটি পরামর্শ বিশেষজ্ঞের অনুমোদনের পরই প্রকাশ করা যায়।", "Advice reaches farmers only after expert approval.")} />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented value={f} onChange={setF} label={L("অবস্থা", "Status")} options={[{ value: "all", label: `${L("সব", "All")} ${count("all")}` }, { value: "approved", label: `${L("অনুমোদিত", "Approved")} ${count("approved")}` }, { value: "pending_review", label: `${L("পর্যালোচনায়", "In review")} ${count("pending_review")}` }, { value: "draft", label: `${L("খসড়া", "Draft")} ${count("draft")}` }]} />
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs"><Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" size={17} /><input className="field !min-h-[42px] pl-9" placeholder={L("সমস্যা বা ফসল", "Issue or crop")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={L("খুঁজুন", "Search")} /></div>
      </div>
      {isLoading ? <Skeleton className="!h-72 !rounded-card" /> : (
        <div className="card overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[700px]">
            <thead className="border-b border-line bg-canvas"><tr>{[L("সমস্যা", "Issue"), L("ফসল", "Crop"), L("অবস্থা", "Status"), L("যাচাইকারী", "Reviewer"), L("হালনাগাদ", "Updated"), ""].map((h, i) => <th key={i} className="th">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-line">{rows.map((a) => { const b = badge(st(a)); return (
              <tr key={a.id} className="transition hover:bg-canvas"><td className="td font-semibold">{a.issue}</td><td className="td">{a.crop}</td><td className="td"><Badge tone={b[2]}>{L(b[0], b[1])}</Badge></td><td className="td text-ink-soft">{a.reviewer}</td><td className="td text-ink-soft">{fmtDate(a.updated, lang)}</td><td className="td text-right"><Button variant="secondary" size="sm" onClick={() => setOpen(a)}>{L("খুলুন", "Open")}</Button></td></tr>); })}
            {rows.length === 0 && <tr><td colSpan={6} className="td py-10 text-center text-ink-mute">{L("কিছু পাওয়া যায়নি।", "Nothing found.")}</td></tr>}</tbody>
          </table>
        </div>
      )}

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open?.issue ?? ""} footer={open && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {st(open) === "draft" && <Button onClick={() => setLocal({ ...local, [open.id]: "pending_review" })}><Send size={18} />{L("বিশেষজ্ঞ পর্যালোচনায় পাঠান", "Submit for expert review")}</Button>}
            <Button variant={st(open) === "approved" ? "primary" : "secondary"} disabled={st(open) !== "approved"} onClick={() => { setLocal({ ...local, [open.id]: "published" }); setOpen(null); }}><Upload size={18} />{L("প্রকাশ করুন", "Publish")}</Button>
          </div>
          {st(open) !== "approved" && st(open) !== "published" && <p className="text-[13.5px] text-ink-mute">{L("অনুমোদন ছাড়া প্রকাশ করা যাবে না।", "Publishing is locked until an expert approves.")}</p>}
        </div>
      )}>
        {open && (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2"><Badge tone={badge(st(open))[2]}>{L(badge(st(open))[0], badge(st(open))[1])}</Badge><span className="text-[14px] text-ink-mute">{open.crop} · {fmtDate(open.updated, lang)}</span></div>
            {[[L("আজ যা করবেন", "Do today"), open.advisory.immediate_actions_bn, <CheckCircle2 key="a" size={18} className="text-brand-600" />], [L("যা করবেন না", "Do not"), open.advisory.prohibited_actions_bn, <Ban key="b" size={18} className="text-clay-500" />], [L("প্রতিরোধ", "Prevention"), open.advisory.prevention_bn, <Leaf key="c" size={18} className="text-brand-600" />]].map(([t, items, icon]) => (
              <div key={t as string}><h3 className="mb-2 flex items-center gap-2 text-[1.05rem]">{icon as React.ReactNode}{t as string}</h3><ul className="space-y-1.5">{(items as string[]).map((x, i) => <li key={i} className="rounded-lg bg-canvas px-3.5 py-2.5">{x}</li>)}</ul></div>
            ))}
            <p className="flex items-start gap-2 rounded-card bg-sun-50 p-3.5 font-semibold text-sun-700"><ShieldAlert size={19} className="mt-1 shrink-0" />{open.advisory.safety_warning_bn}</p>
          </div>
        )}
      </Drawer>
    </div>
  );
}
