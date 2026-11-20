"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Camera, HandHelping, MessageCircleQuestion, Minus, ThumbsDown, ThumbsUp, TrendingDown, TrendingUp } from "lucide-react";
import { AdvisoryPanel, AttentionBanner, CaseHero, ExpertReplyCard, StatusTimeline } from "@/components/result";
import { Button, EmptyState, LinkButton, Spinner } from "@/components/ui";
import { getCase, requestExpert, submitFeedback } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useL } from "@/store/app";

type FB = NonNullable<Parameters<typeof submitFeedback>[1]>;

export default function CasePage() {
  const { id } = useParams<{ id: string }>();
  const L = useL();
  const qc = useQueryClient();
  const { data: c, isLoading, error } = useQuery({ queryKey: ["case", id], queryFn: () => getCase(id) });
  const expert = useMutation({ mutationFn: () => requestExpert(id), onSuccess: () => { qc.invalidateQueries({ queryKey: ["case", id] }); qc.invalidateQueries({ queryKey: ["cases"] }); } });
  const fb = useMutation({ mutationFn: (v: FB) => submitFeedback(id, v), onSuccess: () => qc.invalidateQueries({ queryKey: ["case", id] }) });

  if (isLoading) return <Spinner label={L("ফলাফল আনা হচ্ছে…", "Loading result…")} />;
  if (error || !c) return <EmptyState icon={<MessageCircleQuestion size={28} />} title={L("কেসটি পাওয়া যায়নি", "Case not found")} body={L("লিংকটি ভুল হতে পারে। ইতিহাস থেকে আবার খুলুন।", "The link may be wrong. Open it again from your history.")} action={<LinkButton href="/farmer/cases">{L("ইতিহাসে যান", "Go to history")}</LinkButton>} />;

  const inExpertFlow = ["needs_expert_review", "under_review", "response_received", "closed"].includes(c.status);
  const unsure = !c.diagnosis.issue;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <Link href="/farmer/cases" className="inline-flex items-center gap-2 font-semibold text-ink-soft hover:text-ink"><ArrowLeft size={19} />{L("ইতিহাস", "History")}</Link>
        <span className="rounded-full bg-white px-3 py-1 text-[13.5px] font-semibold text-ink-mute ring-1 ring-inset ring-line-strong">{c.case_number}</span>
      </div>

      <AttentionBanner c={c} />
      <CaseHero c={c} />

      <div className="grid items-start gap-5 lg:grid-cols-[1.5fr_1fr]">
        <AdvisoryPanel c={c} />

        <div className="space-y-5 lg:sticky lg:top-6">
          {!inExpertFlow ? (
            <section className="card space-y-3 p-5">
              <h3 className="text-xl">{L("নিশ্চিত হতে চান?", "Want to be sure?")}</h3>
              <p className="text-ink-soft">{L("কৃষি বিশেষজ্ঞ আপনার ছবি দেখে বাংলায় উত্তর দেবেন।", "An expert will look at your photo and reply in Bangla.")}</p>
              <Button loading={expert.isPending} onClick={() => expert.mutate()} className="w-full"><HandHelping size={20} />{L("বিশেষজ্ঞের পরামর্শ নিন", "Ask an expert")}</Button>
            </section>
          ) : (
            <section className="card space-y-4 p-5">
              <h3 className="text-xl">{L("বিশেষজ্ঞ পর্যালোচনা", "Expert review")}</h3>
              <StatusTimeline status={c.status} />
              {c.status === "needs_expert_review" && <p className="rounded-ctl bg-sun-50 px-4 py-3 text-sun-700 ring-1 ring-inset ring-sun-100">{L("কেস পাঠানো হয়েছে। উত্তর এলে এখানে ও বিজ্ঞপ্তিতে জানানো হবে।", "Your case was sent. The reply will show here and in notifications.")}</p>}
            </section>
          )}
          <ExpertReplyCard c={c} />
          {unsure && <LinkButton href="/farmer/diagnose" variant="secondary" className="w-full"><Camera size={19} />{L("নতুন ছবি দিয়ে আবার দেখুন", "Retry with a new photo")}</LinkButton>}
          <section className="card space-y-4 p-5">
            <h3 className="text-xl">{L("পরামর্শ কি কাজে লেগেছে?", "Did the advice help?")}</h3>
            {c.feedback ? <p className="rounded-ctl bg-brand-50 px-4 py-3 font-semibold text-brand-700">{L("মতামতের জন্য ধন্যবাদ। এটি সিস্টেম উন্নত করবে।", "Thanks for your feedback. It helps improve the system.")}</p> : <FeedbackForm busy={fb.isPending} onSubmit={(v) => fb.mutate(v)} />}
          </section>
        </div>
      </div>
      <p className="pb-2 text-center text-[13.5px] text-ink-mute">{L("এটি AI-সহায়ক পরামর্শ, যোগ্য কৃষি বিশেষজ্ঞের পরামর্শের বিকল্প নয়।", "AI-supported advice. It does not replace qualified agricultural consultation.")}</p>
    </div>
  );
}

function FeedbackForm({ onSubmit, busy }: { onSubmit: (v: FB) => void; busy: boolean }) {
  const L = useL();
  const [h, setH] = useState<FB["helpful"] | null>(null);
  const [o, setO] = useState<FB["outcome"] | null>(null);
  const opt = (on: boolean) => cn("flex min-h-[48px] flex-1 items-center justify-center gap-2 rounded-ctl px-3 font-semibold ring-1 ring-inset transition", on ? "bg-brand-50 text-brand-700 ring-brand-500" : "bg-white ring-line-strong hover:bg-canvas");
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button className={opt(h === "yes")} aria-pressed={h === "yes"} onClick={() => setH("yes")}><ThumbsUp size={18} />{L("হ্যাঁ", "Yes")}</button>
        <button className={opt(h === "no")} aria-pressed={h === "no"} onClick={() => setH("no")}><ThumbsDown size={18} />{L("না", "No")}</button>
        <button className={opt(h === "need_help")} aria-pressed={h === "need_help"} onClick={() => setH("need_help")}><HandHelping size={18} />{L("আরও সাহায্য চাই", "Need help")}</button>
      </div>
      <p className="label !mb-0">{L("গাছের অবস্থা এখন কেমন?", "How is the crop now?")}</p>
      <div className="flex flex-wrap gap-2">
        <button className={opt(o === "better")} aria-pressed={o === "better"} onClick={() => setO("better")}><TrendingUp size={18} />{L("ভালো", "Better")}</button>
        <button className={opt(o === "same")} aria-pressed={o === "same"} onClick={() => setO("same")}><Minus size={18} />{L("একই", "Same")}</button>
        <button className={opt(o === "worse")} aria-pressed={o === "worse"} onClick={() => setO("worse")}><TrendingDown size={18} />{L("খারাপ", "Worse")}</button>
      </div>
      <Button loading={busy} disabled={!h || !o} onClick={() => h && o && onSubmit({ helpful: h, outcome: o })} className="w-full">{L("মতামত পাঠান", "Send feedback")}</Button>
    </div>
  );
}
