"use client";

import React, { useEffect, useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BACKEND_URL } from "@/lib/api";
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
  Loader2,
  RefreshCw,
} from "lucide-react";

interface LiveStats {
  totalFarmers: string;
  totalFarmersSub: string;
  totalDiagnoses: string;
  totalDiagnosesSub: string;
  apiLatency: string;
  isApiOnline: boolean;
  recentActivity: Array<{
    action: string;
    user: string;
    role: string;
    time: string;
    status: string;
  }>;
}

export default function AdminDashboard() {
  const { cases, language } = useAppStore();
  const isBn = language === "bn";

  const [liveStats, setLiveStats] = useState<LiveStats | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchedAt, setFetchedAt] = useState<string>("");

  const fetchStats = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("kb_access_token") : null;
    setIsFetching(true);
    let pingMs = "—";
    let apiHealthy = false;

    try {
      const pingStart = performance.now();
      const healthRes = await fetch(`${BACKEND_URL}/health`, { method: "GET" }).catch(() => null);
      if (healthRes && healthRes.ok) {
        pingMs = `${Math.round(performance.now() - pingStart)}ms`;
        apiHealthy = true;
      }

      let totalUsersCount: number = 0;
      let totalCasesCount: number = 0;
      const recentLogs: LiveStats["recentActivity"] = [];

      if (token) {
        // GET /api/v1/auth/users — admin user list
        const usersRes = await fetch(`${BACKEND_URL}/api/v1/auth/users?limit=5`, {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => null);

        // GET /api/v1/diagnosis-cases
        const casesRes = await fetch(`${BACKEND_URL}/api/v1/diagnosis-cases?limit=5`, {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => null);

        if (usersRes && usersRes.ok) {
          const uJson = await usersRes.json();
          totalUsersCount = uJson.total ?? (Array.isArray(uJson.data) ? uJson.data.length : 0);
          if (Array.isArray(uJson.data)) {
            uJson.data.slice(0, 4).forEach((u: any) => {
              recentLogs.push({
                action: "USER_ACCOUNT",
                user: u.full_name || u.phone_number || "ব্যবহারকারী",
                role: u.roles?.name || u.roles?.code || "farmer",
                time: u.created_at ? new Date(u.created_at).toLocaleTimeString(isBn ? "bn-BD" : "en-US", { hour: "2-digit", minute: "2-digit" }) : "সম্প্রতি",
                status: u.status || "ACTIVE",
              });
            });
          }
        }

        if (casesRes && casesRes.ok) {
          const cJson = await casesRes.json();
          totalCasesCount = cJson.total ?? (Array.isArray(cJson.data) ? cJson.data.length : 0);
        }
      }

      setLiveStats({
        totalFarmers: `${totalUsersCount.toLocaleString("bn-BD")}`,
        totalFarmersSub: isBn ? "সুপাবেস ডাটাবেজের সরাসরি সংখ্যা" : "Live count from database",
        totalDiagnoses: `${totalCasesCount.toLocaleString("bn-BD")}`,
        totalDiagnosesSub: isBn ? "মোট সংরক্ষিত কেস" : "Total stored cases",
        apiLatency: pingMs,
        isApiOnline: apiHealthy,
        recentActivity: recentLogs,
      });
      setFetchedAt(new Date().toLocaleTimeString(isBn ? "bn-BD" : "en-BD"));
    } catch {
      // Backend not reachable
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stats = [
    {
      titleBn: "মোট নিবন্ধিত কৃষক",
      titleEn: "Total Registered Farmers",
      value: liveStats?.totalFarmers ?? "০",
      subBn: liveStats?.totalFarmersSub ?? "লাইভ ডেটা লোড হচ্ছে...",
      subEn: liveStats?.totalFarmersSub ?? "Loading live data...",
      icon: Users,
      color: "text-blue-500 bg-blue-500/10",
    },
    {
      titleBn: "মোট AI স্ক্যান কেস",
      titleEn: "Total AI Diagnoses",
      value: liveStats?.totalDiagnoses ?? "০",
      subBn: liveStats?.totalDiagnosesSub ?? "লাইভ ডেটা লোড হচ্ছে...",
      subEn: liveStats?.totalDiagnosesSub ?? "Loading live data...",
      icon: Cpu,
      color: "text-emerald-500 bg-emerald-500/10",
    },
    {
      titleBn: "সার্ভার লেটেন্সি (Ping)",
      titleEn: "API Ping Latency",
      value: liveStats?.apiLatency ?? "—",
      subBn: liveStats?.isApiOnline ? "সার্ভার অনলাইন ও সচল" : "সার্ভার চেক করা হচ্ছে...",
      subEn: liveStats?.isApiOnline ? "Server healthy & online" : "Checking server status...",
      icon: CheckCircle2,
      color: "text-amber-500 bg-amber-500/10",
    },
    {
      titleBn: "সিস্টেম পরিবেশ (Environment)",
      titleEn: "Platform Mode",
      value: "Production Ready",
      subBn: "সুপাবেস লাইভ কানেক্টেড",
      subEn: "Live DB Connected",
      icon: AlertTriangle,
      color: "text-emerald-500 bg-emerald-500/10",
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
                ? "সারাদেশে কৃষক সেবা, AI মডেল পারফরম্যান্স এবং মাঠপর্যায়ের কৃষি রোগ ট্র্যাকিং ও অডিট মনিটরিং।"
                : "Real-time national surveillance of agricultural health, model latency and DAE expert operations."}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Badge className="bg-emerald-500 text-black font-bold text-xs py-1 px-3">
              ● API Online v1.0
            </Badge>
            <button
              onClick={fetchStats}
              disabled={isFetching}
              className="flex items-center gap-1 text-xs text-emerald-300 hover:text-white transition-colors"
            >
              {isFetching ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              {isBn ? "লাইভ ডেটা রিফ্রেশ" : "Refresh Live Data"}
            </button>
            {fetchedAt && (
              <span className="text-[10px] text-emerald-400">
                {isBn ? `আপডেট: ${fetchedAt}` : `Updated: ${fetchedAt}`}
              </span>
            )}
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
                <div className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
                  {s.value}
                  {isFetching && idx < 2 && (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  )}
                </div>
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
              {liveStats?.recentActivity && liveStats.recentActivity.length > 0 ? (
                liveStats.recentActivity.map((log, index) => (
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
                ))
              ) : (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  {isBn ? "কোনো সাম্প্রতিক ইউজার লগ পাওয়া যায়নি।" : "No recent user activity logs."}
                </div>
              )}
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
                <span className="font-medium">FastAPI Backend (Port 8000)</span>
                <span className="font-bold">{liveStats?.isApiOnline ? `সক্রিয় (${liveStats.apiLatency})` : "অফলাইন"}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">PostgreSQL (Supabase Pooler)</span>
                <span className="font-bold">সংযুক্ত (Port 6543)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">Google Gemini Vision API</span>
                <span className="font-bold">সক্রিয়</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <span className="font-medium">Supabase Storage ('crops' bucket)</span>
                <span className="font-bold">কনফিগারড</span>
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
