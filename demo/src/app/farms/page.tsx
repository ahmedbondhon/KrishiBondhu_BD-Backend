"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import MyFarmsPanel from "@/components/MyFarmsPanel";
import { useAppStore } from "@/store/useAppStore";

export default function FarmsPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            {isBn ? "আমার ফসলের জমি ব্যবস্থাপনা" : "My Farmlands Management"}
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            {isBn
              ? "আপনার চাষকৃত বিভিন্ন প্লট বা খণ্ডের ফসলের স্বাস্থ্য ও ডায়াগনসিস স্ট্যাটাস মনিটর করুন।"
              : "Manage and monitor the crop health and seasonal diagnostics of your plots."}
          </p>
        </div>

        <MyFarmsPanel />
      </main>
    </div>
  );
}

