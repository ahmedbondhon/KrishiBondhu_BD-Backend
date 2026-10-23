"use client";

import React, { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import CropSelector from "@/components/CropSelector";
import DiagnosisUploader from "@/components/DiagnosisUploader";
import DiagnosisResult from "@/components/DiagnosisResult";
import MyFarmsPanel from "@/components/MyFarmsPanel";
import CaseHistory from "@/components/CaseHistory";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sprout,
  Scan,
  MapPin,
  Clock,
  ArrowRight,
  ShieldCheck,
  Headphones,
  PhoneCall,
  Sparkles,
} from "lucide-react";

export default function FarmerDashboard() {
  const { language, activeCase, activeTab, setActiveTab } = useAppStore();
  const isBn = language === "bn";

  // Map global activeTab to farmer sub tabs
  const currentTab =
    activeTab === "farms" ? "farms" : activeTab === "history" ? "history" : "scan";

  return (
    <div className="space-y-6">
      {/* Farmer Welcome & Quick Nav Header */}
      <div className="rounded-2xl bg-gradient-to-r from-emerald-900 via-green-900 to-teal-950 text-white p-5 sm:p-6 shadow-md border border-emerald-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
              <Sprout className="h-3.5 w-3.5" />
              <span>{isBn ? "কৃষক সহায়তা কেন্দ্র" : "Farmer Hub"}</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight">
              {isBn ? "আপনার ফসলের সার্বিক সুরক্ষা" : "Smart Crop Health Companion"}
            </h2>
            <p className="text-xs text-emerald-100/80 max-w-xl">
              {isBn
                ? "সহজে আক্রান্ত পাতার ছবি তুলে তাৎক্ষণিক বাংলা সমাধান জানুন অথবা সরাসরি কৃষিবিদ পরামর্শের অনুরোধ করুন।"
                : "Capture diseased leaves for immediate AI diagnosis and expert DAE recommendations."}
            </p>
          </div>

          {/* Quick Hotline Pill */}
          <div className="bg-card/20 backdrop-blur border border-white/10 px-4 py-2.5 rounded-xl flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center font-bold">
              <PhoneCall className="h-4 w-4" />
            </div>
            <div>
              <div className="text-[10px] text-emerald-200 uppercase font-semibold">
                {isBn ? "কৃষি কল সেন্টার" : "Krishi Hotline"}
              </div>
              <div className="text-base font-black text-white">১৬১২৩</div>
            </div>
          </div>
        </div>

        {/* Minimal Sub-Tabs for Farmer */}
        <div className="mt-5 pt-4 border-t border-white/10 flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("diagnosis")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentTab === "scan"
                ? "bg-white text-emerald-950 shadow-sm"
                : "bg-white/10 text-emerald-100 hover:bg-white/20"
            }`}
          >
            <Scan className="h-3.5 w-3.5" />
            <span>{isBn ? "রোগ নির্ণয় (AI স্ক্যান)" : "Crop Diagnosis"}</span>
          </button>

          <button
            onClick={() => setActiveTab("farms")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentTab === "farms"
                ? "bg-white text-emerald-950 shadow-sm"
                : "bg-white/10 text-emerald-100 hover:bg-white/20"
            }`}
          >
            <Sprout className="h-3.5 w-3.5" />
            <span>{isBn ? "আমার ফসলের জমি" : "My Farmlands"}</span>
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              currentTab === "history"
                ? "bg-white text-emerald-950 shadow-sm"
                : "bg-white/10 text-emerald-100 hover:bg-white/20"
            }`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>{isBn ? "আগের রিপোর্টসমূহ" : "Scan Records"}</span>
          </button>
        </div>
      </div>

      {/* Dynamic Sub-Tab Views */}
      {currentTab === "scan" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-7 space-y-6">
            <CropSelector />
            <DiagnosisUploader />
          </div>
          <div className="lg:col-span-5 sticky top-24">
            <DiagnosisResult />
          </div>
        </div>
      )}

      {currentTab === "farms" && <MyFarmsPanel />}

      {currentTab === "history" && <CaseHistory />}
    </div>
  );
}

