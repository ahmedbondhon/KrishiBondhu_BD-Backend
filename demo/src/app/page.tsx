"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import StatsBanner from "@/components/StatsBanner";
import AuthModal from "@/components/AuthModal";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  PhoneCall,
  Search,
  Sprout,
  UserCheck,
  ShieldAlert,
  ArrowRight,
  ClipboardList,
  Users,
  History,
  CheckCircle2,
  LogIn,
} from "lucide-react";

export default function Home() {
  const {
    role,
    language,
    isAuthenticated,
    currentUser,
    openAuthModal,
  } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl space-y-8">
        {/* Simple & Clean Welcome Banner */}
        <div className="rounded-3xl p-6 sm:p-10 bg-gradient-to-br from-emerald-800 via-green-800 to-teal-900 text-white shadow-xl border border-emerald-600/30 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur border border-white/20 text-xs font-semibold text-emerald-200">
              <Sparkles className="h-3.5 w-3.5 text-amber-300" />
              <span>
                {role === "farmer"
                  ? isBn
                    ? "কৃষক সহায়তা পোর্টাল"
                    : "Farmer Agronomy Portal"
                  : role === "expert"
                  ? isBn
                    ? "কৃষিবিদ বিশেষজ্ঞ পোর্টাল"
                    : "Agronomist Review Portal"
                  : isBn
                  ? "সিস্টেম অ্যাডমিনিস্ট্রেশন"
                  : "Platform Administration"}
              </span>
            </div>

            <h1 className="text-2xl sm:text-4xl font-black tracking-tight leading-snug">
              {isAuthenticated && currentUser ? (
                <>
                  {isBn ? `স্বাগতম, ${currentUser.fullName}!` : `Welcome back, ${currentUser.fullName}!`}
                </>
              ) : isBn ? (
                <>
                  কৃষিবন্ধু বাংলাদেশে{" "}
                  <span className="text-emerald-300 underline decoration-amber-400 decoration-wavy decoration-2">
                    স্বাগতম
                  </span>
                </>
              ) : (
                <>
                  Welcome to{" "}
                  <span className="text-emerald-300 underline decoration-amber-400 decoration-wavy decoration-2">
                    KrishiBondhu BD
                  </span>
                </>
              )}
            </h1>

            <p className="text-sm text-emerald-100/90 leading-relaxed">
              {role === "farmer"
                ? isBn
                  ? "আপনার ফসলের ছবি তুলে দ্রুত রোগ শনাক্ত করুন, বৈজ্ঞানিক সমাধান জানুন অথবা জমির তালিকা ট্র্যাক করুন।"
                  : "Diagnose crop diseases instantly with AI, access certified treatments, and manage your farmlands."
                : role === "expert"
                ? isBn
                  ? "কৃষকদের পাঠানো AI সন্দেহভাজন কেসগুলো পর্যবেক্ষণ করুন এবং বিশেষজ্ঞদের অনুমোদিত প্রেসক্রিপশন প্রদান করুন।"
                  : "Inspect field cases detected by vision AI and issue tailored agronomist prescriptions."
                : isBn
                ? "সারাদেশের কৃষক সেবা, AI মডেলের নির্ভুলতা ও সিস্টেম অডিট এবং ইউজার তালিকা পরিচালনা করুন।"
                : "Monitor national agricultural surveillance, system metrics, audit logs, and user roles."}
            </p>
          </div>

          {/* Quick Action Button in Banner */}
          <div className="shrink-0 flex flex-col sm:flex-row gap-3">
            {!isAuthenticated ? (
              <Button
                onClick={() => openAuthModal("login")}
                className="bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold px-5 h-11 text-sm rounded-xl shadow-lg"
              >
                <LogIn className="h-4 w-4 mr-2" />
                <span>{isBn ? "লগইন করুন" : "Login Account"}</span>
              </Button>
            ) : (
              <div className="bg-white/10 backdrop-blur border border-white/20 p-4 rounded-2xl flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-amber-400 text-slate-950 flex items-center justify-center font-bold">
                  <PhoneCall className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-[10px] text-emerald-200 uppercase font-semibold">
                    {isBn ? "কৃষি হেল্পলাইন" : "Helpline Hotline"}
                  </div>
                  <div className="text-lg font-black text-white">১৬১২৩</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Global Statistics */}
        <StatsBanner />

        {/* Simple Role-Based Feature Cards (Direct Navigation) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-600" />
              <span>{isBn ? "আপনার জন্য ফিচারসমূহ" : "Quick Features"}</span>
            </h2>
            <span className="text-xs text-muted-foreground uppercase font-semibold">
              Role: {role}
            </span>
          </div>

          {role === "farmer" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Link href="/diagnosis" className="group">
                <Card className="h-full border border-border/80 hover:border-emerald-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Search className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-emerald-600 transition-colors">
                      {isBn ? "রোগ নির্ণয় (AI স্ক্যান)" : "Crop Diagnosis"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "ফসল নির্বাচন করে আক্রান্ত পাতার ছবি আপলোড করুন এবং তাৎক্ষণিক বিজ্ঞানসম্মত সমাধান পান।"
                        : "Upload leaf photos and get real-time pathogen identification and Bengali remedies."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-emerald-600">
                      <span>{isBn ? "শুরু করুন" : "Open Diagnosis"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/farms" className="group">
                <Card className="h-full border border-border/80 hover:border-emerald-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-teal-500/10 text-teal-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Sprout className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-teal-600 transition-colors">
                      {isBn ? "আমার ফসলের জমি" : "My Farmlands"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "আপনার চাষকৃত বিভিন্ন প্লট বা খণ্ডের স্বাস্থ্য পরিস্থিতি ও হিস্ট্রি একসাথে সংরক্ষণ করুন।"
                        : "Track your land plots, planted crop varieties, and plot health records."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-teal-600">
                      <span>{isBn ? "জমি দেখুন" : "View Farmlands"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/history" className="group">
                <Card className="h-full border border-border/80 hover:border-emerald-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-blue-500/10 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <History className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-blue-600 transition-colors">
                      {isBn ? "পূর্ববর্তী রিপোর্টসমূহ" : "Diagnosis Records"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "পূর্বে করা সমস্ত স্ক্যানিং ফলাফল ও বিশেষজ্ঞদের অনুমোদিত প্রেসক্রিপশন নোট দেখুন।"
                        : "Review all past scanned cases and verified expert agronomist recommendations."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-blue-600">
                      <span>{isBn ? "হিস্ট্রি দেখুন" : "View History"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>
          )}

          {role === "expert" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Link href="/expert" className="group">
                <Card className="h-full border border-border/80 hover:border-blue-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-blue-500/10 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <ClipboardList className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-blue-600 transition-colors">
                      {isBn ? "অপেক্ষমান কেস কিউ" : "Review Queue"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "কৃষকদের পাঠানো AI সন্দেহভাজন আক্রান্ত ফসলের পাতা নিরীক্ষণ ও প্রেসক্রিপশন প্রদান।"
                        : "Inspect pending cases from farmers and issue customized prescription advisories."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-blue-600">
                      <span>{isBn ? "কিউ খুলুন" : "Open Queue"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/history" className="group">
                <Card className="h-full border border-border/80 hover:border-blue-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <History className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-indigo-600 transition-colors">
                      {isBn ? "অনুমোদিত প্রেসক্রিপশন হিস্ট্রি" : "Verified Records"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "আপনার দ্বারা ইতিপূর্বে পর্যালোচিত ও পরামর্শ প্রদানকৃত সমস্ত রেকর্ড দেখুন।"
                        : "Search and inspect all previously verified cases and prescribed treatments."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-indigo-600">
                      <span>{isBn ? "রেকর্ড দেখুন" : "View Records"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>
          )}

          {role === "admin" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Link href="/admin" className="group">
                <Card className="h-full border border-border/80 hover:border-rose-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-rose-500/10 text-rose-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <ShieldAlert className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-rose-600 transition-colors">
                      {isBn ? "অ্যাডমিন মেট্রিক্স ও অডিট" : "System Governance"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "সার্ভার কানেক্টিভিটি, লাইভ অডিট লগ এবং AI নির্ভুলতার জাতীয় স্ট্যাটাস পর্যবেক্ষণ।"
                        : "Inspect live database connectivity, system audit trail and model latency."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-rose-600">
                      <span>{isBn ? "ড্যাশবোর্ড খুলুন" : "Open Governance"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/admin/users" className="group">
                <Card className="h-full border border-border/80 hover:border-rose-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-amber-500/10 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Users className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-amber-600 transition-colors">
                      {isBn ? "ইউজার ম্যানেজমেন্ট" : "User Management"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "কৃষক, মাঠ এজেন্ট এবং বিশেষজ্ঞদের তালিকা, ফিল্টারিং ও অ্যাকাউন্ট নিয়ন্ত্রণ।"
                        : "Filter users, activate/suspend accounts, and govern platform permissions."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-amber-600">
                      <span>{isBn ? "ইউজার দেখুন" : "View Users"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/history" className="group">
                <Card className="h-full border border-border/80 hover:border-rose-500/50 hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="p-6 space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-purple-500/10 text-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <History className="h-6 w-6" />
                    </div>
                    <h3 className="font-bold text-base text-foreground group-hover:text-purple-600 transition-colors">
                      {isBn ? "সকল কেস অডিট" : "National Cases"}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isBn
                        ? "দেশব্যাপী সম্পন্ন হওয়া সমস্ত রোগের কেস ও পরিসংখ্যান বিস্তারিতভাবে দেখুন।"
                        : "Explore all historical cases and outbreaks across 64 districts."}
                    </p>
                    <div className="pt-2 flex items-center gap-1 text-xs font-bold text-purple-600">
                      <span>{isBn ? "কেস তালিকা" : "Inspect Cases"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-emerald-900/10 dark:border-emerald-500/20 bg-card py-6 mt-12 text-center text-xs text-muted-foreground">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Sprout className="h-4 w-4 text-emerald-600" />
            <span className="font-bold text-foreground">
              {isBn ? "কৃষিবন্ধু বাংলাদেশ" : "KrishiBondhu BD"}
            </span>
            <span>— AI-Driven Agriculture Health Platform</span>
          </div>
          <p>
            {isBn
              ? "কৃষি সম্প্রসারণ অধিদপ্তর ও প্রযুক্তিগত সহায়তা"
              : "Integrated with DAE Agricultural Knowledge Base"}
          </p>
        </div>
      </footer>
    </div>
  );
}
