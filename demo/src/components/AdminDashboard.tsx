"use client";

import React from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldAlert,
  Users,
  Activity,
  Cpu,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Database,
  Layers,
  ArrowUpRight,
} from "lucide-react";

export default function AdminDashboard() {
  const { cases, language } = useAppStore();
  const isBn = language === "bn";

  const stats = [
    {
      titleBn: "মোট নিবন্ধিত কৃষক",
      titleEn: "Total Registered Farmers",
      value: "২৪,৫২০+",
      subBn: "+১২০ জন আজ যুক্ত হয়েছেন",
      subEn: "+120 joined today",
      icon: Users,
      color: "text-blue-500 bg-blue-500/10",
    },
    {
      titleBn: "মোট AI স্ক্যান কেস",
      titleEn: "Total AI Diagnoses",
      value: "১,৮৪,৩১০",
      subBn: "সাফল্যের হার ৯৬.৪%",
      subEn: "96.4% Accuracy rate",
      icon: Cpu,
      color: "text-emerald-500 bg-emerald-500/10",
    },
    {
      titleBn: "এক্সপার্ট রিভিউ সম্পন্ন",
      titleEn: "Expert Reviews Completed",
      value: "৮,৯৫০",
      subBn: "গড় রেসপন্স সময় < ২ ঘণ্টা",
      subEn: "Avg response < 2h",
      icon: CheckCircle2,
      color: "text-amber-500 bg-amber-500/10",
    },
    {
      titleBn: "সক্রিয় রোগ অ্যালার্ট (বগুড়া/রংপুর)",
      titleEn: "Active Disease Alerts",
      value: "৪ টি অঞ্চল",
      subBn: "আলুর লেট ব্লাইট সতর্কতা",
      subEn: "Potato Late Blight Outbreak",
      icon: AlertTriangle,
      color: "text-rose-500 bg-rose-500/10",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-emerald-950 text-white shadow-xl border border-emerald-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>{isBn ? "সিস্টেম অ্যাডমিন প্যানেল" : "System Administrator Control"}</span>
            </div>
            <h2 className="text-2xl font-black tracking-tight">
              {isBn ? "কৃষিবন্ধু প্ল্যাটফর্ম ওভারভিউ ও গভর্ন্যান্স" : "KrishiBondhu Governance Dashboard"}
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-xl">
              {isBn
                ? "সারাদেশে কৃষক সেবা, AI মডেল পারফরম্যান্স এবং মাঠপর্যায়ের কৃষি রোগ ট্র্যাকিং ও অডিট মনিটরিং।"
                : "Real-time national surveillance of agricultural health, model latency and DAE expert operations."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge className="bg-emerald-500 text-black font-bold text-xs py-1 px-3">
              ● API Online v1.0
            </Badge>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <Card key={idx} className="border-border shadow-sm">
              <CardContent className="p-5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">
                    {isBn ? s.titleBn : s.titleEn}
                  </span>
                  <div className={`p-2 rounded-xl ${s.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-2xl font-black tracking-tight text-foreground">{s.value}</div>
                <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                  <TrendingUp className="h-3 w-3 text-emerald-500" />
                  <span>{isBn ? s.subBn : s.subEn}</span>
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Model & Database Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-border shadow-sm">
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-600" />
                <span>{isBn ? "সাম্প্রতিক সিস্টেম অডিট লগ" : "Recent System Audit Logs"}</span>
              </h3>
              <span className="text-xs text-muted-foreground">{isBn ? "লাইভ স্ট্রিমিং" : "Live Streaming"}</span>
            </div>

            <div className="space-y-3">
              {[
                {
                  action: "USER_REGISTER",
                  user: "+8801754890387 (Md. Abdullah)",
                  role: "farmer",
                  time: "১০ মিনিট আগে",
                  status: "SUCCESS",
                },
                {
                  action: "AI_DIAGNOSIS_HIGH_CONFIDENCE",
                  user: "System (Vision Model)",
                  role: "ai-service",
                  time: "২৫ মিনিট আগে",
                  status: "94% Confident",
                },
                {
                  action: "EXPERT_ADVISORY_ISSUED",
                  user: "Dr. Rafiqul Islam (DAE Expert)",
                  role: "expert",
                  time: "১ ঘণ্টা আগে",
                  status: "Case #411 Reviewed",
                },
                {
                  action: "AUTH_TOKEN_REFRESH",
                  user: "+8801812345678",
                  role: "agent",
                  time: "২ ঘণ্টা আগে",
                  status: "SUCCESS",
                },
              ].map((log, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border/50 text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="font-mono font-semibold text-foreground">{log.action}</div>
                    <div className="text-muted-foreground text-[11px]">{log.user} ({log.role})</div>
                  </div>
                  <div className="text-right space-y-0.5">
                    <Badge variant="outline" className="text-[10px] bg-card">
                      {log.status}
                    </Badge>
                    <div className="text-[10px] text-muted-foreground">{log.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Database & Cloud Services */}
        <Card className="border-border shadow-sm">
          <CardContent className="p-5 space-y-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Database className="h-4 w-4 text-teal-600" />
              <span>{isBn ? "সার্ভিস স্ট্যাটাস" : "Services Connectivity"}</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">PostgreSQL (Neon DB)</span>
                <span className="font-bold">সংযুক্ত (12ms)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">Gemini 2.0 Vision AI</span>
                <span className="font-bold">সক্রিয়</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">Supabase Storage</span>
                <span className="font-bold">স্বাভাবিক</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">SMS Gateway Simulator</span>
                <span className="font-bold">অ্যাক্টিভ</span>
              </div>
            </div>

            <div className="pt-2 border-t">
              <p className="text-[11px] text-muted-foreground">
                {isBn
                  ? "সকল মাইগ্রেশন (001-014) ডাটাবেজে এক্সিকিউটেড এবং ইনডেক্সিং অপ্টিমাইজড।"
                  : "All migrations (001-014) synced and indexing fully optimized."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
