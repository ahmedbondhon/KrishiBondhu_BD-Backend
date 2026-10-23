"use client";

import React, { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Stethoscope,
  CheckCircle,
  AlertCircle,
  Clock,
  Send,
  UserCheck,
} from "lucide-react";

export default function ExpertQueue() {
  const { cases, updateCaseStatus, language } = useAppStore();
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [prescriptionNote, setPrescriptionNote] = useState("");
  const isBn = language === "bn";

  const pendingCases = cases.filter(
    (c) => c.status === "pending_expert" || c.status === "analyzed"
  );

  const selectedCase =
    cases.find((c) => c.id === selectedCaseId) || pendingCases[0];

  const handleApprove = () => {
    if (!selectedCase) return;
    updateCaseStatus(
      selectedCase.id,
      "reviewed",
      prescriptionNote ||
        "কৃষিবিদ দ্বারা সরাসরি পর্যবেক্ষণ ও কার্যকর চিকিৎসা সুপারিশ অনুমোদন করা হলো।"
    );
    setPrescriptionNote("");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <UserCheck className="h-5 w-5 text-primary" />
            {isBn ? "কৃষিবিদ বিশেষজ্ঞ পোর্টাল" : "Agronomist Expert Review"}
          </h2>
          <p className="text-xs text-muted-foreground">
            {isBn
              ? "মাঠ পর্যায়ের কৃষক ও AI মডেলের যাচাই-বাছাই কিউ"
              : "Review queue for low-confidence or farmer requested cases"}
          </p>
        </div>
        <Badge variant="warning" className="text-xs">
          {pendingCases.length}{" "}
          {isBn ? "টি কেস অপেক্ষমাণ" : "Pending Cases"}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left List */}
        <div className="lg:col-span-5 space-y-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {isBn ? "পর্যালোচনার তালিকা" : "Review Queue"}
          </p>

          {pendingCases.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-dashed border-border bg-card/40">
              <CheckCircle className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-semibold">
                {isBn ? "কোনো মুলতুবি কেস নেই!" : "No pending cases!"}
              </p>
            </div>
          ) : (
            pendingCases.map((c) => {
              const isSelected = selectedCase?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-primary/10 border-primary shadow-sm"
                      : "bg-card hover:bg-card/80 border-border/70"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-xs font-mono font-bold text-primary">
                        {c.caseNumber}
                      </span>
                      <h4 className="text-sm font-semibold text-foreground">
                        {c.cropNameBn} — {c.diseaseNameBn}
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {c.createdAt}
                      </p>
                    </div>
                    <Badge
                      variant={
                        c.status === "pending_expert" ? "warning" : "default"
                      }
                      className="text-[10px]"
                    >
                      {Math.round(c.confidence * 100)}%
                    </Badge>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Active Case Editor */}
        <div className="lg:col-span-7">
          {selectedCase ? (
            <Card className="border border-border">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="font-mono">
                    {selectedCase.caseNumber}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {selectedCase.createdAt}
                  </span>
                </div>
                <CardTitle className="text-lg pt-1">
                  {selectedCase.cropNameBn}: {selectedCase.diseaseNameBn}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4 items-center p-3 rounded-lg bg-muted/40 border border-border/60">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={selectedCase.imageUrl}
                    alt="Leaf"
                    className="h-20 w-20 rounded-lg object-cover border border-border"
                  />
                  <div className="text-xs space-y-1">
                    <p className="font-medium text-foreground">
                      AI প্রস্তাবিত চিকিৎসা:
                    </p>
                    <p className="text-muted-foreground line-clamp-2">
                      {selectedCase.treatmentBn}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-foreground">
                    {isBn
                      ? "বিশেষজ্ঞ মতামত / সংশোধিত প্রেসক্রিপশন লিখুন:"
                      : "Agronomist Prescription Notes:"}
                  </label>
                  <textarea
                    rows={3}
                    value={prescriptionNote}
                    onChange={(e) => setPrescriptionNote(e.target.value)}
                    placeholder={
                      isBn
                        ? "কৃষকের জন্য সুনির্দিষ্ট পরামর্শ ও নির্দেশনা দিন..."
                        : "Enter customized field advice..."
                    }
                    className="w-full text-xs p-3 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="emerald"
                    onClick={handleApprove}
                    className="gap-1.5 text-xs font-semibold"
                  >
                    <CheckCircle className="h-4 w-4" />
                    {isBn ? "যাচাই সম্পন্ন ও অনুমোদন করুন" : "Verify & Approve"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="p-12 text-center text-muted-foreground border rounded-xl">
              {isBn
                ? "তালিকা থেকে যেকোনো কেস নির্বাচন করুন"
                : "Select a case to inspect"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
