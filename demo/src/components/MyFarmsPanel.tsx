"use client";

import React, { useState } from "react";
import { useAppStore, FarmPlot } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
} from "lucide-react";

export default function MyFarmsPanel() {
  const { plots, addPlot, language, setSelectedCrop } = useAppStore();
  const isBn = language === "bn";

  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState("");
  const [cropNameBn, setCropNameBn] = useState("আলু");
  const [areaDecimal, setAreaDecimal] = useState("30");
  const [location, setLocation] = useState("শিবগঞ্জ, বগুড়া");

  const handleCreatePlot = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

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
                <Button type="submit" size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-xs">
                  {isBn ? "সংরক্ষণ করুন" : "Save Plot"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Plots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plots.map((plot) => (
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
    </div>
  );
}
