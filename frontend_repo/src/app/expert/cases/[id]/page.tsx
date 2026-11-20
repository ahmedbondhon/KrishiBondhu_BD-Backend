"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Lock, Pencil, Send, Wand2, X } from "lucide-react";
import { Meter } from "@/components/result";
import { Button, ConfidenceBadge, Spinner, StatusBadge, UrgencyBadge } from "@/components/ui";
import { acceptCase, expertReview, getCase } from "@/lib/api";
import { ISSUES } from "@/lib/data";
import { cn, fmtDate } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { ExpertReply, Urgency } from "@/types";

const TEMPLATES = [
  "আক্রান্ত অংশ আজই সরিয়ে ফেলুন এবং আশেপাশের গাছগুলো পরীক্ষা করুন।",
  "দুই দিনের মধ্যে সমস্যা বাড়লে স্থানীয় উপজেলা কৃষি অফিসে যোগাযোগ করুন।",
  "পাতায় সরাসরি পানি দেওয়া এড়িয়ে চলুন এবং সকালে সেচ দিন।",
];

export default function ExpertCase() {
  const { id } = useParams<{ id: string }>();
  const L = useL();
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user)!;
  const qc = useQueryClient();
  const { data: c, isLoading } = useQuery({ queryKey: ["case", id], queryFn: () => getCase(id) });
  const accept = useMutation({ mutationFn: () => acceptCase(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["case", id] }) });
  const send = useMutation({ mutationFn: (r: Omit<ExpertReply, "created_at">) => expertReview(id, r), onSuccess: () => { qc.invalidateQueries({ queryKey: ["case", id] }); qc.invalidateQueries({ queryKey: ["cases"] }); } });

  const [decision, setDecision] = useState<ExpertReply["decision"]>("approved_ai");
  const [issue, setIssue] = useState("");
  const [resp, setResp] = useState("");
  const [urg, setUrg] = useState<Urgency>("medium");
  const [follow, setFollow] = useState("");

  useEffect(() => { if (c?.status === "needs_expert_review") accept.mutate(); }, [c?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (c) setUrg(c.diagnosis.urgency === "unknown" ? "medium" : c.diagnosis.urgency); }, [c?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading || !c) return <Spinner />;
  const answered = !!c.expert_reply;
  const decisions = [
    { v: "approved_ai" as const, I: Check, bn: "ফলাফল সঠিক", en: "Approve", on: "bg-brand-50 text-brand-700 ring-brand-500" },
    { v: "corrected_ai" as const, I: Pencil, bn: "সংশোধন", en: "Correct", on: "bg-sun-50 text-sun-700 ring-sun-500" },
    { v: "rejected_ai" as const, I: X, bn: "বাতিল", en: "Reject", on: "bg-clay-50 text-clay-700 ring-clay-500" },
  ];
  const canSend = resp.trim().length > 10 && (decision === "approved_ai" || !!issue);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link href="/expert/cases" className="inline-flex items-center gap-2 font-semibold text-ink-soft hover:text-ink"><ArrowLeft size={19} />{L("কেস তালিকা", "Case queue")}</Link>
        <div className="flex items-center gap-2"><span className="text-ink-mute">{c.case_number}</span><StatusBadge status={c.status} /></div>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <section className="card overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={c.image_url} alt={L("কৃষকের ছবি", "Farmer's photo")} className="h-72 w-full object-cover" />
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 p-5">
              {[[L("কৃষক", "Farmer"), c.farmer_name], [L("জেলা", "District"), c.district], [L("ফসল", "Crop"), `${c.crop.emoji} ${L(c.crop.name_bn, c.crop.name_en)}`], [L("পর্যায়", "Stage"), c.growth_stage], [L("আক্রান্ত", "Affected"), `${c.affected_percent}%`], [L("জমার সময়", "Submitted"), fmtDate(c.created_at, lang)]].map(([k, v]) => <div key={k as string}><dt className="text-[13px] text-ink-mute">{k}</dt><dd className="font-semibold">{v}</dd></div>)}
              <div className="col-span-2"><dt className="text-[13px] text-ink-mute">{L("কৃষকের বর্ণনা", "Farmer's description")}</dt><dd className="font-semibold">{c.symptom_bn || "—"}</dd></div>
            </dl>
          </section>

          <section className="card p-5">
            <div className="flex items-center justify-between gap-2"><h2 className="text-[1.1rem]">{L("সিস্টেমের পূর্বাভাস", "System prediction")}</h2><span className="inline-flex items-center gap-1 text-[13px] text-ink-mute"><Lock size={13} />{L("সংরক্ষিত, বদলানো যায় না", "Preserved, read-only")}</span></div>
            <p className="mt-2 font-display text-2xl font-bold">{c.diagnosis.issue?.name_bn ?? L("নিশ্চিত শনাক্ত হয়নি", "Not identified")}</p>
            <div className="my-3 flex flex-wrap gap-2"><ConfidenceBadge level={c.diagnosis.confidence_level} score={c.diagnosis.confidence_score} /><UrgencyBadge urgency={c.diagnosis.urgency} /></div>
            <Meter score={c.diagnosis.confidence_score} level={c.diagnosis.confidence_level} />
            <ul className="mt-4 space-y-1.5 text-[15px]">{c.diagnosis.candidates.map((x, i) => <li key={i} className="flex justify-between gap-3"><span>{x.name_bn}</span><span className="font-semibold tabular-nums">{Math.round(x.probability * 100)}%</span></li>)}</ul>
            <p className="mt-3 text-[13px] text-ink-mute">{L("মডেল", "Model")}: krishibondhu-crop-vision {c.diagnosis.model_version}</p>
          </section>
        </div>

        {answered ? (
          <section className="card border-l-4 border-l-brand-500 p-5">
            <h2 className="text-xl text-brand-700">{L("আপনার উত্তর পাঠানো হয়েছে", "Your reply was sent")}</h2>
            <p className="mt-2 text-[17px]">{c.expert_reply!.response_bn}</p>
            {c.expert_reply!.corrected_issue_bn && <p className="mt-3 font-display font-bold">{L("সংশোধিত সমস্যা: ", "Corrected issue: ")}{c.expert_reply!.corrected_issue_bn}</p>}
          </section>
        ) : (
          <section className="card space-y-5 p-5 lg:sticky lg:top-6">
            <h2 className="text-xl">{L("আপনার পর্যালোচনা", "Your review")}</h2>
            <div role="radiogroup" aria-label={L("সিদ্ধান্ত", "Decision")} className="grid grid-cols-3 gap-2">
              {decisions.map(({ v, I, bn, en, on }) => <button key={v} role="radio" aria-checked={decision === v} onClick={() => setDecision(v)} className={cn("flex min-h-[64px] flex-col items-center justify-center gap-1 rounded-ctl px-2 text-[14.5px] font-semibold ring-1 ring-inset transition", decision === v ? on : "bg-white ring-line-strong hover:bg-canvas")}><I size={19} />{L(bn, en)}</button>)}
            </div>
            {decision !== "approved_ai" && (
              <div><label className="label" htmlFor="iss">{L("সঠিক সমস্যা", "Correct issue")}</label>
                <select id="iss" className="field" value={issue} onChange={(e) => setIssue(e.target.value)}><option value="">{L("— বেছে নিন —", "— choose —")}</option>{ISSUES.filter((i) => i.crop_code === c.crop.code).map((i) => <option key={i.id} value={i.name_bn}>{i.name_bn}</option>)}<option value="অন্য সমস্যা / পুষ্টির ঘাটতি">অন্য সমস্যা / পুষ্টির ঘাটতি</option></select></div>
            )}
            <div>
              <label className="label" htmlFor="resp">{L("কৃষকের জন্য বাংলায় উত্তর", "Reply to the farmer (Bangla)")}</label>
              <textarea id="resp" className="field min-h-[130px]" value={resp} onChange={(e) => setResp(e.target.value)} />
              <div className="mt-2 flex flex-wrap gap-2">{TEMPLATES.map((t, i) => <button key={i} onClick={() => setResp((r) => (r ? r + " " : "") + t)} className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1.5 text-[14px] font-semibold text-brand-700 hover:bg-brand-100"><Wand2 size={14} />{L("দ্রুত বাক্য", "Quick phrase")} {i + 1}</button>)}</div>
              <p className="hint">{L("কীটনাশকের নাম ও মাত্রা শুধু অনুমোদিত নির্দেশনা থেকে লিখুন।", "Only write pesticide names and doses from approved guidance.")}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div><label className="label" htmlFor="u">{L("জরুরি মাত্রা", "Urgency")}</label><select id="u" className="field" value={urg} onChange={(e) => setUrg(e.target.value as Urgency)}><option value="low">{L("কম", "Low")}</option><option value="medium">{L("মাঝারি", "Medium")}</option><option value="high">{L("উচ্চ", "High")}</option></select></div>
              <div><label className="label" htmlFor="fu">{L("ফলোআপের তারিখ", "Follow-up date")}</label><input id="fu" type="date" className="field" value={follow} onChange={(e) => setFollow(e.target.value)} /></div>
            </div>
            <Button size="lg" className="w-full" disabled={!canSend} loading={send.isPending} onClick={() => send.mutate({ expert_name: user.name, decision, corrected_issue_bn: decision === "approved_ai" ? undefined : issue, response_bn: resp.trim(), urgency: urg, follow_up_date: follow || undefined })}><Send size={19} />{L("কৃষকের কাছে পাঠান", "Send to farmer")}</Button>
          </section>
        )}
      </div>
    </div>
  );
}
