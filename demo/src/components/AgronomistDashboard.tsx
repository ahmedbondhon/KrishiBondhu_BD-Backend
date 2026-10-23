"use client";

import React, { useState } from "react";
import { useAppStore, DiagnosisCase } from "@/store/useAppStore";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import DiagnosisResult from "@/components/DiagnosisResult";
import CaseHistory from "@/components/CaseHistory";
import {
  UserCheck,
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Send,
  FileCheck2,
  Calendar,
  Sparkles,
  ClipboardList,
  History,
} from "lucide-react";

export default function AgronomistDashboard() {
  const { cases, updateCaseStatus, language, setActiveCase, activeTab, setActiveTab } = useAppStore();
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [prescriptionNote, setPrescriptionNote] = useState("");
  const isBn = language === "bn";

  const currentTab = activeTab === "history" ? "reviewed" : "queue";

  const pendingCases = cases.filter(
    (c) => c.status === "pending_expert" || c.status === "analyzed"
  );
  const reviewedCases = cases.filter((c) => c.status === "reviewed");

  const selectedCase =
    cases.find((c) => c.id === selectedCaseId) || pendingCases[0] || cases[0];

  const handleApprove = () => {
    if (!selectedCase) return;
    updateCaseStatus(
      selectedCase.id,
      "reviewed",
      prescriptionNote ||
        (isBn
          ? "কৃষিবিদ দ্বারা সরাসরি পর্যবেক্ষণ ও কার্যকর চিকিৎসা সুপারিশ অনুমোদন করা হলো।"
          : "Agronomist verified diagnosis and confirmed treatment prescribed.")
    );
    setPrescriptionNote("");
  };

  return (
    <div className="space-y-6">
      {/* Agronomist Top Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-950 via-indigo-950 to-slate-900 text-white p-5 sm:p-6 shadow-md border border-blue-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold">
              <UserCheck className="h-3.5 w-3.5" />
              <span>{isBn ? "কৃষিবিদ বিশেষজ্ঞ পোর্টাল" : "Agronomist Expert Workspace"}</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight">
              {isBn ? "রোগ পর্যবেক্ষণ ও প্রেসক্রিপশন" : "Diagnosis Verification & Advisory"}
            </h2>
            <p className="text-xs text-blue-100/80 max-w-xl">
              {isBn
                ? "কৃষকদের পাঠানো AI সন্দেহভাজন কেসগুলো পর্যবেক্ষণ করুন, সঠিক রোগ নিশ্চিত করুন এবং প্রেসক্রিপশন প্রদান করুন।"
                : "Validate AI-detected pathogens and authorize agronomic treatment protocols."}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-card/20 backdrop-blur border border-white/10 px-4 py-2 rounded-xl text-center">
              <div className="text-[10px] text-amber-300 uppercase font-semibold">
                {isBn ? "অপেক্ষমান" : "Pending Queue"}
              </div>
              <div className="text-xl font-black text-amber-400">{pendingCases.length}</div>
            </div>
            <div className="bg-card/20 backdrop-blur border border-white/10 px-4 py-2 rounded-xl text-center">
              <div className="text-[10px] text-emerald-300 uppercase font-semibold">
                {isBn ? "রিভিউ সম্পন্ন" : "Reviewed"}
              </div>
              <div className="text-xl font-black text-emerald-400">{reviewedCases.length}</div>
            </div>
          </div>
        </div>

        {/* Minimal Sub-Tabs */}
        <div className="mt-5 pt-4 border-t border-white/10 flex items-center gap-2">
          <button
            onClick={() => setActiveTab("expert_queue")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentTab === "queue"
                ? "bg-white text-blue-950 shadow-sm"
                : "bg-white/10 text-blue-100 hover:bg-white/20"
            }`}
          >
            <ClipboardList className="h-3.5 w-3.5" />
            <span>
              {isBn ? "অপেক্ষমান কেস কিউ" : "Review Queue"} ({pendingCases.length})
            </span>
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentTab === "reviewed"
                ? "bg-white text-blue-950 shadow-sm"
                : "bg-white/10 text-blue-100 hover:bg-white/20"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span>{isBn ? "পর্যালোচিত কেস হিস্ট্রি" : "Verified Records"}</span>
          </button>
        </div>
      </div>

      {/* SubTab 1: Review Queue & Interactive Consultation */}
      {currentTab === "queue" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Queue list & Case action form */}
          <div className="lg:col-span-7 space-y-5">
            {/* Queue selection cards */}
            <Card className="border-border shadow-sm">
              <CardHeader className="pb-3 pt-4 px-4 border-b">
                <CardTitle className="text-sm font-bold flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Stethoscope className="h-4 w-4 text-blue-600" />
                    {isBn ? "পর্যালোচনার জন্য উন্মুক্ত কেস তালিকা" : "Cases Awaiting Inspection"}
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {pendingCases.length} {isBn ? "টি কেস বাকি" : "Pending"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-2.5">
                {pendingCases.length === 0 ? (
                  <div className="p-6 text-center text-xs text-muted-foreground">
                    {isBn ? "বর্তমানে কোনো অপেক্ষমান কেস নেই।" : "No pending cases in queue."}
                  </div>
                ) : (
                  pendingCases.map((c) => {
                    const isSelected = selectedCase?.id === c.id;
                    return (
                      <div
                        key={c.id}
                        onClick={() => {
                          setSelectedCaseId(c.id);
                          setActiveCase(c);
                        }}
                        className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3 ${
                          isSelected
                            ? "border-blue-500 bg-blue-500/5 shadow-sm ring-1 ring-blue-500/20"
                            : "border-border hover:border-border/80 hover:bg-muted/40"
                        }`}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={c.imageUrl}
                          alt={c.cropName}
                          className="h-12 w-12 rounded-lg object-cover border shrink-0"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono text-[10px] text-muted-foreground font-semibold">
                              {c.caseNumber}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-[10px] font-medium ${
                                c.status === "pending_expert"
                                  ? "text-amber-600 bg-amber-500/10 border-amber-500/30"
                                  : "text-blue-600 bg-blue-500/10 border-blue-500/30"
                              }`}
                            >
                              {c.status === "pending_expert"
                                ? isBn
                                  ? "বিশেষজ্ঞ অনুরোধ"
                                  : "Requested"
                                : isBn
                                ? "AI বিশ্লেষণ"
                                : "AI Analyzed"}
                            </Badge>
                          </div>
                          <h4 className="text-xs font-bold text-foreground truncate mt-0.5">
                            {isBn ? c.cropNameBn : c.cropName} — {isBn ? c.diseaseNameBn : c.diseaseName}
                          </h4>
                          <div className="text-[10px] text-muted-foreground flex items-center gap-2 mt-0.5">
                            <span>কনফিডেন্স: {Math.round(c.confidence * 100)}%</span>
                            <span>•</span>
                            <span>{c.createdAt}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            {/* Expert Prescription Box */}
            {selectedCase && (
              <Card className="border-blue-500/30 shadow-sm bg-card">
                <CardHeader className="pb-3 pt-4 px-4 border-b bg-muted/30">
                  <CardTitle className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <FileCheck2 className="h-4 w-4 text-blue-600" />
                    <span>
                      {isBn
                        ? `কেস #${selectedCase.caseNumber} এর জন্য প্রেসক্রিপশন নোট লিখুন`
                        : `Prescription for Case #${selectedCase.caseNumber}`}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <textarea
                    rows={3}
                    value={prescriptionNote}
                    onChange={(e) => setPrescriptionNote(e.target.value)}
                    placeholder={
                      isBn
                        ? "ওষুধের নাম, স্প্রে করার পরিমাণ ও করণীয় সংক্রান্ত পরামর্শ লিখুন (যেমন: মেনকোজেব ২ গ্রাম/লিটার)..."
                        : "Write agronomist instructions, dosage and follow-up precautions..."
                    }
                    className="w-full text-xs rounded-lg border border-border bg-background p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      onClick={handleApprove}
                      size="sm"
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs h-8 px-4"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
                      <span>{isBn ? "অনুমোদন ও প্রেসক্রিপশন পাঠান" : "Authorize Advisory"}</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column: Case Details & Leaf image preview */}
          <div className="lg:col-span-5 sticky top-24">
            <DiagnosisResult />
          </div>
        </div>
      )}

      {/* SubTab 2: Reviewed History */}
      {currentTab === "reviewed" && <CaseHistory />}
    </div>
  );
}

