"use client";
import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listGeo } from "@/lib/api";
import type { GeoItem } from "@/types";
import { ArrowLeft } from "lucide-react";
import { LangToggle, Logo } from "./ui";
import { ProductPreview } from "./preview";
import { useApp, useL } from "@/store/app";

export function AuthFrame({ title, sub, children }: { title: string; sub: string; children: ReactNode }) {
  const L = useL();
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <aside className="rows-texture relative hidden flex-col justify-between overflow-hidden bg-canopy p-10 text-white lg:flex">
        <div className="absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-brand-500/20 blur-3xl" aria-hidden />
        <Link href="/" className="relative"><Logo light /></Link>
        <div className="relative"><ProductPreview compact /></div>
        <p className="relative max-w-md font-display text-2xl font-bold leading-snug">{L("প্রতিটি কৃষকের হাতে একজন বিশ্বস্ত কৃষি পরামর্শদাতা।", "A trusted agricultural advisor in every farmer's hand.")}</p>
      </aside>
      <main id="main" className="flex flex-col px-5 py-6 md:px-14">
        <div className="mb-8 flex items-center justify-between">
          <Link href="/" className="inline-flex items-center gap-2 font-semibold text-ink-soft hover:text-ink"><ArrowLeft size={18} /><span className="lg:hidden"><Logo size={30} /></span><span className="hidden lg:inline">{L("হোম", "Home")}</span></Link>
          <LangToggle />
        </div>
        <div className="mx-auto w-full max-w-md flex-1">
          <h1 className="text-3xl">{title}</h1>
          <p className="mb-7 mt-1.5 text-ink-soft">{sub}</p>
          {children}
        </div>
      </main>
    </div>
  );
}

/** Counts down from `start` seconds; call `reset(n)` after each OTP send (backend `resend_after`). */
export function useCountdown(start = 0) {
  const [left, setLeft] = useState(start);
  useEffect(() => {
    if (left <= 0) return;
    const t = setTimeout(() => setLeft((v) => v - 1), 1000);
    return () => clearTimeout(t);
  }, [left]);
  return { left, reset: setLeft };
}

export function ResendButton({ left, onClick, busy }: { left: number; onClick: () => void; busy?: boolean }) {
  const L = useL();
  return (
    <button type="button" onClick={onClick} disabled={left > 0 || busy} className="block w-full text-center font-semibold text-brand-700 hover:underline disabled:cursor-not-allowed disabled:text-ink-mute disabled:no-underline">
      {left > 0 ? L(`${left} সেকেন্ড পর আবার কোড পাঠান`, `Resend code in ${left}s`) : L("আবার কোড পাঠান", "Resend code")}
    </button>
  );
}

function GeoSelect({ id, label, level, parent, value, onChange, disabled }: { id: string; label: string; level: "divisions" | "districts" | "upazilas" | "unions"; parent?: string; value: string; onChange: (v: string) => void; disabled?: boolean }) {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const enabled = level === "divisions" || !!parent;
  const q = useQuery({ queryKey: ["geo", level, parent], queryFn: () => listGeo(level, parent), enabled, staleTime: 3_600_000 });
  const items: GeoItem[] = q.data ?? [];
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <select id={id} className="field" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled || !enabled || q.isLoading}>
        <option value="">{q.isLoading ? L("লোড হচ্ছে…", "Loading…") : L("নির্বাচন করুন", "Select")}</option>
        {items.map((g) => <option key={g.id} value={g.id}>{lang === "bn" ? g.name_bn : g.name_en}</option>)}
      </select>
      {q.isError && <p role="alert" className="mt-1 text-[14px] text-clay-700">{L("তালিকা আনা যায়নি। আবার চেষ্টা করুন।", "Could not load the list. Try again.")}</p>}
    </div>
  );
}

export interface GeoValue { division_id: string; district_id: string; upazila_id: string; union_id: string }
export const EMPTY_GEO: GeoValue = { division_id: "", district_id: "", upazila_id: "", union_id: "" };

/** Division → District → Upazila → Union; changing a parent resets its children. */
export function GeoCascade({ value, onChange }: { value: GeoValue; onChange: (v: GeoValue) => void }) {
  const L = useL();
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <GeoSelect id="g-div" label={L("বিভাগ", "Division")} level="divisions" value={value.division_id} onChange={(v) => onChange({ ...EMPTY_GEO, division_id: v })} />
      <GeoSelect id="g-dis" label={L("জেলা", "District")} level="districts" parent={value.division_id} value={value.district_id} onChange={(v) => onChange({ ...value, district_id: v, upazila_id: "", union_id: "" })} />
      <GeoSelect id="g-upa" label={L("উপজেলা", "Upazila")} level="upazilas" parent={value.district_id} value={value.upazila_id} onChange={(v) => onChange({ ...value, upazila_id: v, union_id: "" })} />
      <GeoSelect id="g-uni" label={L("ইউনিয়ন", "Union")} level="unions" parent={value.upazila_id} value={value.union_id} onChange={(v) => onChange({ ...value, union_id: v })} />
    </div>
  );
}
