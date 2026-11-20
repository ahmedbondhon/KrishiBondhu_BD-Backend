"use client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Cloud, Languages, Lock, LogOut, Phone, ShieldCheck, Store, Trash2 } from "lucide-react";
import { getSupport, logout, updateLanguage } from "@/lib/api";
import { Avatar, Badge, Button, PageHeader } from "@/components/ui";
import { flags } from "@/lib/flags";
import { useApp, useL } from "@/store/app";

export default function More() {
  const L = useL();
  const { lang, setLang, user, setUser } = useApp();
  const router = useRouter();
  const { data: help } = useQuery({ queryKey: ["support"], queryFn: getSupport, staleTime: 3_600_000 });
  const signOut = async (all = false) => { await logout(all); setUser(null); router.push("/"); };
  const switchLang = () => { const n = lang === "bn" ? "en" : "bn"; setLang(n); updateLanguage(n); };
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <PageHeader title={L("আরও", "More")} />
      <section className="card flex flex-wrap items-center gap-4 p-5">
        <Avatar name={user?.name ?? "?"} size={56} />
        <div className="min-w-0 flex-1"><p className="font-display text-xl font-bold">{user?.name}</p><p className="text-ink-soft">{user?.phone}{user?.district ? ` · ${user.district}` : ""}</p></div>
        <div className="flex flex-wrap gap-2">
          <Link href="/farmer/profile" className="inline-flex min-h-[44px] items-center rounded-ctl border border-line-strong px-4 font-semibold text-brand-700 hover:bg-brand-50">{L("প্রোফাইল দেখুন ও বদলান", "View and edit profile")}</Link>
          <Button variant="secondary" size="sm" onClick={switchLang}><Languages size={17} />{lang === "bn" ? "English" : "বাংলা"}</Button>
          <Button variant="secondary" size="sm" onClick={() => signOut()}><LogOut size={17} />{L("লগআউট", "Log out")}</Button>
        </div>
      </section>

      {help && (
        <section className="card space-y-3 p-5">
          <h2 className="flex items-center gap-2 text-xl"><Phone className="text-brand-600" />{L(help.title_bn, help.title_en)}</h2>
          <p className="text-ink-soft">{L(help.instructions_bn, help.instructions_en)}</p>
          <p className="text-[14px] text-ink-mute">{L(help.available_hours_bn, help.available_hours_en)}</p>
          <div className="flex flex-wrap gap-2">
            <a href={`tel:${help.helpline_number}`} className="inline-flex min-h-[48px] items-center gap-2 rounded-ctl bg-brand-600 px-5 font-bold text-white hover:bg-brand-700"><Phone size={18} />{L("কল করুন", "Call")}: {help.helpline_number}</a>
            <a href={`mailto:${help.support_email}`} className="inline-flex min-h-[48px] items-center rounded-ctl border border-line-strong px-5 font-semibold text-ink-soft hover:bg-brand-50">{help.support_email}</a>
          </div>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-xl">{L("আসছে শীঘ্রই", "Coming soon")}</h2>
        {[
          { I: Cloud, on: flags.climate, bn: "আবহাওয়া ও বন্যা সতর্কতা", en: "Weather and flood alerts", db: "ভারী বৃষ্টির আগে জানাবে: সার দেওয়া পিছিয়ে দিন, নালা পরিষ্কার করুন।", de: "Get warned before heavy rain: delay fertiliser, clear drainage." },
          { I: Store, on: flags.market, bn: "বাজারদর ও দলগত বিক্রি", en: "Market prices and group selling", db: "কাছের বাজারের দাম তুলনা করে ভালো দামে বিক্রির সুযোগ।", de: "Compare nearby market prices and find better ways to sell." },
        ].map(({ I, on, bn, en, db, de }) => (
          <div key={bn} className="card flex items-start gap-3.5 p-4">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-500"><I size={22} /></span>
            <div className="flex-1"><p className="font-display font-bold">{L(bn, en)}</p><p className="text-ink-soft">{L(db, de)}</p></div>
            {!on && <Badge tone="neutral" icon={<Lock size={12} />}>{L("বন্ধ", "Off")}</Badge>}
          </div>
        ))}
      </section>

      <section className="card space-y-3 p-5">
        <h2 className="flex items-center gap-2 text-xl"><ShieldCheck className="text-brand-600" />{L("গোপনীয়তা", "Privacy")}</h2>
        <p className="text-ink-soft">{L("আপনার ছবি ও তথ্য শুধু আপনি ও অনুমোদিত বিশেষজ্ঞ দেখতে পারেন। যেকোনো সময় একাউন্ট ও তথ্য মুছে ফেলার অনুরোধ করা যায়।", "Only you and authorised experts can see your photos and data. You can request deletion of your account and data at any time.")}</p>
        <Button variant="secondary" className="!text-clay-600"><Trash2 size={18} />{L("একাউন্ট মোছার অনুরোধ", "Request account deletion")}</Button>
        <Button variant="secondary" onClick={() => signOut(true)}><LogOut size={18} />{L("সব ডিভাইস থেকে লগআউট", "Log out of all devices")}</Button>
      </section>
    </div>
  );
}
