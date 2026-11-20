"use client";
import { Check, Headphones, ShieldCheck } from "lucide-react";
import { Gauge } from "./charts";
import { leafPlaceholder } from "@/lib/data";
import { useL } from "@/store/app";

/** Static product mock used on the landing and auth screens. */
export function ProductPreview({ compact = false }: { compact?: boolean }) {
  const L = useL();
  return (
    <div className="relative mx-auto w-full max-w-[400px] text-ink">
      <div className="card overflow-hidden shadow-pop">
        <div className="relative h-36">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={leafPlaceholder(100, 5)} alt="" className="h-full w-full object-cover" />
          <span className="absolute left-3 top-3 rounded-full bg-white/95 px-2.5 py-0.5 text-[13px] font-semibold">🥔 {L("আলু", "Potato")}</span>
        </div>
        <div className="space-y-3 p-4">
          <div>
            <p className="text-[13px] text-ink-mute">{L("সম্ভাব্য সমস্যা", "Likely problem")}</p>
            <p className="font-display text-xl font-bold leading-tight">{L("আলুর লেট ব্লাইট (নাবি ধসা)", "Potato late blight")}</p>
          </div>
          <div className="flex items-center gap-3 rounded-xl bg-canvas p-3">
            <div className="w-[104px] shrink-0"><Gauge score={0.86} level="high" /></div>
            <p className="text-[14px] leading-snug text-ink-soft">{L("উচ্চ নিশ্চয়তা। আজই আক্রান্ত অংশ সরান।", "High confidence. Remove affected parts today.")}</p>
          </div>
          {!compact && (
            <ul className="space-y-1.5 text-[14.5px]">
              {[L("আক্রান্ত পাতা তুলে মাটিতে পুঁতুন", "Bury the affected leaves"), L("কুয়াশায় সেচ বন্ধ রাখুন", "Pause irrigation in fog")].map((t) => (
                <li key={t} className="flex items-start gap-2"><span className="mt-1 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-brand-600 text-white"><Check size={11} strokeWidth={3.5} /></span>{t}</li>
              ))}
            </ul>
          )}
          <div className="flex items-center gap-2 rounded-ctl bg-canopy px-3 py-2 text-[14px] font-semibold text-white"><Headphones size={16} className="text-lime-400" />{L("বাংলায় শুনুন", "Listen in Bangla")}</div>
        </div>
      </div>
      <div className="absolute -left-4 top-24 hidden items-center gap-2 rounded-full bg-white px-3.5 py-2 text-[13.5px] font-semibold shadow-pop sm:flex md:-left-10"><ShieldCheck size={16} className="text-brand-600" />{L("বিশেষজ্ঞ-যাচাইকৃত", "Expert-verified")}</div>
    </div>
  );
}
