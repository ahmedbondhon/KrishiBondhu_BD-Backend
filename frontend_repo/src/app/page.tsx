"use client";
import Link from "next/link";
import { ArrowRight, Camera, CheckCircle2, ChevronDown, Cloud, Headphones, Lock, ScanSearch, ShieldCheck, Stethoscope, Store, UserCheck, WifiOff, Wrench, Sprout } from "lucide-react";
import { Badge, LangToggle, LinkButton, Logo } from "@/components/ui";
import { ProductPreview } from "@/components/preview";
import { CROPS } from "@/lib/data";
import { useApp, useL } from "@/store/app";

export default function Landing() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const home = user ? (user.role === "expert" ? "/expert/dashboard" : user.role === "admin" || user.role === "technical_admin" ? "/admin/dashboard" : "/farmer/dashboard") : "/register";
  const n = (i: number) => (lang === "bn" ? "১২৩৪"[i - 1] : String(i));

  return (
    <div>
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-canopy/90 text-white backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Logo light />
          <nav className="hidden items-center gap-1 md:flex" aria-label="Sections">
            {[["#how", L("কীভাবে কাজ করে", "How it works")], ["#features", L("সুবিধা", "Features")], ["#portals", L("পোর্টাল", "Portals")], ["#faq", L("প্রশ্ন", "FAQ")]].map(([h, t]) => <a key={h} href={h} className="rounded-ctl px-3 py-2 font-semibold text-brand-100 hover:bg-white/10 hover:text-white">{t}</a>)}
          </nav>
          <div className="flex items-center gap-2">
            <LangToggle dark />
            <Link href="/login" className="hidden min-h-[40px] items-center rounded-ctl px-3.5 font-semibold hover:bg-white/10 sm:inline-flex">{L("লগইন", "Log in")}</Link>
            <LinkButton href={home} variant="accent" size="sm">{L("শুরু করুন", "Get started")}</LinkButton>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="rows-texture relative overflow-hidden bg-canopy text-white">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-brand-500/20 blur-3xl" aria-hidden />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-14 md:grid-cols-[1.1fr_0.9fr] md:pb-28 md:pt-20">
          <div>
            <Badge tone="dark" icon={<Sprout size={14} className="text-lime-400" />}>{L("আলু · টমেটো · মরিচ", "Potato · Tomato · Chili")}</Badge>
            <h1 className="mt-5 text-[2.5rem] font-extrabold leading-[1.12] md:text-[3.6rem]">{L("এক ছবিতে বুঝে নিন ফসলের সমস্যা", "Understand your crop's problem from one photo")}</h1>
            <p className="mt-5 max-w-xl text-[18px] text-brand-100">{L("পাতার ছবি তুলুন, বাংলায় সহজ পরামর্শ শুনুন। সিস্টেম নিশ্চিত না হলে কৃষি বিশেষজ্ঞ আপনার ছবি দেখে উত্তর দেবেন।", "Take a leaf photo and hear simple advice in Bangla. When the system is unsure, an agricultural expert reviews your photo and replies.")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <LinkButton href={home} variant="accent" size="lg"><Camera size={22} />{L("ছবি তুলে পরীক্ষা করুন", "Check my crop")}</LinkButton>
              <LinkButton href="/login" variant="secondary" size="lg" className="!bg-transparent !text-white !ring-white/30 hover:!bg-white/10">{L("ডেমো দেখুন", "Try the demo")}</LinkButton>
            </div>
            <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-[15px] text-brand-100">
              {[L("বিনামূল্যে", "Free to use"), L("মোবাইল ব্রাউজারেই চলে", "Runs in a mobile browser"), L("ধীর নেটওয়ার্কেও কাজ করে", "Built for slow networks")].map((t) => <li key={t} className="flex items-center gap-1.5"><CheckCircle2 size={16} className="text-lime-400" />{t}</li>)}
            </ul>
          </div>
          <ProductPreview />
        </div>
        <div className="absolute inset-x-0 bottom-0 h-10 rounded-t-[32px] bg-canvas" aria-hidden />
      </section>

      {/* How it works — a true sequence */}
      <section id="how" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16">
        <h2 className="max-w-2xl text-3xl md:text-4xl">{L("চার ধাপে সমাধান", "From photo to plan in four steps")}</h2>
        <ol className="mt-9 grid gap-4 md:grid-cols-4">
          {[
            [Camera, "ছবি তুলুন", "Take a photo", "ফসল বেছে আক্রান্ত অংশের কাছ থেকে ছবি তুলুন।", "Pick the crop and photograph the affected part up close."],
            [ScanSearch, "মান যাচাই", "Quality check", "ঝাপসা বা অন্ধকার হলে সাথে সাথে আবার তুলতে বলা হয়।", "Blurry or dark photos are flagged so you can retake them."],
            [Headphones, "বাংলায় শুনুন", "Hear the advice", "আজ কী করবেন আর কী করবেন না — লেখায় ও কণ্ঠে।", "What to do and what to avoid today, in text and voice."],
            [UserCheck, "বিশেষজ্ঞের উত্তর", "Expert reply", "অনিশ্চিত বা গুরুতর হলে কৃষি কর্মকর্তা ছবি দেখে জানাবেন।", "If it is uncertain or serious, an officer reviews and replies."],
          ].map(([I, tb, te, db, de], i) => {
            const Ic = I as typeof Camera;
            return (
              <li key={i} className="card relative p-5">
                <span className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-600 text-white"><Ic size={22} /></span><span className="font-display text-2xl font-extrabold text-brand-200">{n(i + 1)}</span></span>
                <h3 className="mt-4 text-xl">{L(tb as string, te as string)}</h3>
                <p className="mt-1 text-ink-soft">{L(db as string, de as string)}</p>
              </li>
            );
          })}
        </ol>
      </section>

      {/* Features bento */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 pb-16">
        <h2 className="max-w-2xl text-3xl md:text-4xl">{L("মাঠের বাস্তবতা মাথায় রেখে বানানো", "Designed around real field conditions")}</h2>
        <div className="mt-9 grid gap-4 md:grid-cols-6">
          <div className="card rows-texture relative overflow-hidden bg-canopy p-6 text-white md:col-span-4">
            <ShieldCheck className="text-lime-400" size={28} />
            <h3 className="mt-4 text-2xl">{L("ওষুধ আন্দাজ করে বলা হয় না", "No guessing about pesticides")}</h3>
            <p className="mt-2 max-w-md text-brand-100">{L("প্রতিটি পরামর্শ বিশেষজ্ঞের যাচাই করা। সিস্টেম নিজে থেকে কীটনাশকের নাম বা মাত্রা বানায় না। নিশ্চিত না হলে সেটাই বলে।", "Every piece of advice is expert-reviewed. The system never invents pesticide names or doses, and says so when it is not sure.")}</p>
            <div className="mt-5 flex flex-wrap gap-2"><Badge tone="dark">{L("নিশ্চয়তা কম → বিশেষজ্ঞ", "Low confidence → expert")}</Badge><Badge tone="dark">{L("অনুমোদিত তথ্য ভান্ডার", "Approved content only")}</Badge></div>
          </div>
          <div className="card p-6 md:col-span-2"><WifiOff className="text-sky-500" size={26} /><h3 className="mt-4 text-xl">{L("নেটওয়ার্ক দুর্বল? সমস্যা নেই", "Weak network? Fine")}</h3><p className="mt-1 text-ink-soft">{L("ছবি ছোট করে পাঠানো হয়, আর লেখা তথ্য খসড়া হিসেবে সংরক্ষিত থাকে।", "Photos are compressed before upload and your details are kept as a draft.")}</p></div>
          <div className="card p-6 md:col-span-2"><Headphones className="text-brand-600" size={26} /><h3 className="mt-4 text-xl">{L("পড়তে না পারলেও চলবে", "No need to read")}</h3><p className="mt-1 text-ink-soft">{L("পরামর্শ বাংলায় শোনা যায়। বড় বোতাম, সহজ ভাষা।", "Advice can be heard in Bangla. Big buttons, plain language.")}</p></div>
          <div className="card p-6 md:col-span-2"><Stethoscope className="text-clay-500" size={26} /><h3 className="mt-4 text-xl">{L("বিশেষজ্ঞ সবসময় নিয়ন্ত্রণে", "Experts stay in control")}</h3><p className="mt-1 text-ink-soft">{L("বিশেষজ্ঞ সিস্টেমের ফলাফল মেনে নিতে, সংশোধন বা বাতিল করতে পারেন।", "Experts can approve, correct or reject the system's result.")}</p></div>
          <div className="card p-6 md:col-span-2"><Lock className="text-ink-soft" size={26} /><h3 className="mt-4 text-xl">{L("আপনার তথ্য আপনার", "Your data stays yours")}</h3><p className="mt-1 text-ink-soft">{L("অনুমতি ছাড়া ছবি ও তথ্য ব্যবহার হয় না। যেকোনো সময় মুছে ফেলা যায়।", "Photos and data are used only with consent, and can be deleted any time.")}</p></div>
        </div>
      </section>

      {/* Portals */}
      <section id="portals" className="border-y border-line bg-white">
        <div className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16">
          <h2 className="max-w-2xl text-3xl md:text-4xl">{L("প্রত্যেকের জন্য আলাদা কাজের জায়গা", "A workspace for every role")}</h2>
          <div className="mt-9 grid gap-4 md:grid-cols-3">
            {[
              { I: Sprout, t: "কৃষক", e: "Farmers", d: "ছবি তুলে পরীক্ষা, বাংলা পরামর্শ, ইতিহাস ও খামারের তথ্য।", de: "Photo checks, Bangla advice, history and farm records.", tone: "bg-brand-50 text-brand-700" },
              { I: Stethoscope, t: "কৃষি বিশেষজ্ঞ", e: "Experts", d: "জরুরি কেস আগে দেখা, ছবি যাচাই করে বাংলায় উত্তর।", de: "Triage urgent cases, review photos and reply in Bangla.", tone: "bg-sky-50 text-sky-700" },
              { I: Wrench, t: "অ্যাডমিন", e: "Admins", d: "পরামর্শ ভান্ডার অনুমোদন, ব্যবহারকারী ও মান পর্যবেক্ষণ।", de: "Approve advisory content, manage users and watch quality.", tone: "bg-sun-50 text-sun-700" },
            ].map((p) => (
              <div key={p.t} className="rounded-card border border-line bg-canvas p-6">
                <span className={`grid h-11 w-11 place-items-center rounded-xl ${p.tone}`}><p.I size={22} /></span>
                <h3 className="mt-4 text-xl">{L(p.t, p.e)}</h3><p className="mt-1 text-ink-soft">{L(p.d, p.de)}</p>
                <Link href="/login" className="mt-4 inline-flex items-center gap-1.5 font-semibold text-brand-700 hover:underline">{L("ডেমো খুলুন", "Open the demo")}<ArrowRight size={16} /></Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Crops + roadmap */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid gap-10 md:grid-cols-2">
          <div>
            <h2 className="text-3xl md:text-4xl">{L("এখন যে ফসল দেখা যায়", "Crops covered today")}</h2>
            <div className="mt-6 flex flex-wrap gap-3">{CROPS.map((c) => <span key={c.id} className="card inline-flex items-center gap-3 px-5 py-3 text-xl font-bold"><span className="text-3xl">{c.emoji}</span>{L(c.name_bn, c.name_en)}</span>)}</div>
          </div>
          <div>
            <h2 className="text-3xl md:text-4xl">{L("পরে যা আসছে", "What comes next")}</h2>
            <ul className="mt-6 space-y-3">
              {[{ I: Cloud, bn: "আবহাওয়া ও বন্যা সতর্কতা", en: "Weather and flood alerts" }, { I: Store, bn: "বাজারদর ও দলগত বিক্রি", en: "Market prices and group selling" }].map(({ I, bn, en }) => (
                <li key={bn} className="card flex items-center gap-3 p-4"><span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100 text-slate-500"><I size={20} /></span><span className="flex-1 font-semibold">{L(bn, en)}</span><Badge tone="neutral" icon={<Lock size={12} />}>{L("শীঘ্রই", "Soon")}</Badge></li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-3xl scroll-mt-20 px-4 pb-16">
        <h2 className="text-3xl md:text-4xl">{L("সাধারণ প্রশ্ন", "Common questions")}</h2>
        <div className="mt-6 space-y-3">
          {[
            ["এটা কি রোগের চূড়ান্ত নির্ণয়?", "Is this a final diagnosis?", "না। এটি সহায়ক পরামর্শ। অনিশ্চিত বা গুরুতর হলে কৃষি বিশেষজ্ঞ ছবি দেখে চূড়ান্ত মত দেন।", "No. It is supportive advice. For uncertain or serious cases an expert reviews the photo and gives the final view."],
            ["ইন্টারনেট ধীর হলে কী হবে?", "What if my internet is slow?", "ছবি ছোট করে পাঠানো হয় এবং আপনার লেখা তথ্য খসড়া হিসেবে সংরক্ষিত থাকে, তাই আবার সব লিখতে হয় না।", "Photos are compressed and your details are saved as a draft, so you do not retype everything."],
            ["কীটনাশকের নাম ও মাত্রা কি বলা হবে?", "Will it tell me which pesticide and how much?", "সিস্টেম নিজে থেকে নাম বা মাত্রা বলে না। শুধু অনুমোদিত পরামর্শ ও বিশেষজ্ঞের নির্দেশনা দেখানো হয়।", "The system never invents names or doses. Only approved advice and expert guidance are shown."],
            ["আমার ছবি কারা দেখতে পারে?", "Who can see my photos?", "শুধু আপনি এবং আপনার কেস দেখা অনুমোদিত বিশেষজ্ঞ। গবেষণায় ব্যবহারের জন্য আলাদা সম্মতি লাগে।", "Only you and the expert assigned to your case. Using them for research needs separate consent."],
          ].map(([qb, qe, ab, ae]) => (
            <details key={qb} className="card group p-5 open:shadow-pop">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 font-display text-lg font-bold">{L(qb, qe)}<ChevronDown className="shrink-0 transition group-open:rotate-180" /></summary>
              <p className="mt-3 text-ink-soft">{L(ab, ae)}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="rows-texture rounded-sheet bg-canopy p-8 text-center text-white md:p-14">
          <h2 className="mx-auto max-w-2xl text-3xl md:text-4xl">{L("আজই আপনার ক্ষেতের একটি ছবি দিন", "Send a photo of your field today")}</h2>
          <p className="mx-auto mt-3 max-w-xl text-brand-100">{L("একাউন্ট খুলতে এক মিনিটের মতো লাগে।", "Creating an account takes about a minute.")}</p>
          <div className="mt-7 flex flex-wrap justify-center gap-3"><LinkButton href={home} variant="accent" size="lg"><Camera size={22} />{L("বিনামূল্যে শুরু করুন", "Start for free")}</LinkButton></div>
        </div>
      </section>

      <footer className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 md:flex-row md:items-center md:justify-between">
          <Logo />
          <p className="max-w-xl text-[14px] text-ink-mute">{L("কৃষিবন্ধু একটি AI-সহায়ক পরামর্শ প্ল্যাটফর্ম। এটি যোগ্য কৃষি বিশেষজ্ঞের পরামর্শের বিকল্প নয়।", "KrishiBondhu is an AI-supported advisory platform. It does not replace qualified agricultural consultation.")}</p>
        </div>
      </footer>
    </div>
  );
}
