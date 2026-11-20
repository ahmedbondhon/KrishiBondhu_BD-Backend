"use client";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { ConfidenceBadge, StatusBadge } from "./ui";
import { CROP_COLOR } from "@/lib/analytics";
import { timeAgo } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { DiagnosisCase } from "@/types";

export function CaseRow({ c, href }: { c: DiagnosisCase; href: string }) {
  const lang = useApp((s) => s.lang);
  const L = useL();
  return (
    <Link href={href} className="card group flex items-center gap-3.5 p-3 transition hover:shadow-pop md:p-3.5">
      <span className="relative shrink-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={c.image_url} alt="" className="h-[72px] w-[72px] rounded-xl object-cover" />
        <span className="absolute -bottom-1 -right-1 grid h-7 w-7 place-items-center rounded-full bg-white text-[15px] shadow-card" style={{ boxShadow: `0 0 0 2px ${CROP_COLOR[c.crop.code]}` }}>{c.crop.emoji}</span>
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-[1.05rem] font-bold">{c.diagnosis.issue?.name_bn ?? L("নিশ্চিত শনাক্ত হয়নি", "Not identified")}</p>
        <p className="text-[13.5px] text-ink-mute">{L(c.crop.name_bn, c.crop.name_en)} · {c.growth_stage} · {timeAgo(c.created_at, lang)}</p>
        <div className="mt-1.5 flex flex-wrap gap-1.5"><StatusBadge status={c.status} /><span className="hidden sm:inline-flex"><ConfidenceBadge level={c.diagnosis.confidence_level} /></span></div>
      </div>
      <ChevronRight className="shrink-0 text-ink-mute transition group-hover:translate-x-0.5" />
    </Link>
  );
}
