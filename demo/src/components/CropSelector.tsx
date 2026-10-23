"use client";

import React from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CropOption {
  id: string;
  nameBn: string;
  nameEn: string;
  scientificName: string;
  icon: string;
  varietiesBn: string[];
  commonDiseasesBn: string;
  sampleImg: string;
}

export const CROPS: CropOption[] = [
  {
    id: "potato",
    nameBn: "আলু",
    nameEn: "Potato",
    scientificName: "Solanum tuberosum",
    icon: "🥔",
    varietiesBn: ["গ্রানোলা (Granola)", "অ্যাস্টারিক্স (Asterix)", "কার্ডিনাল (Cardinal)"],
    commonDiseasesBn: "নাবী ধসা, আগাম ধসা, মোজাইক",
    sampleImg:
      "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: "tomato",
    nameBn: "টমেটো",
    nameEn: "Tomato",
    scientificName: "Solanum lycopersicum",
    icon: "🍅",
    varietiesBn: ["বারি টমেটো ১৪ (BARI Tomato 14)", "বারি টমেটো ১৫ (BARI Tomato 15)"],
    commonDiseasesBn: "পাতা কোঁকড়ানো, আর্লি ব্লাইট, ব্যাকটেরিয়াল উইল্ট",
    sampleImg:
      "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: "chili",
    nameBn: "মরিচ",
    nameEn: "Chili",
    scientificName: "Capsicum annuum",
    icon: "🌶️",
    varietiesBn: ["বারি ঝালকা (BARI Jhalka)", "বগুড়া স্থানীয় ঝাল (Local Bogura)"],
    commonDiseasesBn: "অ্যানথ্রাকনোজ (ফল পচা), লিফ কার্ল (পাতা কোঁকড়ানো)",
    sampleImg:
      "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=600&q=80",
  },
];

export default function CropSelector() {
  const { selectedCrop, setSelectedCrop, setActiveImage, language } = useAppStore();
  const isBn = language === "bn";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-bold">
            ১
          </span>
          {isBn ? "আক্রান্ত ফসল নির্বাচন করুন" : "Select Affected Crop"}
        </label>
        <span className="text-xs text-muted-foreground">
          {isBn ? "মডেল অপ্টিমাইজড" : "Optimized AI Model"}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {CROPS.map((crop) => {
          const isSelected = selectedCrop === crop.id;
          return (
            <button
              key={crop.id}
              type="button"
              onClick={() => {
                setSelectedCrop(crop.id, isBn ? crop.nameBn : crop.nameEn);
              }}
              className={`relative flex flex-col items-center justify-center p-3.5 rounded-xl border transition-all text-center group ${
                isSelected
                  ? "bg-primary/10 border-primary shadow-sm ring-2 ring-primary/20"
                  : "bg-card/70 border-border/80 hover:border-emerald-400/50 hover:bg-card hover:shadow"
              }`}
            >
              <div className="text-3xl mb-1.5 transition-transform duration-200 group-hover:scale-110">
                {crop.icon}
              </div>
              <span className="text-sm font-bold text-foreground">
                {isBn ? crop.nameBn : crop.nameEn}
              </span>
              <span className="text-[11px] italic text-muted-foreground">
                {crop.scientificName}
              </span>
              <div className="mt-1.5 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium line-clamp-1">
                {crop.varietiesBn.join(", ")}
              </div>

              {isSelected && (
                <div className="absolute top-2 right-2 h-2.5 w-2.5 rounded-full bg-primary ring-2 ring-background" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
