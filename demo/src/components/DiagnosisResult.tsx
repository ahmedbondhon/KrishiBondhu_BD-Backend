"use client";

import React, { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle,
  FileCheck2,
  Share2,
  Volume2,
  Stethoscope,
  ShieldAlert,
  ArrowRight,
  Clock,
  Sparkles,
} from "lucide-react";

export default function DiagnosisResult() {
  const { activeCase, updateCaseStatus, language } = useAppStore();
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [copied, setCopied] = useState(false);

  const isBn = language === "bn";

  if (!activeCase) {
    return null;
  }

  const isHighConfidence = activeCase.confidence >= 0.75;
  const isPendingExpert = activeCase.status === "pending_expert";
  const isReviewed = activeCase.status === "reviewed";

  const handleRequestExpert = () => {
    updateCaseStatus(
      activeCase.id,
      "pending_expert",
      "কৃষিবিদ পর্যালোচনার জন্য জমা দেওয়া হয়েছে।"
    );
  };

  const handleSimulateAudio = () => {
    setIsPlayingAudio(true);
    setTimeout(() => setIsPlayingAudio(false), 3000);
  };

  const handleShare = () => {
    navigator.clipboard?.writeText(
      `কৃষিবন্ধু ChashiGuard রিপোর্ট #${activeCase.caseNumber}: ${activeCase.cropNameBn} - ${activeCase.diseaseNameBn}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="border-2 border-emerald-500/30 bg-card/95 shadow-xl shadow-emerald-900/5 overflow-hidden transition-all">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-600 via-green-600 to-teal-700 p-4 text-white">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs bg-white/20 backdrop-blur px-2.5 py-1 rounded-md font-bold">
              {activeCase.caseNumber}
            </span>
            <span className="text-xs text-emerald-100 flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {activeCase.createdAt}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isReviewed ? (
              <Badge className="bg-blue-500 text-white font-medium">
                {isBn ? "কৃষিবিদ দ্বারা অনুমোদিত" : "Expert Verified"}
              </Badge>
            ) : isPendingExpert ? (
              <Badge className="bg-amber-400 text-amber-950 font-bold">
                {isBn ? "বিশেষজ্ঞ পর্যালোচনায়" : "Under Expert Review"}
              </Badge>
            ) : (
              <Badge className="bg-emerald-400 text-emerald-950 font-bold">
                {isBn ? "AI নির্ণয় সম্পন্ন" : "AI Diagnosed"}
              </Badge>
            )}
          </div>
        </div>
      </div>

      <CardContent className="p-5 sm:p-6 space-y-6">
        {/* Diagnosis Header with Confidence */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <Badge variant="outline" className="text-xs font-normal">
                {activeCase.cropNameBn}
              </Badge>
              {activeCase.autoSelected && (
                <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 text-[11px] font-medium">
                  ✨ {isBn ? "স্বয়ংক্রিয় শনাক্তকৃত ফসল" : "Auto-detected Crop"}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs text-muted-foreground italic">
                {activeCase.diseaseName}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-foreground">
              {activeCase.diseaseNameBn}
            </h2>
            {activeCase.autoSelected && activeCase.autoSelectMessageBn && (
              <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1 flex items-center gap-1.5 font-medium">
                <span>✨</span>
                <span>{activeCase.autoSelectMessageBn}</span>
              </p>
            )}
          </div>

          {/* Confidence Meter */}
          <div className="flex items-center gap-3 bg-muted/60 px-4 py-2.5 rounded-xl border border-border">
            <div className="text-right">
              <span className="text-[11px] text-muted-foreground block">
                {isBn ? "AI আত্মবিশ্বাস" : "AI Confidence"}
              </span>
              <span
                className={`text-lg font-black ${
                  isHighConfidence ? "text-emerald-600" : "text-amber-600"
                }`}
              >
                {Math.round(activeCase.confidence * 100)}%
              </span>
            </div>
            <div className="w-14 h-2.5 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isHighConfidence ? "bg-emerald-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.round(activeCase.confidence * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Prescription & Treatment */}
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2">
            <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
              <FileCheck2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              {isBn
                ? "জরুরি চিকিৎসা ও প্রেসক্রিপশন"
                : "Immediate Treatment & Prescription"}
            </h3>
            <p className="text-sm text-foreground/90 leading-relaxed font-medium">
              {activeCase.treatmentBn}
            </p>
          </div>

          {/* Prevention Advisory */}
          <div className="p-4 rounded-xl bg-muted/40 border border-border/80 space-y-2">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-600" />
              {isBn
                ? "ভবিষ্যতের জন্য প্রতিরোধমূলক পরামর্শ"
                : "Preventive Measures"}
            </h3>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              {activeCase.preventionBn}
            </p>
          </div>

          {/* Expert Notes if any */}
          {activeCase.expertNotesBn && (
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 space-y-2">
              <h3 className="text-sm font-bold text-blue-900 dark:text-blue-200 flex items-center gap-2">
                <Stethoscope className="h-4 w-4 text-blue-600" />
                {isBn ? "কৃষিবিদের বিশেষ মন্তব্য" : "Agronomist's Note"}
              </h3>
              <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed">
                {activeCase.expertNotesBn}
              </p>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSimulateAudio}
              className="text-xs font-medium"
            >
              <Volume2
                className={`h-4 w-4 mr-1.5 ${
                  isPlayingAudio ? "text-emerald-600 animate-bounce" : ""
                }`}
              />
              {isPlayingAudio
                ? isBn
                  ? "পড়া হচ্ছে..."
                  : "Speaking..."
                : isBn
                ? "বাংলায় শুনুন"
                : "Listen Audio"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
              className="text-xs font-medium"
            >
              <Share2 className="h-4 w-4 mr-1.5" />
              {copied
                ? isBn
                  ? "কপি হয়েছে!"
                  : "Copied!"
                : isBn
                ? "শেয়ার করুন"
                : "Share Report"}
            </Button>
          </div>

          {!isReviewed && !isPendingExpert && (
            <Button
              onClick={handleRequestExpert}
              variant="secondary"
              size="sm"
              className="text-xs font-semibold text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/80 hover:bg-emerald-200"
            >
              <Stethoscope className="h-3.5 w-3.5 mr-1.5" />
              {isBn
                ? "বিশেষজ্ঞ যাচাই অনুরোধ পাঠান"
                : "Request Human Expert Review"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
