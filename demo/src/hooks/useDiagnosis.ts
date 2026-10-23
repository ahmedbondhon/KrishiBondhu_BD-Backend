import { useMutation, useQuery } from "@tanstack/react-query";
import { useAppStore, DiagnosisCase } from "@/store/useAppStore";
import { uploadToSupabaseStorage, dataURLtoBlob } from "@/lib/supabaseStorage";

import { BACKEND_URL } from "@/lib/api";

interface AnalyzeParams {
  crop: string;
  cropBn: string;
  image: string;
  symptoms: string[];
}

export function useDiagnoseCropMutation() {
  const addCase = useAppStore((state) => state.addCase);
  const setActiveCase = useAppStore((state) => state.setActiveCase);

  return useMutation({
    mutationFn: async (params: AnalyzeParams): Promise<DiagnosisCase> => {
      let effectiveCrop = params.crop;
      let effectiveCropBn = params.cropBn;
      let isAutoSelected = false;
      let autoSelectMessageBn = "";

      // 0. Strict Agricultural Gatekeeper Verification: Reject selfies, human photos, non-crops, auto-select crops
      if (params.image && params.image.startsWith("data:")) {
        try {
          const verifyRes = await fetch(`${BACKEND_URL}/api/v1/files/verify-crop-image`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              image_base64: params.image,
              selected_crop: params.crop,
              mime_type: params.image.split(";")[0]?.replace("data:", "") || "image/jpeg",
              strict_crop_match: false, // Auto-selection enabled!
            }),
          });
          const verifyData = await verifyRes.json();
          if (!verifyRes.ok || verifyData.success === false) {
            const errDetail = verifyData?.error?.details?.[0];
            const errorMsg =
              errDetail?.message_bn ||
              verifyData?.error?.message_bn ||
              verifyData?.message ||
              verifyData?.error?.message ||
              "ছবিটি যাচাই করা যায়নি। অনুগ্রহ করে আক্রান্ত ফসলের পাতার পরিষ্কার ছবি তুলে আপলোড করুন।";
            const customErr: any = new Error(errorMsg);
            customErr.errorCode = verifyData?.error?.code || verifyData?.error_code || "REJECT_GATEKEEPER";
            customErr.detectedCrop = errDetail?.detected_crop;
            customErr.selectedCrop = errDetail?.selected_crop || params.crop;
            throw customErr;
          }

          if (verifyData?.data?.final_selected_crop) {
            effectiveCrop = verifyData.data.final_selected_crop;
            if (effectiveCrop === "tomato") effectiveCropBn = "টমেটো";
            else if (effectiveCrop === "potato") effectiveCropBn = "আলু";
            else if (effectiveCrop === "chili") effectiveCropBn = "মরিচ";

            if (verifyData.data.auto_selected || effectiveCrop !== params.crop) {
              isAutoSelected = true;
              autoSelectMessageBn =
                verifyData.data.message_bn ||
                `ছবি দেখে স্বয়ংক্রিয়ভাবে '${effectiveCropBn}' নির্বাচন করা হয়েছে।`;
              // Automatically sync the global store crop selection!
              useAppStore.getState().setSelectedCrop(effectiveCrop, effectiveCropBn);
            }
          }
        } catch (gatekeeperErr: any) {
          if (
            gatekeeperErr?.errorCode ||
            (gatekeeperErr instanceof Error && (
              gatekeeperErr.message.includes("ফসলের") ||
              gatekeeperErr.message.includes("ছবি") ||
              gatekeeperErr.message.includes("শনাক্ত") ||
              gatekeeperErr.message.includes("অমিল")
            ))
          ) {
            throw gatekeeperErr;
          }
          console.warn("Gatekeeper verification error:", gatekeeperErr);
        }
      }

      // Check if this picture was already diagnosed
      const existingCase = useAppStore.getState().cases.find((item) => {
        if (item.rawImage && item.rawImage === params.image) return true;
        if (item.imageUrl === params.image) return true;
        return false;
      });

      // 1. Upload crop picture directly to Supabase storage 'crops' folder (only once per picture)
      let finalCropImageUrl = existingCase?.imageUrl || params.image;
      if (!existingCase && params.image && params.image.startsWith("data:")) {
        try {
          const blob = dataURLtoBlob(params.image);
          const uploadRes = await uploadToSupabaseStorage("crops", blob);
          if (uploadRes?.publicUrl) {
            finalCropImageUrl = uploadRes.publicUrl;
          }
        } catch (uploadErr) {
          console.warn("Could not upload crop image to Supabase storage bucket, using data URL fallback:", uploadErr);
        }
      }

      // Simulate backend/AI service latency with realistic response
      await new Promise((res) => setTimeout(res, 1800));

      const isLowConfidence = params.symptoms.length === 0 && Math.random() < 0.2;
      const confidence = isLowConfidence ? 0.62 : 0.94;
      const randomNum = Math.floor(1000 + Math.random() * 9000);

      const diagnoses: Record<
        string,
        { name: string; nameBn: string; treatment: string; prevention: string }
      > = {
        potato: {
          name: "Late Blight (Phytophthora infestans)",
          nameBn: "আলুর নাবী ধসা (লেট ব্লাইট)",
          treatment:
            "ডাইমেথোমর্ফ বা ম্যানকোজেব জাতীয় ওষুধ প্রতি লিটার পানিতে ২ গ্রাম মিশিয়ে কুয়াশাচ্ছন্ন আবহাওয়ায় ৭ দিন পর পর স্প্রে করুন।",
          prevention:
            "রোগমুক্ত সার্টিফাইড বীজ ব্যবহার করুন, জমিতে পানি জমতে দেবেন না এবং নিয়মিত পর্যবেক্ষণ করুন।",
        },
        tomato: {
          name: "Early Blight (Alternaria solani)",
          nameBn: "টমেটোর আগাম ধসা রোগ",
          treatment:
            "রোভরাল বা রিডোমিল গোল্ড প্রতি লিটার পানিতে ২ গ্রাম হারে ১০ দিন পর পর ২-৩ বার স্প্রে করুন।",
          prevention:
            "নিচের আক্রান্ত পাতা ছেঁটে দিন এবং গাছের গোড়ায় সরাসরি পানি দেওয়া থেকে বিরত থাকুন।",
        },
        chili: {
          name: "Chili Anthracnose (Colletotrichum capsici)",
          nameBn: "মরিচের ফল পচা / অ্যানথ্রাকনোজ ও লিফ কার্ল",
          treatment:
            "প্রোপিকোনাজল বা ডাইফেনোকোনাজল প্রতি লিটার পানিতে ১ মিলি হারে স্প্রে করুন। সাদা মাছি দমনে ইমিডাক্লোপ্রিড দিন।",
          prevention:
            "সুস্থ ও রোগমুক্ত বীজ বপন করুন, জমিতে অতিরিক্ত আর্দ্রতা জমতে দেবেন না এবং নিয়মিত আগাছা পরিষ্কার রাখুন।",
        },
      };

      const selected = diagnoses[effectiveCrop] || diagnoses.potato;

      const newCaseId =
        existingCase?.id ||
        (typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `22000000-0000-0000-0000-${Date.now().toString().slice(-12)}`);

      const caseNumber = existingCase?.caseNumber || `KB-2026-00${randomNum}`;
      const createdAt =
        existingCase?.createdAt ||
        new Date().toLocaleDateString("bn-BD", {
          hour: "2-digit",
          minute: "2-digit",
        });

      const newCase: DiagnosisCase = {
        id: newCaseId,
        caseNumber: caseNumber,
        cropName: effectiveCrop,
        cropNameBn: effectiveCropBn,
        diseaseName: selected.name,
        diseaseNameBn: selected.nameBn,
        confidence: confidence,
        status: confidence < 0.75 ? "pending_expert" : "analyzed",
        imageUrl: finalCropImageUrl,
        rawImage: params.image,
        createdAt: createdAt,
        treatmentBn: selected.treatment,
        preventionBn: selected.prevention,
        autoSelected: isAutoSelected,
        autoSelectMessageBn: autoSelectMessageBn,
      };

      return newCase;
    },
    onSuccess: (data) => {
      addCase(data);
      setActiveCase(data);
    },
  });
}

export function useCasesHistoryQuery() {
  const cases = useAppStore((state) => state.cases);

  return useQuery({
    queryKey: ["casesHistory"],
    queryFn: async () => {
      return cases;
    },
    initialData: cases,
  });
}
