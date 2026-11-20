"use client";

import React from "react";
import { useAppStore } from "@/store/useAppStore";
import { Sparkles, ScanLine, ShieldCheck, HeartPulse } from "lucide-react";

export default function StatsBanner() {
  const language = useAppStore((state) => state.language);
  const cases = useAppStore((state) => state.cases);
  const isBn = language === "bn";

  const stats = [
    {
      icon: ScanLine,
      title: isBn ? "ডায়াগনসিস সম্পন্ন" : "Diagnosed Cases",
      value: `${cases.length.toLocaleString("bn-BD")} টি`,
      sub: isBn ? "আপনার সংরক্ষিত কেস" : "Your recorded cases",
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      icon: Sparkles,
      title: isBn ? "AI ভিশন ইঞ্জিন" : "AI Vision Engine",
      value: "Gemini 2.5",
      sub: isBn ? "রিয়েল-টাইম রোগ শনাক্তকরণ" : "Real-time crop vision",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      icon: ShieldCheck,
      title: isBn ? "বিশেষজ্ঞ সহায়তা" : "Agronomist Advisory",
      value: isBn ? "অনুমোদিত" : "Verified",
      sub: isBn ? "DAE কৃষি কর্মকর্তা যাচাই" : "DAE verified protocols",
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
    {
      icon: HeartPulse,
      title: isBn ? "কৃষি হটলাইন" : "National Hotline",
      value: "১৬১২৩",
      sub: isBn ? "টোল-ফ্রি কৃষি কল সেন্টার" : "Toll-free agricultural support",
      color: "text-purple-500",
      bg: "bg-purple-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 my-6">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <div
            key={i}
            className="p-4 rounded-xl border border-border/80 bg-card/60 backdrop-blur hover:bg-card hover:shadow-md hover:border-emerald-500/30 transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div
                className={`h-10 w-10 rounded-lg flex items-center justify-center ${stat.bg} ${stat.color}`}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">
                  {stat.title}
                </p>
                <p className="text-lg font-bold tracking-tight text-foreground">
                  {stat.value}
                </p>
                <p className="text-[11px] text-muted-foreground/80">{stat.sub}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
