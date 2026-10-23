"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import AgronomistDashboard from "@/components/AgronomistDashboard";
import { useAppStore } from "@/store/useAppStore";

export default function ExpertPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-blue-50/20 to-background dark:via-blue-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <AgronomistDashboard />
      </main>
    </div>
  );
}

