"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import AdminDashboard from "@/components/AdminDashboard";
import { useAppStore } from "@/store/useAppStore";

export default function AdminPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-rose-50/20 to-background dark:via-rose-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <AdminDashboard />
      </main>
    </div>
  );
}

