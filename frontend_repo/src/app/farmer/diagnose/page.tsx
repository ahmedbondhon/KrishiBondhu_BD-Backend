"use client";
import { useRouter } from "next/navigation";
import { DragEvent, useEffect, useRef, useState } from "react";
import { AlertTriangle, ArrowLeft, ArrowRight, Camera, Check, CheckCircle2, Focus, ImagePlus, Lightbulb, RefreshCw, Sun, UploadCloud, WifiOff } from "lucide-react";
import { Button, LeafScan, PageHeader } from "@/components/ui";
import { useQuery } from "@tanstack/react-query";
import { ApiError, createDiagnosis, listCropIssues, listGrowthStages, verifyCropImage } from "@/lib/api";
import { CROPS, ISSUES, STAGES } from "@/lib/data";
import { ALLOWED, MAX_BYTES, QualityResult, assessQuality, compressImage } from "@/lib/image";
import { cn, toBn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { Crop } from "@/types";

const SYMPTOMS = [
  ["পাতায় বাদামি দাগ", "Brown spots on leaves"], ["পাতা কুঁকড়ে যাচ্ছে", "Leaves curling"], ["পাতা হলুদ হচ্ছে", "Leaves turning yellow"],
  ["পাতা কালো হয়ে পচছে", "Leaves blackening and rotting"], ["ফলে দাগ", "Spots on fruit"], ["গাছ নেতিয়ে পড়ছে", "Plant wilting"],
];
/** Number of problems the backend catalog knows for a crop (falls back to the built-in list). */
function IssueCount({ crop }: { crop: Crop }) {
  const L = useL();
  const q = useQuery({ queryKey: ["issues", crop.id], queryFn: () => listCropIssues(crop.id), staleTime: 3_600_000 });
  const n = q.data?.length ? q.data.length : ISSUES.filter((i) => i.crop_code === crop.code).length;
  return <span className="text-[14px] text-ink-mute">{L(`${n}টি সমস্যা চিনতে পারে`, `Recognises ${n} problems`)}</span>;
}
interface Draft { cropCode?: string; stage?: string; symptom?: string; percent?: number }
const DRAFT_KEY = "kb-diagnose-draft";

export default function DiagnosePage() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [crop, setCrop] = useState<Crop | null>(null);
  const [stage, setStage] = useState("");
  const [symptom, setSymptom] = useState("");
  const [percent, setPercent] = useState(15);
  const [img, setImg] = useState<{ dataUrl: string; blob: Blob; q: QualityResult } | null>(null);
  const [imgErr, setImgErr] = useState("");
  const [checking, setChecking] = useState(false);
  const [drag, setDrag] = useState(false);
  const [phase, setPhase] = useState<null | "uploading" | "analyzing">(null);
  const [err, setErr] = useState("");
  const camRef = useRef<HTMLInputElement>(null);
  const stagesQ = useQuery({ queryKey: ["stages", crop?.id], queryFn: () => listGrowthStages(crop?.id), enabled: !!crop, staleTime: 3_600_000 });
  const STG = stagesQ.data?.length ? stagesQ.data.map((x) => ({ code: x.code, bn: x.name_bn, en: x.name_en })) : STAGES;
  const galRef = useRef<HTMLInputElement>(null);

  // Restore a saved draft (or a ?crop= shortcut) so a dropped connection never loses typed details
  useEffect(() => {
    try {
      const d: Draft = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? "{}");
      const qc = new URLSearchParams(window.location.search).get("crop");
      const code = qc ?? d.cropCode;
      if (code) { setCrop(CROPS.find((c) => c.code === code) ?? null); setStep(1); }
      if (d.stage) setStage(d.stage);
      if (d.symptom) setSymptom(d.symptom);
      if (d.percent) setPercent(d.percent);
    } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify({ cropCode: crop?.code, stage, symptom, percent } satisfies Draft)); } catch {}
  }, [crop, stage, symptom, percent]);

  async function onFile(file?: File | null) {
    setImgErr("");
    if (!file) return;
    if (!ALLOWED.includes(file.type)) return setImgErr(L("শুধু JPG, PNG বা WebP ছবি দেওয়া যাবে।", "Only JPG, PNG or WebP images are allowed."));
    if (file.size > 25 * 1024 * 1024) return setImgErr(L("ছবিটি অনেক বড়। অন্য একটি ছবি বেছে নিন।", "This image is too large. Choose another one."));
    setChecking(true);
    try {
      const { blob, dataUrl } = await compressImage(file);
      if (blob.size > MAX_BYTES) return setImgErr(L("ছবি ৫ MB-এর বেশি। একটু কাছ থেকে আবার তুলুন।", "Image is over 5 MB. Retake it a little closer."));
      if (crop) {
        try { await verifyCropImage(dataUrl, crop); } // backend AI gatekeeper: not a plant / wrong crop
        catch (e) { const ae = e as ApiError; return setImgErr(lang === "bn" ? ae.message_bn ?? ae.message : ae.message); }
      }
      setImg({ dataUrl, blob, q: await assessQuality(dataUrl) });
    } catch {
      setImgErr(L("ছবিটি খোলা যায়নি। আরেকটি ছবি দিন।", "We could not open this image. Try another."));
    } finally {
      setChecking(false);
    }
  }
  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files?.[0]); };

  async function submit() {
    if (!crop || !img) return;
    setErr("");
    if (!navigator.onLine) return setErr(L("ইন্টারনেট নেই। আপনার তথ্য সংরক্ষিত আছে — সংযোগ ফিরলে আবার চাপুন।", "You are offline. Your details are saved — tap again once you reconnect."));
    try {
      const c = await createDiagnosis({ crop, growth_stage: STG.find((s) => s.code === stage)?.bn ?? stage, symptom_bn: symptom, affected_percent: percent, image_data_url: img.dataUrl, image_blob: img.blob, quality: img.q.status, farmer_name: user?.name ?? "কৃষক", district: user?.district ?? "বগুড়া" }, setPhase);
      try { localStorage.removeItem(DRAFT_KEY); } catch {}
      router.replace(`/farmer/cases/${c.id}`);
    } catch (e) {
      setPhase(null);
      const ae = e as ApiError;
      setErr(lang === "bn" ? ae.message_bn ?? "ফলাফল আনা যায়নি। একটু পরে আবার চেষ্টা করুন।" : ae.message);
    }
  }

  const q = img && {
    acceptable: { ok: true, bn: "ছবিটি পরীক্ষার জন্য ভালো।", en: "This photo is good for analysis." },
    blurry: { ok: false, bn: "ছবিটি ঝাপসা। ফোন স্থির রেখে আরও কাছ থেকে আবার তুলুন।", en: "Photo is blurry. Hold steady and retake closer." },
    dark: { ok: false, bn: "ছবিটি অন্ধকার। দিনের আলোয় আবার তুলুন।", en: "Photo is too dark. Retake in daylight." },
    bright: { ok: false, bn: "আলো খুব বেশি। হালকা ছায়ায় এনে আবার তুলুন।", en: "Too bright. Move into light shade and retake." },
  }[img.q.status];

  if (phase)
    return (
      <div className="rows-texture fixed inset-0 z-[60] grid place-items-center bg-canopy p-6 text-white" role="status" aria-live="polite">
        <div className="w-full max-w-sm text-center">
          <LeafScan />
          <h2 className="mt-6 text-2xl">{phase === "uploading" ? L("ছবি পাঠানো হচ্ছে…", "Uploading photo…") : L("ছবি বিশ্লেষণ চলছে…", "Analysing photo…")}</h2>
          <p className="mt-1 text-brand-100">{L("কয়েক সেকেন্ড লাগবে। অপেক্ষা করুন।", "This takes a few seconds. Please wait.")}</p>
          <ol className="mx-auto mt-6 w-fit space-y-2 text-left">
            {([["uploading", "ছবি পাঠানো", "Photo uploaded"], ["analyzing", "রোগ শনাক্তকরণ", "Identifying the problem"]] as const).map(([k, b, e], i) => {
              const done = phase === "analyzing" && i === 0;
              return <li key={k} className="flex items-center gap-2.5 text-brand-100">{done ? <CheckCircle2 size={20} className="text-lime-400" /> : <span className={cn("h-5 w-5 rounded-full border-2", phase === k ? "animate-pulse border-lime-400" : "border-white/25")} />}<span className={phase === k || done ? "font-semibold text-white" : ""}>{L(b, e)}</span></li>;
            })}
          </ol>
        </div>
      </div>
    );

  const labels = [L("ফসল", "Crop"), L("বিবরণ", "Details"), L("ছবি", "Photo"), L("নিশ্চিত", "Confirm")];
  const stageObj = STG.find((x) => x.code === stage);
  const pctText = (lang === "bn" ? toBn(percent) : percent) + "%";

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title={L("নতুন পরীক্ষা", "New check")} sub={L("চার ধাপে আপনার ফসলের সমস্যা বুঝুন।", "Understand your crop's problem in four steps.")} />

      <ol className="mb-7 grid grid-cols-4 gap-2" aria-label={L("ধাপ", "Steps")}>
        {labels.map((t, i) => {
          const done = i < step, on = i === step;
          return (
            <li key={t}>
              <button disabled={!done} onClick={() => setStep(i)} aria-current={on ? "step" : undefined} className="group w-full text-left disabled:cursor-default">
                <span className={cn("block h-1.5 rounded-full transition-colors", done || on ? "bg-brand-600" : "bg-line-strong")} />
                <span className="mt-2 flex items-center gap-1.5 text-[14px] font-semibold">
                  <span className={cn("grid h-5 w-5 place-items-center rounded-full text-[11px]", done ? "bg-brand-600 text-white" : on ? "bg-canopy text-white" : "bg-line-strong text-ink-mute")}>{done ? <Check size={12} strokeWidth={3.5} /> : lang === "bn" ? toBn(i + 1) : i + 1}</span>
                  <span className={on ? "text-ink" : done ? "text-brand-700" : "text-ink-mute"}>{t}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0">
          {step === 0 && (
            <section>
              <h2 className="mb-4 text-2xl">{L("কোন ফসল পরীক্ষা করবেন?", "Which crop are you checking?")}</h2>
              <div className="grid gap-3 sm:grid-cols-3">
                {CROPS.map((c) => (
                  <button key={c.id} onClick={() => { setCrop(c); setStep(1); }} className={cn("card flex flex-row items-center gap-4 p-4 text-left transition hover:shadow-pop sm:flex-col sm:items-start sm:gap-2 sm:p-5", crop?.id === c.id && "ring-2 ring-brand-600")}>
                    <span className="grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-[2.6rem]">{c.emoji}</span>
                    <span><span className="block font-display text-2xl font-bold">{L(c.name_bn, c.name_en)}</span><IssueCount crop={c} /></span>
                  </button>
                ))}
              </div>
              <p className="hint">{L("শুরুতে আমরা এই তিনটি ফসলের সমস্যা চিনতে পারি।", "For now we recognise problems in these three crops.")}</p>
            </section>
          )}

          {step === 1 && crop && (
            <section className="space-y-7">
              <h2 className="text-2xl">{L(`${crop.name_bn} সম্পর্কে বলুন`, `Tell us about your ${crop.name_en.toLowerCase()}`)}</h2>
              <div>
                <p className="label">{L("গাছ এখন কোন পর্যায়ে?", "What stage is the crop at?")}</p>
                <div className="flex flex-wrap gap-2">{STG.map((s) => <button key={s.code} onClick={() => setStage(s.code)} aria-pressed={stage === s.code} className={cn("min-h-[44px] rounded-full px-[18px] font-semibold ring-1 ring-inset transition", stage === s.code ? "bg-brand-600 text-white ring-brand-600" : "bg-white ring-line-strong hover:bg-brand-50")}>{L(s.bn, s.en)}</button>)}</div>
              </div>
              <div>
                <p className="label">{L("কী সমস্যা দেখছেন?", "What are you seeing?")}</p>
                <div className="mb-3 flex flex-wrap gap-2">{SYMPTOMS.map(([b, e]) => <button key={b} onClick={() => setSymptom(b)} className={cn("min-h-[40px] rounded-full px-3.5 text-[15px] ring-1 ring-inset transition", symptom === b ? "bg-sun-50 font-semibold text-sun-700 ring-sun-500" : "bg-white ring-line-strong hover:bg-canvas")}>{L(b, e)}</button>)}</div>
                <textarea className="field min-h-[90px]" placeholder={L("নিজের ভাষায় লিখুন (ঐচ্ছিক)", "Describe in your own words (optional)")} value={symptom} onChange={(e) => setSymptom(e.target.value)} />
              </div>
              <div>
                <label className="label" htmlFor="pct">{L("ক্ষেতের কতটুকু আক্রান্ত?", "How much of the field is affected?")} <span className="ml-1 rounded-full bg-brand-50 px-2.5 py-0.5 font-display text-brand-700">{pctText}</span></label>
                <input id="pct" type="range" min={5} max={100} step={5} value={percent} onChange={(e) => setPercent(Number(e.target.value))} className="h-2 w-full cursor-pointer accent-[#178049]" />
                <div className="flex justify-between text-[13.5px] text-ink-mute"><span>{L("অল্প", "A little")}</span><span>{L("প্রায় সব", "Almost all")}</span></div>
              </div>
              <Button size="lg" disabled={!stage} onClick={() => setStep(2)} className="w-full sm:w-auto">{L("পরের ধাপ: ছবি", "Next: the photo")}<ArrowRight size={19} /></Button>
            </section>
          )}

          {step === 2 && (
            <section className="space-y-5">
              <h2 className="text-2xl">{L("আক্রান্ত অংশের ছবি দিন", "Add a photo of the affected part")}</h2>
              <div className="grid grid-cols-3 gap-2 text-center text-[13.5px] font-semibold">
                {[[Focus, "কাছ থেকে তুলুন", "Get close"], [Sun, "দিনের আলোয়", "Use daylight"], [Lightbulb, "ফোন স্থির রাখুন", "Hold steady"]].map(([I, b, e], i) => { const Ic = I as typeof Sun; return <div key={i} className="rounded-xl bg-sun-50 px-2 py-3 text-sun-700"><Ic className="mx-auto mb-1" size={22} />{L(b as string, e as string)}</div>; })}
              </div>
              {!img ? (
                <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={onDrop} className={cn("card grid place-items-center gap-4 border-2 border-dashed p-8 text-center transition", drag ? "border-brand-600 bg-brand-50" : "border-line-strong")}>
                  <span className="grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-brand-600"><UploadCloud size={30} /></span>
                  <p className="hidden text-ink-soft md:block">{L("ছবি এখানে টেনে আনুন, অথবা", "Drag a photo here, or")}</p>
                  <Button size="lg" onClick={() => camRef.current?.click()} loading={checking} className="w-full max-w-xs"><Camera size={22} />{L("ক্যামেরায় ছবি তুলুন", "Take a photo")}</Button>
                  <button onClick={() => galRef.current?.click()} className="inline-flex min-h-[44px] items-center gap-2 font-semibold text-brand-700 hover:underline"><ImagePlus size={19} />{L("গ্যালারি থেকে বেছে নিন", "Choose from gallery")}</button>
                  <p className="text-[13.5px] text-ink-mute">JPG · PNG · WebP · {L("সর্বোচ্চ ৫ MB", "max 5 MB")}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={img.dataUrl} alt={L("আপনার তোলা ছবি", "Your photo")} className="max-h-[380px] w-full rounded-card object-cover" />
                  {q && <p role="status" className={cn("flex items-start gap-2 rounded-ctl px-4 py-3 font-semibold ring-1 ring-inset", q.ok ? "bg-brand-50 text-brand-700 ring-brand-200" : "bg-clay-50 text-clay-700 ring-clay-100")}>{q.ok ? <CheckCircle2 className="mt-0.5 shrink-0" size={20} /> : <AlertTriangle className="mt-0.5 shrink-0" size={20} />}{L(q.bn, q.en)}</p>}
                  <div className="grid gap-2 sm:grid-cols-2">
                    <Button variant="secondary" onClick={() => { setImg(null); camRef.current?.click(); }}><RefreshCw size={19} />{L("আবার তুলুন", "Retake")}</Button>
                    <Button onClick={() => setStep(3)}>{img.q.status === "acceptable" ? L("এগিয়ে যান", "Continue") : L("তবুও এগিয়ে যান", "Continue anyway")}<ArrowRight size={19} /></Button>
                  </div>
                </div>
              )}
              {imgErr && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 ring-1 ring-inset ring-clay-100">{imgErr}</p>}
              <input ref={camRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ""; }} />
              <input ref={galRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ""; }} />
            </section>
          )}

          {step === 3 && crop && img && (
            <section className="space-y-5">
              <h2 className="text-2xl">{L("সব ঠিক আছে তো?", "Does everything look right?")}</h2>
              <div className="card flex gap-4 p-4 lg:hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img.dataUrl} alt="" className="h-24 w-24 shrink-0 rounded-xl object-cover" />
                <dl className="min-w-0 space-y-0.5 text-[15.5px]">
                  <div><dt className="inline text-ink-mute">{L("ফসল: ", "Crop: ")}</dt><dd className="inline font-semibold">{crop.emoji} {L(crop.name_bn, crop.name_en)}</dd></div>
                  <div><dt className="inline text-ink-mute">{L("পর্যায়: ", "Stage: ")}</dt><dd className="inline font-semibold">{stageObj ? L(stageObj.bn, stageObj.en) : "—"}</dd></div>
                  <div><dt className="inline text-ink-mute">{L("আক্রান্ত: ", "Affected: ")}</dt><dd className="inline font-semibold">{pctText}</dd></div>
                </dl>
              </div>
              <p className="flex items-start gap-2 rounded-ctl bg-sky-50 p-3.5 text-[15px] text-sky-700"><Lightbulb size={18} className="mt-0.5 shrink-0" />{L("এই ফলাফল সহায়ক পরামর্শ, চূড়ান্ত রোগনির্ণয় নয়। অনিশ্চিত হলে বিশেষজ্ঞের কাছে পাঠানো যাবে।", "The result is supportive advice, not a final diagnosis. Uncertain cases can go to an expert.")}</p>
              {err && <p role="alert" className="flex items-start gap-2 rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 ring-1 ring-inset ring-clay-100"><WifiOff size={18} className="mt-1 shrink-0" />{err}</p>}
              <Button size="lg" className="w-full" onClick={submit}>{L("ফলাফল দেখুন", "See the result")}<ArrowRight size={20} /></Button>
            </section>
          )}

          {step > 0 && <button onClick={() => setStep(step - 1)} className="mt-6 inline-flex min-h-[44px] items-center gap-2 font-semibold text-ink-soft hover:text-ink"><ArrowLeft size={18} />{L("পেছনে", "Back")}</button>}
        </div>

        {/* Live summary */}
        <aside className="card sticky top-6 hidden space-y-4 p-5 lg:block" aria-label={L("সারসংক্ষেপ", "Summary")}>
          <h3 className="text-lg">{L("আপনার তথ্য", "Your details")}</h3>
          {img ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={img.dataUrl} alt="" className="h-36 w-full rounded-xl object-cover" /> : <div className="grid h-36 place-items-center rounded-xl bg-canvas text-ink-mute"><Camera size={28} /></div>}
          <dl className="space-y-2 text-[15px]">
            {[[L("ফসল", "Crop"), crop ? `${crop.emoji} ${L(crop.name_bn, crop.name_en)}` : "—"], [L("পর্যায়", "Stage"), stageObj ? L(stageObj.bn, stageObj.en) : "—"], [L("সমস্যা", "Problem"), symptom || "—"], [L("আক্রান্ত", "Affected"), step > 0 ? pctText : "—"]].map(([k, v]) => <div key={k as string} className="flex justify-between gap-3 border-b border-line pb-2 last:border-0"><dt className="text-ink-mute">{k}</dt><dd className="max-w-[60%] text-right font-semibold">{v}</dd></div>)}
          </dl>
          <p className="text-[13px] text-ink-mute">{L("লেখা তথ্য স্বয়ংক্রিয়ভাবে খসড়া হিসেবে সংরক্ষিত হয়।", "Your details are saved automatically as a draft.")}</p>
        </aside>
      </div>
    </div>
  );
}
