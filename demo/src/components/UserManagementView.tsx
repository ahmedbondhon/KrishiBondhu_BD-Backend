"use client";

import React, { useState, useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  Search,
  Phone,
  MapPin,
  Lock,
  Unlock,
  Database,
  RefreshCw,
  Loader2,
  CheckCircle2,
} from "lucide-react";

interface SupabaseUser {
  id: string;
  full_name: string;
  phone_number: string;
  status: string;
  created_at?: string;
  roles?: {
    code: string;
    name: string;
  };
}

export default function UserManagementView() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  const [users, setUsers] = useState<SupabaseUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const fetchSupabaseUsers = async () => {
    setLoading(true);
    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      const resp = await fetch(
        `${sbUrl}/users?select=id,phone_number,full_name,status,created_at,roles(code,name)&order=created_at.desc`,
        {
          headers: {
            apikey: sbKey,
            Authorization: `Bearer ${sbKey}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (resp.ok) {
        const data = await resp.json();
        setUsers(data || []);
      }
    } catch (e) {
      console.error("Error fetching users from Supabase:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    const loadInitialUsers = async () => {
      try {
        const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
        const sbKey =
          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

        const resp = await fetch(
          `${sbUrl}/users?select=id,phone_number,full_name,status,created_at,roles(code,name)&order=created_at.desc`,
          {
            headers: {
              apikey: sbKey,
              Authorization: `Bearer ${sbKey}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (resp.ok) {
          const data = await resp.json();
          if (!ignore) setUsers(data || []);
        }
      } catch (e) {
        console.error("Error fetching users from Supabase:", e);
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    loadInitialUsers();
    return () => {
      ignore = true;
    };
  }, []);

  const toggleUserStatus = async (user: SupabaseUser) => {
    const nextStatus = user.status === "active" ? "suspended" : "active";
    // Update local state immediately
    setUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, status: nextStatus } : u))
    );

    // Sync to Supabase live database
    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      await fetch(`${sbUrl}/users?id=eq.${user.id}`, {
        method: "PATCH",
        headers: {
          apikey: sbKey,
          Authorization: `Bearer ${sbKey}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({ status: nextStatus }),
      });
    } catch (err) {
      console.error("Failed to update status on Supabase:", err);
    }
  };

  const filteredUsers = users.filter((u) => {
    const roleCode = u.roles?.code || "farmer";
    const name = u.full_name || "";
    const phone = u.phone_number || "";

    const matchesSearch =
      name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      phone.includes(searchTerm);
    const matchesRole =
      roleFilter === "all" ||
      roleCode.toLowerCase().includes(roleFilter.toLowerCase());
    const matchesStatus = statusFilter === "all" || u.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleBadge = (roleCode: string = "farmer") => {
    if (roleCode.includes("admin")) {
      return (
        <Badge className="bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20 font-bold text-[10px]">
          🛡️ {isBn ? "অ্যাডমিন" : "Admin"}
        </Badge>
      );
    }
    if (roleCode.includes("expert")) {
      return (
        <Badge className="bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20 font-bold text-[10px]">
          🧑‍🔬 {isBn ? "কৃষিবিদ" : "Agronomist"}
        </Badge>
      );
    }
    if (roleCode.includes("dealer") || roleCode.includes("agent")) {
      return (
        <Badge className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 font-bold text-[10px]">
          🤝 {isBn ? "ডিলার / এজেন্ট" : "Dealer / Agent"}
        </Badge>
      );
    }
    return (
      <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 font-bold text-[10px]">
        🌱 {isBn ? "কৃষক" : "Farmer"}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-teal-950 to-emerald-950 text-white shadow-xl border border-emerald-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2">
            <Database className="h-3.5 w-3.5 text-emerald-400" />
            <span>{isBn ? "সুপাবেস লাইভ ইউজার ডিরেক্টরি" : "Supabase Live Users Directory"}</span>
          </div>
          <h2 className="text-2xl font-black tracking-tight">
            {isBn ? "ব্যবহারকারী পরিচালনা ও কন্ট্রোল" : "Users Directory & Governance"}
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            {isBn
              ? "সরাসরি Supabase PostgreSQL ডাটাবেজ থেকে আসল রেজিস্টার্ড ইউজারদের তালিকা ও অ্যাকাউন্ট নিয়ন্ত্রণ।"
              : "Live synchronization with Supabase users, roles, and status administration."}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={fetchSupabaseUsers}
            disabled={loading}
            variant="outline"
            size="sm"
            className="bg-card/20 border-white/20 text-white hover:bg-card/30 text-xs gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>{isBn ? "রিফ্রেশ" : "Refresh"}</span>
          </Button>

          <div className="bg-card/20 backdrop-blur border border-white/10 px-4 py-2 rounded-xl text-center">
            <div className="text-xs text-emerald-300 font-medium">
              {isBn ? "সুপাবেস ইউজার" : "Total Users"}
            </div>
            <div className="text-xl font-black">{users.length}</div>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <Card className="border-border shadow-sm">
        <CardContent className="p-4 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="relative w-full md:w-80">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={isBn ? "নাম বা ফোন নম্বর দিয়ে খুঁজুন..." : "Search name or phone..."}
              className="pl-9 h-9 text-xs"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            {/* Role Filter */}
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border text-xs">
              {["all", "farmer", "expert", "dealer", "admin"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRoleFilter(r)}
                  className={`px-2.5 py-1 rounded-md capitalize transition-all ${
                    roleFilter === r
                      ? "bg-card text-foreground font-bold shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {r === "all"
                    ? isBn
                      ? "সকল রোল"
                      : "All"
                    : r === "farmer"
                    ? isBn
                      ? "কৃষক"
                      : "Farmer"
                    : r === "expert"
                    ? isBn
                      ? "বিশেষজ্ঞ"
                      : "Expert"
                    : r === "dealer"
                    ? isBn
                      ? "ডিলার"
                      : "Dealer"
                    : isBn
                    ? "অ্যাডমিন"
                    : "Admin"}
                </button>
              ))}
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border text-xs">
              {["all", "active", "suspended"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`px-2.5 py-1 rounded-md capitalize transition-all ${
                    statusFilter === s
                      ? "bg-card text-foreground font-bold shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {s === "all"
                    ? isBn
                      ? "সব"
                      : "All"
                    : s === "active"
                    ? isBn
                      ? "সক্রিয়"
                      : "Active"
                    : isBn
                    ? "স্থগিত"
                    : "Suspended"}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="border-border shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">
            <Loader2 className="h-7 w-7 animate-spin text-emerald-600" />
            <p className="text-xs">{isBn ? "সুপাবেস থেকে ইউজার ডাটা আনা হচ্ছে..." : "Loading users from Supabase..."}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b border-border/80 text-muted-foreground uppercase font-semibold">
                <tr>
                  <th className="p-3.5 pl-5">{isBn ? "ব্যবহারকারী (Supabase)" : "User"}</th>
                  <th className="p-3.5">{isBn ? "রোল (Role)" : "Role"}</th>
                  <th className="p-3.5">{isBn ? "ফোন নম্বর" : "Phone"}</th>
                  <th className="p-3.5">{isBn ? "স্ট্যাটাস" : "Status"}</th>
                  <th className="p-3.5 pr-5 text-right">{isBn ? "পদক্ষেপ" : "Action"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-muted-foreground">
                      {isBn ? "কোনো ব্যবহারকারী পাওয়া যায়নি।" : "No users matched your criteria."}
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3.5 pl-5">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-bold flex items-center justify-center shrink-0">
                            {(u.full_name || "U").charAt(0)}
                          </div>
                          <div>
                            <div className="font-bold text-foreground text-sm">
                              {u.full_name || "বেনামী ব্যবহারকারী"}
                            </div>
                            <div className="text-muted-foreground text-[10px] font-mono">
                              ID: {u.id.substring(0, 13)}...
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="p-3.5">{getRoleBadge(u.roles?.code)}</td>

                      <td className="p-3.5 font-mono text-[12px] text-foreground font-semibold">
                        <div className="flex items-center gap-1.5">
                          <Phone className="h-3 w-3 text-muted-foreground" />
                          <span>{u.phone_number}</span>
                        </div>
                      </td>

                      <td className="p-3.5">
                        {u.status === "active" ? (
                          <Badge
                            variant="outline"
                            className="text-emerald-600 bg-emerald-500/10 border-emerald-500/20 text-[10px]"
                          >
                            ● {isBn ? "সক্রিয়" : "Active"}
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="text-rose-600 bg-rose-500/10 border-rose-500/20 text-[10px]"
                          >
                            ⛔ {isBn ? "স্থগিত" : "Suspended"}
                          </Badge>
                        )}
                      </td>

                      <td className="p-3.5 pr-5 text-right">
                        <Button
                          size="sm"
                          variant={u.status === "active" ? "outline" : "default"}
                          onClick={() => toggleUserStatus(u)}
                          className="h-7 text-[11px] px-2.5"
                        >
                          {u.status === "active" ? (
                            <>
                              <Lock className="h-3 w-3 mr-1 text-rose-500" />
                              <span>{isBn ? "স্থগিত করুন" : "Suspend"}</span>
                            </>
                          ) : (
                            <>
                              <Unlock className="h-3 w-3 mr-1" />
                              <span>{isBn ? "সক্রিয় করুন" : "Activate"}</span>
                            </>
                          )}
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
