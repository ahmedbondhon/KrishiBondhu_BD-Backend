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

      // 1. Upload crop picture directly to Supabase storage 'crops' folder
      let finalCropImageUrl = existingCase?.imageUrl || params.image;
      let blob: Blob | null = null;
      if (params.image && params.image.startsWith("data:")) {
        try {
          blob = dataURLtoBlob(params.image);
          if (!existingCase) {
            const uploadRes = await uploadToSupabaseStorage("crops", blob);
            if (uploadRes?.publicUrl) {
              finalCropImageUrl = uploadRes.publicUrl;
            }
          }
        } catch (uploadErr) {
          console.warn("Image upload warning:", uploadErr);
        }
      }

      // 2. Call REAL FastAPI Backend Diagnosis API
      const token = typeof window !== "undefined" ? localStorage.getItem("kb_access_token") : null;
      let diagnosisData: any = null;

      try {
        const formData = new FormData();
        const fileBlob = blob || (params.image.startsWith("data:") ? dataURLtoBlob(params.image) : new Blob([]));
        formData.append("image", fileBlob, `${effectiveCrop}_specimen.jpg`);
        formData.append("crop_name", effectiveCrop);
        if (params.symptoms && params.symptoms.length > 0) {
          formData.append("notes", `লক্ষণসমূহ: ${params.symptoms.join(", ")}`);
        }

        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const apiRes = await fetch(`${BACKEND_URL}/api/v1/quick-diagnosis`, {
          method: "POST",
          headers,
          body: formData,
        });

        if (apiRes.ok) {
          const resJson = await apiRes.json();
          diagnosisData = resJson.data || resJson;
        } else {
          const errJson = await apiRes.json().catch(() => ({}));
          const errMsg =
            errJson?.detail?.message_bn ||
            errJson?.detail ||
            errJson?.message ||
            "সার্ভার থেকে রোগ বিশ্লেষণ সম্পন্ন করা যায়নি।";
          throw new Error(typeof errMsg === "string" ? errMsg : JSON.stringify(errMsg));
        }
      } catch (backendErr: any) {
        if (backendErr?.message && !backendErr.message.includes("Failed to fetch") && !backendErr.message.includes("NetworkError")) {
          throw backendErr;
        }
        // If backend server is offline, inform the user clearly
        throw new Error("ব্যাকএন্ড সার্ভার (http://localhost:8000) সচল নেই। অনুগ্রহ করে ব্যাকএন্ড সার্ভার চালু করুন।");
      }

      const caseNumber = diagnosisData?.case_number || `KB-2026-${Math.floor(100000 + Math.random() * 900000)}`;
      const diseaseName = diagnosisData?.issue_name_en || diagnosisData?.issue_name_bn || "Diagnosed Plant Condition";
      const diseaseNameBn = diagnosisData?.issue_name_bn || diagnosisData?.issue_name_en || "শনাক্তকৃত রোগ";
      const confidence = Number(diagnosisData?.confidence_score ?? 0.90);
      const requiresExpert = Boolean(diagnosisData?.requires_expert_review ?? (confidence < 0.75));

      const advisory = diagnosisData?.advisory || {};
      const treatmentBn =
        advisory.detailed_treatment_bn ||
        advisory.summary_bn ||
        diagnosisData?.treatment_bn ||
        "কৃষি কর্মকর্তার পরামর্শ অনুযায়ী অনুমোদিত বালাইনাশক স্প্রে করুন।";
      const preventionBn =
        advisory.preventive_measures_bn ||
        diagnosisData?.prevention_bn ||
        "জমি পরিষ্কার রাখুন এবং সুস্থ প্রত্যয়িত বীজ ব্যবহার করুন।";

      const newCase: DiagnosisCase = {
        id: diagnosisData?.case_id || (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `case-${Date.now()}`),
        caseNumber: caseNumber,
        cropName: effectiveCrop,
        cropNameBn: effectiveCropBn,
        diseaseName: diseaseName,
        diseaseNameBn: diseaseNameBn,
        confidence: confidence,
        status: requiresExpert ? "pending_expert" : "analyzed",
        imageUrl: finalCropImageUrl,
        rawImage: params.image,
        createdAt: new Date().toLocaleDateString("bn-BD", { hour: "2-digit", minute: "2-digit" }),
        treatmentBn: treatmentBn,
        preventionBn: preventionBn,
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
  const setCases = useAppStore((state) => state.setCases);

  return useQuery({
    queryKey: ["casesHistory"],
    queryFn: async () => {
      const token = typeof window !== "undefined" ? localStorage.getItem("kb_access_token") : null;
      if (!token) return cases;

      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/diagnosis-cases?limit=100`, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        });
        if (res.ok) {
          const data = await res.json();
          const items: DiagnosisCase[] = (data?.data || []).map(
            (c: {
              id: string;
              case_number: string;
              status: string;
              created_at?: string;
              urgency_level?: string;
              crop_id?: string;
              [key: string]: unknown;
            }) => ({
              id: c.id,
              caseNumber: c.case_number,
              cropName: c.crop_id || "crop",
              cropNameBn: c.crop_id === "potato" ? "আলু" : c.crop_id === "tomato" ? "টমেটো" : c.crop_id === "chili" ? "মরিচ" : "ফসল",
              diseaseName: "Diagnosed Condition",
              diseaseNameBn: "রোগ নির্ণয় সম্পন্ন",
              confidence: 0.90,
              status: c.status as DiagnosisCase["status"],
              imageUrl: "",
              createdAt: c.created_at ? new Date(c.created_at).toLocaleDateString("bn-BD") : "—",
              treatmentBn: "—",
              preventionBn: "—",
            })
          );
          if (items.length > 0) {
            setCases(items);
            return items;
          }
          return [];
        }
      } catch {
        // Network error — return empty or local
      }
      return cases;
    },
    initialData: cases,
    staleTime: 60_000,
  });
}
