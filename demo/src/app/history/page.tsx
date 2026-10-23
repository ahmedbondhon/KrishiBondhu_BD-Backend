"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import CaseHistory from "@/components/CaseHistory";
import { useAppStore } from "@/store/useAppStore";

export default function HistoryPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            {isBn ? "সকল রোগ নির্ণয় ও চিকিৎসা রেকর্ড" : "Diagnosis & Advisory Records"}
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            {isBn
              ? "পূর্ববর্তী সমস্ত স্ক্যান, AI ফলাফল ও কৃষিবিদদের অনুমোদিত প্রেসক্রিপশন দেখতে ক্লিক করুন।"
              : "Review past crop health scans, AI predictions and certified agronomist prescriptions."}
          </p>
        </div>

        <CaseHistory />
      </main>
    </div>
  );
}

