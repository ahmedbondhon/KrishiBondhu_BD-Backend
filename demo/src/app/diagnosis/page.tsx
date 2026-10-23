"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import CropSelector from "@/components/CropSelector";
import DiagnosisUploader from "@/components/DiagnosisUploader";
import DiagnosisResult from "@/components/DiagnosisResult";
import { useAppStore } from "@/store/useAppStore";

export default function DiagnosisPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            {isBn ? "স্মার্ট ফসল রোগ নির্ণয় (AI Diagnosis)" : "AI Crop Disease Diagnosis"}
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            {isBn
              ? "ফসল বেছে নিন, আক্রান্ত পাতার স্পষ্ট ছবি আপলোড করুন এবং তাৎক্ষণিক বিজ্ঞানসম্মত সমাধান গ্রহণ করুন।"
              : "Select crop species, take or upload clear specimen photos for instant AI identification."}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-7 space-y-6">
            <CropSelector />
            <DiagnosisUploader />
          </div>
          <div className="lg:col-span-5 sticky top-24">
            <DiagnosisResult />
          </div>
        </div>
      </main>
    </div>
  );
}

