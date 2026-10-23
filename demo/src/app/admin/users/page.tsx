"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import UserManagementView from "@/components/UserManagementView";
import { useAppStore } from "@/store/useAppStore";

export default function AdminUsersPage() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-rose-50/20 to-background dark:via-rose-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <UserManagementView />
      </main>
    </div>
  );
}

