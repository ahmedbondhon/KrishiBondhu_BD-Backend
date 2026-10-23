"use client";

import React, { useState, useRef } from "react";
import { useAppStore } from "@/store/useAppStore";
import { useDiagnoseCropMutation } from "@/hooks/useDiagnosis";
import { CROPS } from "@/components/CropSelector";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BACKEND_URL } from "@/lib/api";
import {
  UploadCloud,
  Camera,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Image as ImageIcon,
  Check,
  RefreshCw,
} from "lucide-react";

const SYMPTOMS_LIST = [
  { id: "brown_spots", bn: "পাতায় বাদামী/কালো দাগ", en: "Brown/Black leaf spots" },
  { id: "yellowing", bn: "পাতা হলুদ হয়ে যাওয়া", en: "Yellowing chlorosis" },
  { id: "curling", bn: "পাতা কোঁকড়ানো বা মুচড়ে যাওয়া", en: "Leaf curling/wilting" },
  { id: "powdery", bn: "পাতায় সাদা পাউডারের মতো আবরণ", en: "White powdery mildew" },
  { id: "stem_rot", bn: "কাণ্ড বা গোড়া পচে যাওয়া", en: "Stem/collar rot" },
  { id: "stunted", bn: "গাছের বৃদ্ধি স্থবির হয়ে যাওয়া", en: "Stunted growth" },
];

export default function DiagnosisUploader() {
  const {
    selectedCrop,
    selectedCropBn,
    setSelectedCrop,
    selectedSymptoms,
    toggleSymptom,
    activeImage,
    setActiveImage,
    language,
  } = useAppStore();

  const isBn = language === "bn";
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isDetectingCrop, setIsDetectingCrop] = useState(false);
  const [autoDetectNotice, setAutoDetectNotice] = useState<string | null>(null);

  const diagnoseMutation = useDiagnoseCropMutation();

  // Pick default sample image matching the selected crop
  const currentCropObj = CROPS.find((c) => c.id === selectedCrop) || CROPS[0];
  const effectiveImage = activeImage || currentCropObj.sampleImg;

  const cases = useAppStore((state) => state.cases);
  const existingCaseForImage = cases.find(
    (item) =>
      (item.rawImage && item.rawImage === effectiveImage) ||
      item.imageUrl === effectiveImage
  );

  const processAndAutoDetect = (dataUrl: string, mime?: string) => {
    setActiveImage(dataUrl);
    setAutoDetectNotice(null);
    setIsDetectingCrop(true);

    fetch(`${BACKEND_URL}/api/v1/files/verify-crop-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_base64: dataUrl,
        selected_crop: selectedCrop,
        mime_type: mime || "image/jpeg",
        strict_crop_match: false,
      }),
    })
      .then((res) => res.json())
      .then((json) => {
        if (json?.success && json?.data?.detected_crop) {
          const detected = json.data.detected_crop;
          const target = CROPS.find((c) => c.id === detected);
          if (target && target.id !== selectedCrop) {
            setSelectedCrop(target.id, target.nameBn);
            setAutoDetectNotice(
              isBn
                ? `✨ AI ছবি দেখে স্বয়ংক্রিয়ভাবে '${target.nameBn}' নির্বাচন করেছে!`
                : `✨ AI auto-selected '${target.nameEn}' from image!`
            );
          } else if (target) {
            setAutoDetectNotice(
              isBn
                ? `✅ '${target.nameBn}'-এর পাতা নিশ্চিত করা হয়েছে`
                : `✅ Specimen confirmed as '${target.nameEn}'`
            );
          }
        }
      })
      .catch((err) => {
        console.warn("Auto-detection background error:", err);
      })
      .finally(() => {
        setIsDetectingCrop(false);
      });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        processAndAutoDetect(dataUrl, file.type);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStartAnalysis = () => {
    diagnoseMutation.mutate({
      crop: selectedCrop,
      cropBn: selectedCropBn,
      image: effectiveImage,
      symptoms: selectedSymptoms,
    });
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-foreground flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-bold">
              ২
            </span>
            {isBn
              ? "আক্রান্ত পাতার ছবি তুলুন বা আপলোড করুন"
              : "Upload or Capture Leaf Photo"}
          </label>
          <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {isBn ? "HD ইমেজ সাপোর্ট" : "High Resolution"}
          </span>
        </div>

        {/* Upload Container */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            const file = e.dataTransfer.files?.[0];
            if (file) {
              const reader = new FileReader();
              reader.onload = () => {
                const dataUrl = reader.result as string;
                processAndAutoDetect(dataUrl, file.type);
              };
              reader.readAsDataURL(file);
            }
          }}
          className={`relative border-2 border-dashed rounded-2xl p-4 sm:p-6 transition-all duration-200 overflow-hidden text-center ${
            dragActive
              ? "border-primary bg-primary/5"
              : "border-border/80 bg-card/40 hover:border-emerald-500/50 hover:bg-card/70"
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />

          {effectiveImage ? (
            <div className="flex flex-col sm:flex-row items-center gap-5">
              <div className="relative group w-full sm:w-48 h-40 sm:h-36 rounded-xl overflow-hidden border border-border bg-black/10 shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={effectiveImage}
                  alt="Leaf specimen"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => fileInputRef.current?.click()}
                    className="h-8 text-xs font-medium"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    {isBn ? "পরিবর্তন" : "Change"}
                  </Button>
                </div>
              </div>

              <div className="text-left space-y-2 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="success" className="text-xs">
                    {isBn ? "নমুনা প্রস্তুত" : "Specimen Ready"}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-semibold">
                    {selectedCropBn}
                  </span>
                  {isDetectingCrop && (
                    <Badge variant="outline" className="text-[11px] animate-pulse border-primary/40 text-primary flex items-center gap-1 font-normal">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      {isBn ? "AI ফসল শনাক্ত করছে..." : "AI Detecting crop..."}
                    </Badge>
                  )}
                  {autoDetectNotice && !isDetectingCrop && (
                    <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 text-[11px] font-normal">
                      {autoDetectNotice}
                    </Badge>
                  )}
                </div>
                <h4 className="font-semibold text-sm sm:text-base text-foreground">
                  {isBn
                    ? "আক্রান্ত অংশের সুস্পষ্ট ছবি গৃহীত হয়েছে"
                    : "High-clarity crop image loaded"}
                </h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {isBn
                    ? "AI মডেলটি পাতায় ছত্রাক, ব্যাকটেরিয়া বা পুষ্টিহীনতার লক্ষণ স্ক্যান করতে প্রস্তুত।"
                    : "Ready to run multi-spectral computer vision inference for diseases."}
                </p>

                <div className="flex flex-wrap gap-2 pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    className="h-8 text-xs"
                  >
                    <UploadCloud className="h-3.5 w-3.5 mr-1.5" />
                    {isBn ? "নিজের ছবি দিন" : "Upload Custom"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setActiveImage(currentCropObj.sampleImg)}
                    className="h-8 text-xs text-muted-foreground"
                  >
                    {isBn ? "ডিফল্ট নমুনা ব্যবহার" : "Use Sample Specimen"}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="cursor-pointer py-8 flex flex-col items-center justify-center space-y-3"
            >
              <div className="h-14 w-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                <Camera className="h-7 w-7" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {isBn
                    ? "ছবি ক্লিক করে নির্বাচন করুন অথবা টেনে আনুন"
                    : "Click to select or drag and drop leaf photo"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  PNG, JPG, WEBP (সর্বোচ্চ ১০MB)
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Symptom Checklist */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-foreground flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-bold">
              ৩
            </span>
            {isBn
              ? "লক্ষণগুলো চিহ্নিত করুন (ঐচ্ছিক)"
              : "Check Visible Symptoms (Optional)"}
          </span>
          <span className="text-xs text-muted-foreground font-normal">
            {isBn ? "নির্ভুলতা বাড়াতে সাহায্য করে" : "Boosts AI Confidence"}
          </span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
          {SYMPTOMS_LIST.map((sym) => {
            const isChecked = selectedSymptoms.includes(sym.id);
            return (
              <button
                key={sym.id}
                type="button"
                onClick={() => toggleSymptom(sym.id)}
                className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-left text-xs transition-all ${
                  isChecked
                    ? "bg-primary/10 border-primary text-foreground font-medium"
                    : "bg-card/60 border-border/70 text-muted-foreground hover:bg-card hover:text-foreground"
                }`}
              >
                <div
                  className={`h-4 w-4 rounded flex items-center justify-center border transition-colors ${
                    isChecked
                      ? "bg-primary border-primary text-primary-foreground"
                      : "border-muted-foreground/40 bg-background"
                  }`}
                >
                  {isChecked && <Check className="h-3 w-3 stroke-[3]" />}
                </div>
                <span>{isBn ? sym.bn : sym.en}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Trigger Button & Loading State */}
      <div className="pt-2">
        <Button
          onClick={handleStartAnalysis}
          disabled={diagnoseMutation.isPending}
          size="lg"
          variant="emerald"
          className="w-full text-base font-bold shadow-lg shadow-emerald-600/25 py-6 rounded-xl"
        >
          {diagnoseMutation.isPending ? (
            <span className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>
                {isBn
                  ? "ChashiGuard AI বিশ্লেষণ করছে..."
                  : "ChashiGuard AI Analyzing..."}
              </span>
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              <span>
                {existingCaseForImage
                  ? isBn
                    ? "পুনরায় রোগ নির্ণয় ও ফলাফল হালনাগাদ করুন"
                    : "Re-run & Update Diagnosis"
                  : isBn
                  ? "ChashiGuard AI দিয়ে রোগ নির্ণয় করুন"
                  : "Run ChashiGuard AI Diagnosis"}
              </span>
            </span>
          )}
        </Button>

        {existingCaseForImage && !diagnoseMutation.isPending && (
          <p className="mt-2 text-center text-[11px] text-muted-foreground flex items-center justify-center gap-1.5 font-medium">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
            <span>
              {isBn
                ? `এই ছবির রিপোর্ট #${existingCaseForImage.caseNumber} সংরক্ষিত আছে (বারবার চাপলেও ডুপ্লিকেট হবে না)`
                : `Report #${existingCaseForImage.caseNumber} is stored for this image (no duplicates)`}
            </span>
          </p>
        )}

        {diagnoseMutation.isPending && (
          <div className="mt-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 text-center animate-pulse">
            {isBn
              ? "চিত্র প্রক্রিয়াকরণ ➔ লক্ষণ শনাক্তকরণ ➔ কৃষি বিশেষজ্ঞ ডাটাবেস যাচাই..."
              : "Visual processing ➔ Symptom mapping ➔ Advisory database matching..."}
          </div>
        )}

        {diagnoseMutation.isError && (() => {
          const err = diagnoseMutation.error as any;
          const errMsg: string = err?.message || "";
          const isMismatch =
            err?.errorCode === "REJECT_CROP_MISMATCH" ||
            errMsg.includes("ফসলের অমিল") ||
            errMsg.includes("অমিল");

          const detectedCropId =
            err?.detectedCrop ||
            (errMsg.includes("টমেটো")
              ? "tomato"
              : errMsg.includes("আলু")
              ? "potato"
              : errMsg.includes("মরিচ")
              ? "chili"
              : null);

          const detectedCropObj = CROPS.find((c) => c.id === detectedCropId);

          return (
            <div
              className={`mt-4 p-4 rounded-xl border flex items-start gap-3 shadow-sm animate-in fade-in slide-in-from-top-2 ${
                isMismatch
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200"
                  : "bg-destructive/10 border-destructive/20 text-destructive"
              }`}
            >
              <AlertCircle
                className={`h-5 w-5 shrink-0 mt-0.5 ${
                  isMismatch ? "text-amber-600 dark:text-amber-400" : "text-destructive"
                }`}
              />
              <div className="space-y-2 text-left flex-1">
                <h5 className="font-semibold text-sm">
                  {isMismatch
                    ? (isBn ? "ফসলের অমিল শনাক্ত হয়েছে (Crop Mismatch)" : "Crop Mismatch Detected")
                    : (isBn ? "ছবি যাচাইকরণ ব্যর্থ হয়েছে (Gatekeeper Rejection)" : "Image Verification Failed")}
                </h5>
                <p className="text-xs leading-relaxed opacity-90">
                  {errMsg ||
                    (isBn
                      ? "এটি কোনো ফসলের ছবি নয়। অনুগ্রহ করে শুধুমাত্র আক্রান্ত ফসলের পাতার পরিষ্কার ছবি তুলে আপলোড করুন।"
                      : "Not a valid crop image. Please upload a clear photo of an infected crop leaf.")}
                </p>

                {isMismatch && detectedCropObj && detectedCropObj.id !== selectedCrop && (
                  <div className="pt-1.5 flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs h-8 px-3 shadow flex items-center gap-1.5"
                      onClick={() => {
                        setSelectedCrop(detectedCropObj.id, detectedCropObj.nameBn);
                        diagnoseMutation.reset();
                        diagnoseMutation.mutate({
                          crop: detectedCropObj.id,
                          cropBn: detectedCropObj.nameBn,
                          image: effectiveImage,
                          symptoms: selectedSymptoms,
                        });
                      }}
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      {isBn
                        ? `'${detectedCropObj.nameBn}' হিসেবে রোগ নির্ণয় করুন`
                        : `Switch to '${detectedCropObj.nameEn}' & Analyze`}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="text-xs h-8 px-3 border-amber-500/40 text-amber-800 dark:text-amber-300 hover:bg-amber-500/10"
                      onClick={() => {
                        setSelectedCrop(detectedCropObj.id, detectedCropObj.nameBn);
                        diagnoseMutation.reset();
                      }}
                    >
                      {isBn ? `'${detectedCropObj.nameBn}' নির্বাচন করুন` : `Select ${detectedCropObj.nameEn}`}
                    </Button>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
