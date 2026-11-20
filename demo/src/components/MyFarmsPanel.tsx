"use client";

import React, { useState, useEffect } from "react";
import { useAppStore, FarmPlot } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { BACKEND_URL } from "@/lib/api";
import {
  Sprout,
  Plus,
  MapPin,
  Calendar,
  Layers,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Loader2,
  RefreshCw,
} from "lucide-react";

// Convert backend PlotResponse → FarmPlot (UI type)
function backendPlotToFarmPlot(p: {
  id: string;
  name: string;
  area_bigha?: number | null;
  area_sqm?: number | null;
  created_at?: string | null;
  [key: string]: unknown;
}): FarmPlot {
  const areaDecimal = p.area_bigha
    ? Math.round(Number(p.area_bigha) * 33.06) // 1 bigha ≈ 33 decimal
    : p.area_sqm
    ? Math.round(Number(p.area_sqm) / 40.47) // 1 decimal ≈ 40.47 sqm
    : 0;
  return {
    id: p.id,
    name: p.name,
    cropNameBn: "—",
    areaDecimal,
    location: "—",
    healthStatus: "good",
    lastDiagnosisDate: p.created_at ? new Date(p.created_at).toLocaleDateString("bn-BD") : "—",
  };
}

export default function MyFarmsPanel() {
  const { plots, addPlot, language, setSelectedCrop, currentUser } = useAppStore();
  const isBn = language === "bn";

  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState("");
  const [cropNameBn, setCropNameBn] = useState("আলু");
  const [areaDecimal, setAreaDecimal] = useState("30");
  const [location, setLocation] = useState("শিবগঞ্জ, বগুড়া");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [backendPlots, setBackendPlots] = useState<FarmPlot[]>([]);
  const [fetchError, setFetchError] = useState("");
  const [hasFetched, setHasFetched] = useState(false);

  // ── Fetch farms from backend on mount ─────────────────────
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("kb_access_token") : null;
    if (!token) return; // not logged in via backend — use local store

    const fetchPlots = async () => {
      setIsFetching(true);
      setFetchError("");
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/farms`, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        });
        if (res.ok) {
          const data = await res.json();
          const items: FarmPlot[] = (data?.data || data?.items || []).map(backendPlotToFarmPlot);
          setBackendPlots(items);
        } else {
          setFetchError("");
        }
      } catch {
        setFetchError("");
      } finally {
        setIsFetching(false);
        setHasFetched(true);
      }
    };

    fetchPlots();
  }, []);

  // Merge: show backend plots if available, otherwise local store
  const displayPlots = backendPlots.length > 0 ? backendPlots : plots;

  // ── Create new farm ────────────────────────────────────────
  const handleCreatePlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("kb_access_token") : null;

    // Convert decimal to bigha (1 decimal = 0.03025 bigha)
    const areaBigha = (parseFloat(areaDecimal) || 20) * 0.03025;

    if (token) {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/farms`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            name: name.trim(),
            area_bigha: areaBigha.toFixed(4),
          }),
        });
        if (res.ok) {
          const data = await res.json();
          const created = data?.data || data;
          const newPlot = backendPlotToFarmPlot(created);
          newPlot.cropNameBn = cropNameBn;
          newPlot.location = location;
          setBackendPlots((prev) => [newPlot, ...prev]);
          addPlot(newPlot); // keep local store in sync
          setName("");
          setShowAddForm(false);
          setIsSubmitting(false);
          return;
        }
      } catch {
        // Backend failed — fallback to local
      }
    }

    // Local store fallback (backend not running / no token)
    const newPlot: FarmPlot = {
      id:
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `33000000-0000-0000-0000-${Date.now().toString().slice(-12)}`,
      name,
      cropNameBn,
      areaDecimal: parseFloat(areaDecimal) || 20,
      location,
      healthStatus: "good",
      lastDiagnosisDate: "আজকের তারিখ",
    };
    addPlot(newPlot);
    setName("");
    setShowAddForm(false);
    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-card border border-emerald-500/20 shadow-sm">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Sprout className="h-5 w-5 text-emerald-600" />
            <span>{isBn ? "আমার খামার ও জমির তথ্য" : "My Farm Plots & Fields"}</span>
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            {isBn
              ? "আপনার নিবন্ধিত ফসলি জমি, জমির স্বাস্থ্য ও সাম্প্রতিক ডায়াগনসিস ট্র্যাকিং"
              : "Manage your registered land plots, crop health status and diagnosis records"}
          </p>
          {isFetching && (
            <p className="text-[11px] text-primary flex items-center gap-1 mt-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              {isBn ? "ব্যাকএন্ড থেকে জমির তথ্য আনা হচ্ছে..." : "Loading farms from server..."}
            </p>
          )}
          {hasFetched && backendPlots.length > 0 && (
            <p className="text-[11px] text-emerald-600 flex items-center gap-1 mt-1">
              <CheckCircle2 className="h-3 w-3" />
              {isBn ? `ব্যাকএন্ড থেকে ${backendPlots.length}টি জমি লোড হয়েছে` : `${backendPlots.length} plots loaded from server`}
            </p>
          )}
        </div>

        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-emerald-600 hover:bg-emerald-700 font-medium text-xs gap-1.5 self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>{isBn ? "নতুন জমি যুক্ত করুন" : "Add New Plot"}</span>
        </Button>
      </div>

      {/* Add New Plot Form Drawer/Card */}
      {showAddForm && (
        <Card className="border-emerald-500/30 bg-emerald-50/30 dark:bg-emerald-950/20 animate-in fade-in slide-in-from-top-4 duration-200">
          <CardContent className="p-5">
            <h3 className="text-sm font-semibold mb-3 text-emerald-950 dark:text-emerald-100">
              {isBn ? "নতুন জমির বিবরণ লিখুন:" : "Enter New Plot Details:"}
            </h3>
            <form onSubmit={handleCreatePlot} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  {isBn ? "জমির নাম/চিহ্ন" : "Plot Name"}
                </label>
                <Input
                  placeholder={isBn ? "যেমন: উত্তর পাড়ার আলু জমি" : "e.g. North Potato Field"}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="text-xs h-9"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  {isBn ? "বর্তমান ফসল" : "Current Crop"}
                </label>
                <select
                  value={cropNameBn}
                  onChange={(e) => setCropNameBn(e.target.value)}
                  className="w-full text-xs h-9 rounded-md border border-input bg-background px-2"
                >
                  <option value="আলু">আলু (Potato)</option>
                  <option value="ধান">ধান (Rice)</option>
                  <option value="টমেটো">টমেটো (Tomato)</option>
                  <option value="গম">গম (Wheat)</option>
                  <option value="ভুট্টা">ভুট্টা (Maize)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  {isBn ? "আয়তন (শতাংশ)" : "Area (Decimal)"}
                </label>
                <Input
                  type="number"
                  placeholder="30"
                  value={areaDecimal}
                  onChange={(e) => setAreaDecimal(e.target.value)}
                  className="text-xs h-9"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  {isBn ? "অবস্থান" : "Location"}
                </label>
                <Input
                  placeholder={isBn ? "শেরপুর, বগুড়া" : "Sherpur, Bogra"}
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="text-xs h-9"
                  required
                />
              </div>

              <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddForm(false)}
                  className="text-xs"
                >
                  {isBn ? "বাতিল" : "Cancel"}
                </Button>
                <Button type="submit" disabled={isSubmitting} size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-xs">
                  {isSubmitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : (isBn ? "সংরক্ষণ করুন" : "Save Plot")}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Plots Grid */}
      {displayPlots.length === 0 ? (
        <Card className="border border-dashed border-border bg-card/40 p-8 text-center space-y-3">
          <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 text-emerald-600 mx-auto flex items-center justify-center">
            <Sprout className="h-6 w-6" />
          </div>
          <h3 className="font-bold text-base text-foreground">
            {isBn ? "এখনো কোনো জমি যোগ করা হয়নি" : "No Farmlands Added Yet"}
          </h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            {isBn
              ? "আপনার চাষকৃত ফসলের জমি যুক্ত করে নিয়মিত ফসলের স্বাস্থ্য ও ডায়াগনসিস হিস্ট্রি ট্র্যাক করুন।"
              : "Register your farmlands to monitor crop health and track historical diagnoses."}
          </p>
          <Button
            size="sm"
            onClick={() => setShowAddForm(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            {isBn ? "প্রথম জমি যোগ করুন" : "Add Your First Plot"}
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayPlots.map((plot) => (
          <Card
            key={plot.id}
            className="hover:shadow-md transition-all border-border hover:border-emerald-500/40"
          >
            <CardContent className="p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-base text-foreground">{plot.name}</h3>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                    <MapPin className="h-3.5 w-3.5 text-emerald-600" />
                    <span>{plot.location}</span>
                  </div>
                </div>

                <Badge
                  variant="outline"
                  className={
                    plot.healthStatus === "good"
                      ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30"
                      : plot.healthStatus === "warning"
                      ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                      : "bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30"
                  }
                >
                  {plot.healthStatus === "good"
                    ? isBn
                      ? "সুস্থ ফসল"
                      : "Healthy"
                    : isBn
                    ? "সতর্কতা / আক্রান্ত"
                    : "Warning"}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-2 p-3 bg-muted/60 rounded-xl text-xs">
                <div>
                  <span className="text-muted-foreground block">{isBn ? "ফসল:" : "Crop:"}</span>
                  <span className="font-semibold text-foreground">{plot.cropNameBn}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">{isBn ? "জমির আয়তন:" : "Area:"}</span>
                  <span className="font-semibold text-foreground">{plot.areaDecimal} {isBn ? "শতাংশ" : "decimal"}</span>
                </div>
                <div className="col-span-2 pt-1 border-t border-border/50 flex items-center justify-between text-[11px]">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {isBn ? "সর্বশেষ পরীক্ষা:" : "Last Exam:"}
                  </span>
                  <span className="font-medium text-foreground">{plot.lastDiagnosisDate}</span>
                </div>
              </div>

              <div className="pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (plot.cropNameBn.includes("আলু")) setSelectedCrop("potato", "আলু");
                    else if (plot.cropNameBn.includes("টমেটো")) setSelectedCrop("tomato", "টমেটো");
                    else setSelectedCrop("chili", "মরিচ");
                  }}
                  className="w-full text-xs font-medium text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 border-emerald-500/30"
                >
                  {isBn ? "এই জমির রোগ নির্ণয় করুন 🔍" : "Diagnose this plot"}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      )}
    </div>
  );
}
