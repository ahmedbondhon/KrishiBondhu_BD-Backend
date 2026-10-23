"use client";

import React from "react";
import { useCasesHistoryQuery } from "@/hooks/useDiagnosis";
import { useAppStore, DiagnosisCase } from "@/store/useAppStore";
import { Badge } from "@/components/ui/badge";
import { History, CheckCircle2, AlertCircle, ArrowUpRight } from "lucide-react";

export default function CaseHistory() {
  const { data: cases } = useCasesHistoryQuery();
  const { setActiveCase, language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-foreground flex items-center gap-2">
          <History className="h-4 w-4 text-primary" />
          {isBn ? "সাম্প্রতিক ডায়াগনসিস ইতিহাস" : "Recent Diagnoses"}
        </h3>
        <span className="text-xs text-muted-foreground">
          {cases?.length || 0} {isBn ? "টি রেকর্ড" : "records"}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {cases?.map((c) => {
          return (
            <div
              key={c.id}
              onClick={() => setActiveCase(c)}
              className="p-3.5 rounded-xl border border-border/80 bg-card/60 hover:bg-card hover:shadow-sm hover:border-emerald-500/40 cursor-pointer transition-all flex items-center gap-3 group"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={c.imageUrl}
                alt={c.cropName}
                className="h-14 w-14 rounded-lg object-cover border border-border shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="font-mono text-[10px] text-muted-foreground font-semibold">
                    {c.caseNumber}
                  </span>
                  <span className="text-[10px] text-muted-foreground">•</span>
                  <span className="text-[10px] text-muted-foreground">
                    {c.createdAt}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-foreground truncate group-hover:text-primary transition-colors">
                  {c.cropNameBn} — {c.diseaseNameBn}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant={
                      c.status === "reviewed"
                        ? "success"
                        : c.status === "pending_expert"
                        ? "warning"
                        : "default"
                    }
                    className="text-[10px] py-0 px-2 h-4"
                  >
                    {c.status === "reviewed"
                      ? isBn
                        ? "অনুমোদিত"
                        : "Approved"
                      : c.status === "pending_expert"
                      ? isBn
                        ? "বিশেষজ্ঞ কিউ"
                        : "In Queue"
                      : isBn
                      ? "AI প্রস্তুত"
                      : "AI Ready"}
                  </Badge>
                  <span className="text-[11px] font-medium text-muted-foreground">
                    {Math.round(c.confidence * 100)}%
                  </span>
                </div>
              </div>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
            </div>
          );
        })}
      </div>
    </div>
  );
}
