"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sprout,
  Sun,
  Moon,
  ShieldCheck,
  UserCheck,
  Languages,
  LogOut,
  LogIn,
  Search,
  History,
  ClipboardList,
  Users,
  User,
  ShieldAlert,
  LayoutDashboard,
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    role,
    setRole,
    language,
    setLanguage,
    isDark,
    toggleTheme,
    isAuthenticated,
    currentUser,
    openAuthModal,
    logout,
  } = useAppStore();

  const isBn = language === "bn";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-emerald-900/10 dark:border-emerald-500/20 bg-background/95 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between gap-2">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/30 ring-2 ring-emerald-400/20 group-hover:scale-105 transition-transform">
            <Sprout className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-lg text-foreground tracking-tight">
                {isBn ? "কৃষিবন্ধু" : "KrishiBondhu"}
              </span>
              <Badge
                variant="outline"
                className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 text-[9px] font-bold uppercase py-0 px-1.5"
              >
                AI
              </Badge>
            </div>
            <p className="text-[10px] text-muted-foreground hidden sm:block">
              {isBn ? "স্মার্ট কৃষি সুরক্ষা প্ল্যাটফর্ম" : "Smart Agri-Health Portal"}
            </p>
          </div>
        </Link>

        {/* Feature Navigation Pages */}
        <nav className="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/50 text-xs font-semibold overflow-x-auto">
          {/* Main Dashboard */}
          <Link
            href="/"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
              pathname === "/"
                ? "bg-card text-emerald-700 dark:text-emerald-300 font-bold shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <LayoutDashboard className="h-3.5 w-3.5" />
            <span>{isBn ? "ড্যাশবোর্ড" : "Dashboard"}</span>
          </Link>

          {/* Role: Farmer Pages */}
          {role === "farmer" && (
            <>
              <Link
                href="/diagnosis"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/diagnosis"
                    ? "bg-card text-emerald-700 dark:text-emerald-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Search className="h-3.5 w-3.5" />
                <span>{isBn ? "রোগ নির্ণয়" : "Diagnosis"}</span>
              </Link>
              <Link
                href="/farms"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/farms"
                    ? "bg-card text-emerald-700 dark:text-emerald-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sprout className="h-3.5 w-3.5" />
                <span>{isBn ? "আমার জমি" : "My Farms"}</span>
              </Link>
              <Link
                href="/history"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/history"
                    ? "bg-card text-emerald-700 dark:text-emerald-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                <span>{isBn ? "হিস্ট্রি" : "History"}</span>
              </Link>
            </>
          )}

          {/* Role: Expert Pages */}
          {role === "expert" && (
            <>
              <Link
                href="/expert"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/expert"
                    ? "bg-card text-blue-700 dark:text-blue-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <ClipboardList className="h-3.5 w-3.5" />
                <span>{isBn ? "অপেক্ষমান কিউ" : "Review Queue"}</span>
              </Link>
              <Link
                href="/history"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/history"
                    ? "bg-card text-blue-700 dark:text-blue-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                <span>{isBn ? "রিভিউ ইতিহাস" : "Reviewed"}</span>
              </Link>
            </>
          )}

          {/* Role: Admin Pages */}
          {role === "admin" && (
            <>
              <Link
                href="/admin"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/admin"
                    ? "bg-card text-rose-700 dark:text-rose-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>{isBn ? "অ্যাডমিন মেট্রিক্স" : "System Control"}</span>
              </Link>
              <Link
                href="/admin/users"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/admin/users"
                    ? "bg-card text-rose-700 dark:text-rose-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Users className="h-3.5 w-3.5" />
                <span>{isBn ? "ইউজার লিস্ট" : "Users"}</span>
              </Link>
              <Link
                href="/history"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                  pathname === "/history"
                    ? "bg-card text-rose-700 dark:text-rose-300 font-bold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                <span>{isBn ? "সকল কেস" : "All Cases"}</span>
              </Link>
            </>
          )}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Language Switcher */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLanguage(isBn ? "en" : "bn")}
            className="h-8 px-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            <Languages className="h-3.5 w-3.5 mr-1" />
            <span>{isBn ? "EN" : "বাংলা"}</span>
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            className="h-8 w-8 px-0 text-muted-foreground hover:text-foreground"
          >
            {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* Authentication & Profile Status */}
          {isAuthenticated && currentUser ? (
            <div className="flex items-center gap-2 pl-2 border-l">
              <Link
                href="/profile"
                className="hidden lg:flex flex-col items-end text-xs hover:opacity-80 transition-opacity"
                title={isBn ? "প্রোফাইল দেখুন" : "View Profile"}
              >
                <span className="font-bold text-foreground leading-tight">
                  {currentUser.fullName}
                </span>
                <span className="text-muted-foreground text-[10px] uppercase font-semibold">
                  {role === "farmer"
                    ? isBn
                      ? "কৃষক (প্রোফাইল)"
                      : "Farmer (Profile)"
                    : role === "expert"
                    ? isBn
                      ? "কৃষিবিদ (প্রোফাইল)"
                      : "Agronomist (Profile)"
                    : isBn
                    ? "অ্যাডমিন (প্রোফাইল)"
                    : "Admin (Profile)"}
                </span>
              </Link>
              <Link href="/profile">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 px-2 text-xs text-emerald-600 border-emerald-500/30"
                  title="Profile"
                >
                  <User className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline ml-1">{isBn ? "প্রোফাইল" : "Profile"}</span>
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  logout();
                  router.push("/login");
                }}
                className="h-8 px-2.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/20 border-rose-200"
              >
                <LogOut className="h-3.5 w-3.5 mr-1" />
                <span className="hidden sm:inline">{isBn ? "লগআউট" : "Logout"}</span>
              </Button>
            </div>
          ) : (
            <Link href="/login">
              <Button
                size="sm"
                className="h-8 px-3 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
              >
                <LogIn className="h-3.5 w-3.5 mr-1.5" />
                <span>{isBn ? "লগইন" : "Login"}</span>
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
