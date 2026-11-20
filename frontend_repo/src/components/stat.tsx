import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Sparkline } from "./charts";

const tone = {
  brand: ["bg-brand-50 text-brand-700", "#1F9D5C"],
  sun: ["bg-sun-50 text-sun-700", "#D99A00"],
  clay: ["bg-clay-50 text-clay-700", "#D9472F"],
  sky: ["bg-sky-50 text-sky-700", "#2F74C8"],
} as const;

export function Stat({ label, value, hint, icon, tone: t = "brand", spark, className }: { label: string; value: ReactNode; hint?: ReactNode; icon?: ReactNode; tone?: keyof typeof tone; spark?: number[]; className?: string }) {
  return (
    <div className={cn("card flex flex-col justify-between gap-3 p-4 md:p-5", className)}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[14.5px] font-semibold text-ink-soft">{label}</p>
        {icon && <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-[10px]", tone[t][0])}>{icon}</span>}
      </div>
      <div className="flex items-end justify-between gap-2">
        <div><p className="font-display text-[2rem] font-extrabold leading-none tabular-nums">{value}</p><p className="mt-1.5 min-h-[1.5rem] text-[13.5px] leading-snug text-ink-mute">{hint ?? "\u00A0"}</p></div>
        {spark && <Sparkline data={spark} color={tone[t][1]} />}
      </div>
    </div>
  );
}
