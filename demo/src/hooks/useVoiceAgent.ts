"use client";

/**
 * useVoiceAgent.ts
 * ================
 * KrishiBondhu Voice Command Agent — বাংলা ও English উভয় ভাষায় কাজ করে।
 *
 * সাপোর্টেড কমান্ড:
 *   - "রোগ নির্ণয়" / "diagnosis" / "scan crop"
 *   - "আমার জমি" / "farms" / "my farms"
 *   - "ইতিহাস" / "history" / "case history"
 *   - "হোম" / "home" / "dashboard"
 *   - "বিশেষজ্ঞ" / "expert" / "expert queue"
 *   - "অ্যাডমিন" / "admin"
 *   - "লগআউট" / "logout"
 *   - "বাংলা" / "english" / "language"
 *   - "ডার্ক মোড" / "dark mode" / "light mode"
 *   - "প্রোফাইল" / "profile"
 *   - "সাহায্য" / "help" / "কী কমান্ড আছে"
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/store/useAppStore";

export type VoiceAgentStatus =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "error";

interface UseVoiceAgentReturn {
  status: VoiceAgentStatus;
  transcript: string;
  lastResponse: string;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string) => void;
  executeCommand: (text: string) => void;
}

// ── Supported Commands ────────────────────────────────────
interface VoiceCommand {
  patterns: (string | RegExp)[];
  handler: (params: {
    router: ReturnType<typeof useRouter>;
    store: ReturnType<typeof useAppStore.getState>;
    speak: (t: string) => void;
    setLanguage: (lang: "bn" | "en") => void;
    transcript: string;
  }) => void;
  responseBn: string;
  responseEn: string;
}

function matchesCommand(transcript: string, patterns: (string | RegExp)[]): boolean {
  const lower = transcript.toLowerCase().trim();
  return patterns.some((p) => {
    if (typeof p === "string") return lower.includes(p.toLowerCase());
    return p.test(lower);
  });
}

// ── TTS Helper ────────────────────────────────────────────
let currentUtterance: SpeechSynthesisUtterance | null = null;

function speakText(text: string, lang: "bn" | "en") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = lang === "bn" ? "bn-BD" : "en-US";
  utter.rate = 0.9;
  utter.pitch = 1.1;
  currentUtterance = utter;
  window.speechSynthesis.speak(utter);
}

// ── Main Hook ────────────────────────────────────────────
export function useVoiceAgent(): UseVoiceAgentReturn {
  const router = useRouter();
  const { language, setLanguage, toggleTheme, isDark } = useAppStore();
  const isBn = language === "bn";

  const [status, setStatus] = useState<VoiceAgentStatus>("idle");
  const [transcript, setTranscript] = useState("");
  const [lastResponse, setLastResponse] = useState("");
  const [isSupported] = useState(() => {
    if (typeof window === "undefined") return false;
    const hasSpeechRecognition =
      "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
    return Boolean(hasSpeechRecognition && "speechSynthesis" in window);
  });

  const recognitionRef = useRef<InstanceType<typeof SpeechRecognition> | null>(null);
  const isListeningRef = useRef(false);

  // ── speak helper ─────────────────────────────────────
  const speak = useCallback(
    (text: string) => {
      setStatus("speaking");
      setLastResponse(text);
      speakText(text, isBn ? "bn" : "en");
      // Resume to idle after estimated speaking time
      const duration = Math.max(2000, text.length * 80);
      setTimeout(() => setStatus("idle"), duration);
    },
    [isBn]
  );

  // ── Command Definitions ───────────────────────────────
  const getCommands = useCallback((): VoiceCommand[] => [
    // ── Automated Crop Selection & Diagnosis ─────────
    {
      patterns: ["আলু", "potato", "আলুর রোগ", "আলুর পাতা", "আলু স্ক্যান"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("potato", "আলু (Potato)");
        router.push("/diagnosis");
        speak(isBn ? "আলু ফসল নির্বাচন করা হয়েছে। এবার আক্রান্ত পাতার ছবি তুলুন বা আপলোড করুন।" : "Potato selected. Please upload or take a leaf photo.");
      },
      responseBn: "আলু ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Potato crop selected.",
    },
    {
      patterns: ["টমেটো", "tomato", "টমেটোর রোগ", "টমেটো স্ক্যান"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("tomato", "টমেটো (Tomato)");
        router.push("/diagnosis");
        speak(isBn ? "টমেটো ফসল নির্বাচন করা হয়েছে। পাতার পরিষ্কার ছবি আপলোড করুন।" : "Tomato selected. Upload a clear leaf photo.");
      },
      responseBn: "টমেটো ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Tomato crop selected.",
    },
    {
      patterns: ["ধান", "rice", "ধানের রোগ", "ধান স্ক্যান", "প্যাডি"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("rice", "ধান (Rice)");
        router.push("/diagnosis");
        speak(isBn ? "ধান ফসল নির্বাচন করা হয়েছে। আক্রান্ত পাতার ছবি নির্বাচন করুন।" : "Rice selected. Please upload leaf photo.");
      },
      responseBn: "ধান ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Rice crop selected.",
    },
    {
      patterns: ["মরিচ", "chili", "মরিচের রোগ", "মরিচ স্ক্যান"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("chili", "মরিচ (Chili)");
        router.push("/diagnosis");
        speak(isBn ? "মরিচ ফসল নির্বাচন করা হয়েছে। আক্রান্ত পাতার ছবি দিন।" : "Chili selected. Please upload leaf photo.");
      },
      responseBn: "মরিচ ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Chili crop selected.",
    },
    {
      patterns: ["ভুট্টা", "corn", "ভুট্টার রোগ", "ভুট্টা স্ক্যান"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("corn", "ভুট্টা (Corn)");
        router.push("/diagnosis");
        speak(isBn ? "ভুট্টা ফসল নির্বাচন করা হয়েছে।" : "Corn selected.");
      },
      responseBn: "ভুট্টা ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Corn crop selected.",
    },
    {
      patterns: ["বেগুন", "eggplant", "brinjal", "বেগুনের রোগ"],
      handler: ({ router, store, speak }) => {
        store.setSelectedCrop("eggplant", "বেগুন (Brinjal)");
        router.push("/diagnosis");
        speak(isBn ? "বেগুন ফসল নির্বাচন করা হয়েছে।" : "Eggplant selected.");
      },
      responseBn: "বেগুন ফসল নির্বাচন করা হয়েছে।",
      responseEn: "Eggplant crop selected.",
    },

    // ── Automated Camera / Upload Action ─────────────
    {
      patterns: ["ছবি তোলো", "ক্যামেরা খোলো", "ক্যামেরা", "স্ক্যান করো", "ছবি আপলোড", "ক্যামেরা অন", "take photo", "camera", "upload photo"],
      handler: ({ router, speak }) => {
        router.push("/diagnosis");
        speak(isBn ? "ক্যামেরা ও ছবি আপলোড প্রস্তুত করা হচ্ছে। পাতার ছবি দিন।" : "Opening camera and file upload.");
        setTimeout(() => {
          if (typeof document !== "undefined") {
            const input = document.querySelector('input[type="file"]') as HTMLInputElement;
            if (input) input.click();
          }
        }, 800);
      },
      responseBn: "ক্যামেরা প্রস্তুত করা হচ্ছে।",
      responseEn: "Opening camera upload.",
    },

    // ── Automated Add Farmland Action ─────────────────
    {
      patterns: ["জমি যোগ", "নতুন জমি", "ফার্ম যোগ", "জমি যোগ করো", "add farm", "new farmland", "add plot"],
      handler: ({ router, speak }) => {
        router.push("/farms");
        speak(isBn ? "নতুন জমি যোগ করার ফর্ম খোলা হচ্ছে।" : "Opening add farmland form.");
        setTimeout(() => {
          if (typeof document !== "undefined") {
            const btns = Array.from(document.querySelectorAll("button"));
            const addBtn = btns.find((b) => b.textContent?.includes("জমি যোগ") || b.textContent?.includes("Add Plot"));
            if (addBtn) addBtn.click();
          }
        }, 800);
      },
      responseBn: "নতুন জমি যোগ করার ফর্ম খোলা হচ্ছে।",
      responseEn: "Opening add plot form.",
    },

    // ── Automated Hotline Call ────────────────────────
    {
      patterns: ["কল করো", "ফোন করো", "হেল্পলাইন", "হটলাইন", "১৬১২৩", "call helpline", "emergency call", "help line"],
      handler: ({ speak }) => {
        speak(isBn ? "কৃষি সম্প্রসারণ তথ্য সার্ভিসের ফ্রি হটলাইন ১৬১২৩ নম্বরে কল করা হচ্ছে।" : "Calling Agriculture Helpline 16123.");
        if (typeof window !== "undefined") {
          window.location.href = "tel:16123";
        }
      },
      responseBn: "১৬১২৩ হটলাইনে কল করা হচ্ছে।",
      responseEn: "Calling 16123 hotline.",
    },

    // ── Automated Login / Register Modals ─────────────
    {
      patterns: ["লগইন", "লগইন করো", "সাইন ইন", "login", "sign in"],
      handler: ({ store, speak }) => {
        store.openAuthModal("login");
        speak(isBn ? "লগইন উইন্ডো খোলা হয়েছে। মোবাইল নম্বর ও পাসওয়ার্ড দিন।" : "Opening login window.");
      },
      responseBn: "লগইন উইন্ডো খোলা হয়েছে।",
      responseEn: "Opening login modal.",
    },
    {
      patterns: ["নিবন্ধন", "রেজিস্ট্রেশন", "রেজিস্টার", "নতুন একাউন্ট", "register", "sign up"],
      handler: ({ store, speak }) => {
        store.openAuthModal("register");
        speak(isBn ? "নতুন কৃষক নিবন্ধন ফর্ম খোলা হয়েছে।" : "Opening registration window.");
      },
      responseBn: "রেজিস্ট্রেশন উইন্ডো খোলা হয়েছে।",
      responseEn: "Opening registration modal.",
    },

    // ── Agricultural Disease Advice & Doctor ─────────
    {
      patterns: ["নাবী ধসা", "লেট ব্লাইট", "late blight", "আলুর ধসা"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "আলুর নাবী ধসা বা লেট ব্লাইট রোগের জন্য ম্যানকোজেব অথবা রিডোমিল গোল্ড ২ গ্রাম প্রতি লিটার পানিতে মিশিয়ে শেষ বিকেলে ৭ দিন পর পর স্প্রে করুন। জমিতে পানি জমতে দেবেন না।"
            : "For Late Blight, spray Mancozeb or Ridomil Gold at 2g per liter of water every 7 days. Avoid waterlogging."
        );
      },
      responseBn: "নাবী ধসা রোগের পরামর্শ দেওয়া হলো।",
      responseEn: "Late blight advice issued.",
    },
    {
      patterns: ["আগাম ধসা", "আর্লি ব্লাইট", "early blight"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "আগাম ধসা রোগের জন্য রোভরাল বা স্কোর প্রতি লিটার পানিতে ২ গ্রাম হারে স্প্রে করুন এবং আক্রান্ত পাতা নষ্ট করে ফেলুন।"
            : "For Early Blight, spray Rovral or Score at 2g per liter of water."
        );
      },
      responseBn: "আগাম ধসা রোগের চিকিৎসা পরামর্শ।",
      responseEn: "Early blight advice issued.",
    },
    {
      patterns: ["ব্লাস্ট রোগ", "ধানের ব্লাস্ট", "blast disease", "ব্লাস্ট"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "ধানের ব্লাস্ট রোগের জন্য ট্রাইসাইক্লাজোল জাতীয় ছত্রাকনাশক যেমন ট্রুপার বা নেটিভো প্রতি লিটার পানিতে ১ গ্রাম হারে মিশিয়ে স্প্রে করুন।"
            : "For Paddy Blast disease, spray Tricyclazole fungicides like Trooper or Nativo at 1g/L."
        );
      },
      responseBn: "ধানের ব্লাস্ট রোগের পরামর্শ।",
      responseEn: "Rice blast remedy issued.",
    },
    {
      patterns: ["খোল পোড়া", "শীথ ব্লাইট", "sheath blight"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "ধানের খোল পোড়া রোগের জন্য ভ্যালিডামাইসিন বা ফলিকুর প্রতি লিটার পানিতে ১ মিলি হারে স্প্রে করুন। জমিতে অতিরিক্ত ইউরিয়া ব্যবহার করবেন না।"
            : "For Sheath Blight, spray Validamycin or Folicur at 1ml/L. Avoid excess urea."
        );
      },
      responseBn: "খোল পোড়া রোগের পরামর্শ।",
      responseEn: "Sheath blight remedy issued.",
    },
    {
      patterns: ["পাতা কুঁকড়ানো", "লিফ কার্ল", "leaf curl", "পাতা কুঁকড়ে"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "পাতা কুঁকড়ানো রোগ সাদা মাছি ও মাকড়ের আক্রমণের ফলে হয়। ইমিডাক্লোপ্রিড যেমন টিডো বা অ্যাডমায়ার প্রতি লিটার পানিতে ০.৫ মিলি হারে স্প্রে করুন।"
            : "Leaf curl is spread by whiteflies. Spray Imidacloprid at 0.5ml per liter of water."
        );
      },
      responseBn: "পাতা কুঁকড়ানো রোগের পরামর্শ।",
      responseEn: "Leaf curl advice issued.",
    },
    {
      patterns: ["ফল পচা", "অ্যানথ্রাকনোজ", "anthracnose", "মরিচ পচা"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "মরিচের ফল পচা বা অ্যানথ্রাকনোজের জন্য টিল্ট বা স্কোর প্রতি লিটার পানিতে ০.৫ মিলি স্প্রে করুন এবং আক্রান্ত ফল তুলে পুড়িয়ে ফেলুন।"
            : "For Anthracnose, spray Tilt or Score at 0.5ml/L and dispose of infected fruits."
        );
      },
      responseBn: "ফল পচা রোগের পরামর্শ।",
      responseEn: "Anthracnose advice issued.",
    },
    {
      patterns: ["পোকা", "কীটপতঙ্গ", "মাজরা", "লেদা পোকা", "pests", "insect"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "ক্ষতিকারক পোকা দমনে জমিতে সেক্স ফেরোমোন ফাঁদ ও আলোক ফাঁদ ব্যবহার করুন। বেশি আক্রমণ হলে অনুমোদিত বালাইনাশক ভিরতাকো ব্যবহার করুন।"
            : "Use sex pheromone and light traps for pest control. Apply certified bio-pesticides when needed."
        );
      },
      responseBn: "পোকা দমনের পরামর্শ।",
      responseEn: "Pest control advice issued.",
    },
    {
      patterns: ["সার", "ইউরিয়া", "fertilizer", "সার প্রয়োগ"],
      handler: ({ speak }) => {
        speak(
          isBn
            ? "মাটির উর্বরতা রক্ষা করতে ইউরিয়া, টিএসপি, পটাশ ও জিপসাম সার সঠিক মাত্রায় দুই থেকে তিন কিস্তিতে জমিতে প্রয়োগ করুন।"
            : "Apply balanced Nitrogen, Phosphorus, and Potassium fertilizers in 2-3 split doses."
        );
      },
      responseBn: "সার প্রয়োগের পরামর্শ।",
      responseEn: "Fertilizer advice issued.",
    },

    // ── Navigation ───────────────────────────────────
    {
      patterns: ["রোগ নির্ণয়", "diagnosis", "scan crop", "স্ক্যান", "ফসল স্ক্যান", "diagnose"],
      handler: ({ router, speak }) => {
        router.push("/diagnosis");
        speak(isBn ? "রোগ নির্ণয় পেজে যাচ্ছি।" : "Opening diagnosis page.");
      },
      responseBn: "রোগ নির্ণয় পেজে যাচ্ছি।",
      responseEn: "Opening diagnosis page.",
    },
    {
      patterns: ["আমার জমি", "farms", "my farms", "জমি", "ফার্ম", "farmland"],
      handler: ({ router, speak }) => {
        router.push("/farms");
        speak(isBn ? "আপনার জমির তালিকা খুলছি।" : "Opening your farmlands.");
      },
      responseBn: "আপনার জমির তালিকা খুলছি।",
      responseEn: "Opening your farmlands.",
    },
    {
      patterns: ["ইতিহাস", "history", "case history", "হিস্ট্রি", "পুরনো কেস", "past cases"],
      handler: ({ router, speak }) => {
        router.push("/history");
        speak(isBn ? "কেস হিস্ট্রি খুলছি।" : "Opening case history.");
      },
      responseBn: "কেস হিস্ট্রি খুলছি।",
      responseEn: "Opening case history.",
    },
    {
      patterns: ["হোম", "home", "dashboard", "ড্যাশবোর্ড", "মেইন পেজ", "go home"],
      handler: ({ router, speak }) => {
        router.push("/");
        speak(isBn ? "হোম পেজে যাচ্ছি।" : "Going to home.");
      },
      responseBn: "হোম পেজে যাচ্ছি।",
      responseEn: "Going to home.",
    },
    {
      patterns: ["বিশেষজ্ঞ", "expert", "expert queue", "কিউ", "review queue"],
      handler: ({ router, speak, store }) => {
        if (store.role === "expert" || store.role === "admin") {
          router.push("/expert");
          speak(isBn ? "বিশেষজ্ঞ কিউ খুলছি।" : "Opening expert review queue.");
        } else {
          speak(isBn ? "আপনি বিশেষজ্ঞ পোর্টালে প্রবেশ করতে পারবেন না।" : "Expert portal access denied.");
        }
      },
      responseBn: "বিশেষজ্ঞ কিউ খুলছি।",
      responseEn: "Opening expert review queue.",
    },
    {
      patterns: ["অ্যাডমিন", "admin", "admin panel", "সিস্টেম কন্ট্রোল"],
      handler: ({ router, speak, store }) => {
        if (store.role === "admin") {
          router.push("/admin");
          speak(isBn ? "অ্যাডমিন প্যানেল খুলছি।" : "Opening admin panel.");
        } else {
          speak(isBn ? "শুধুমাত্র অ্যাডমিন এই পেজে যেতে পারবেন।" : "Admin access only.");
        }
      },
      responseBn: "অ্যাডমিন প্যানেল খুলছি।",
      responseEn: "Opening admin panel.",
    },
    {
      patterns: ["প্রোফাইল", "profile", "my profile", "আমার প্রোফাইল"],
      handler: ({ router, speak }) => {
        router.push("/profile");
        speak(isBn ? "প্রোফাইল পেজ খুলছি।" : "Opening your profile.");
      },
      responseBn: "প্রোফাইল পেজ খুলছি।",
      responseEn: "Opening your profile.",
    },

    // ── App Controls ──────────────────────────────────
    {
      patterns: ["লগআউট", "logout", "sign out", "বের হও", "log out"],
      handler: ({ store, router, speak }) => {
        store.logout();
        if (typeof window !== "undefined") {
          localStorage.removeItem("kb_access_token");
          localStorage.removeItem("kb_refresh_token");
        }
        router.push("/login");
        speak(isBn ? "লগআউট হয়ে গেছেন।" : "You have been logged out.");
      },
      responseBn: "লগআউট হয়ে গেছেন।",
      responseEn: "You have been logged out.",
    },
    {
      patterns: ["বাংলা", "বাংলায় যাও", "switch to bengali", "bangla"],
      handler: ({ speak, setLanguage }) => {
        setLanguage("bn");
        speak("ভাষা বাংলায় পরিবর্তন হয়েছে।");
      },
      responseBn: "ভাষা বাংলায় পরিবর্তন হয়েছে।",
      responseEn: "Switched to Bangla.",
    },
    {
      patterns: ["english", "switch to english", "ইংরেজি", "ইংলিশ"],
      handler: ({ speak, setLanguage }) => {
        setLanguage("en");
        speak("Language switched to English.");
      },
      responseBn: "ভাষা ইংরেজিতে পরিবর্তন হয়েছে।",
      responseEn: "Language switched to English.",
    },
    {
      patterns: ["ডার্ক মোড", "dark mode", "dark", "রাতের মোড"],
      handler: ({ store, speak }) => {
        if (!store.isDark) store.toggleTheme();
        speak(isBn ? "ডার্ক মোড চালু করা হয়েছে।" : "Dark mode enabled.");
      },
      responseBn: "ডার্ক মোড চালু।",
      responseEn: "Dark mode enabled.",
    },
    {
      patterns: ["লাইট মোড", "light mode", "light", "দিনের মোড"],
      handler: ({ store, speak }) => {
        if (store.isDark) store.toggleTheme();
        speak(isBn ? "লাইট মোড চালু করা হয়েছে।" : "Light mode enabled.");
      },
      responseBn: "লাইট মোড চালু।",
      responseEn: "Light mode enabled.",
    },

    // ── Help ──────────────────────────────────────────
    {
      patterns: ["সাহায্য", "help", "কী কমান্ড", "কী বলবো", "commands", "what can you do"],
      handler: ({ speak }) => {
        const helpText = isBn
          ? "আপনি বলতে পারেন: আলু বা ধান রোগ নির্ণয়, ছবি তোলো, জমি যোগ করো, আমার জমি, ইতিহাস, প্রোফাইল, ১৬১২৩ কল করো, লেট ব্লাইট প্রতিকার, ডার্ক মোড অথবা লগআউট।"
          : "You can say: diagnosis, upload photo, add farm, call 16123, late blight treatment, dark mode, or logout.";
        speak(helpText);
      },
      responseBn: "সাহায্য তালিকা পড়া হচ্ছে।",
      responseEn: "Reading help list.",
    },

    // ── Status ────────────────────────────────────────
    {
      patterns: ["কী চলছে", "কেমন আছো", "status", "আমার রোল", "আমি কে", "who am i"],
      handler: ({ speak, store }) => {
        const user = store.currentUser;
        if (user) {
          speak(
            isBn
              ? `আপনি ${user.fullName}, রোল: ${store.role}। আপনি লগইন আছেন।`
              : `You are ${user.fullName}, role: ${store.role}. You are logged in.`
          );
        } else {
          speak(isBn ? "আপনি এখনো লগইন করেননি। 'লগইন' বলে লগইন করতে পারেন।" : "You are not logged in. Say 'login' to sign in.");
        }
      },
      responseBn: "স্ট্যাটাস পড়া হচ্ছে।",
      responseEn: "Reading status.",
    },
  ], [isBn]);

  // ── Process Transcript ────────────────────────────
  const processTranscript = useCallback(
    (text: string) => {
      setStatus("processing");
      const commands = getCommands();
      const store = useAppStore.getState();

      const matched = commands.find((cmd) =>
        matchesCommand(text, cmd.patterns)
      );

      if (matched) {
        matched.handler({
          router,
          store,
          speak,
          setLanguage,
          transcript: text,
        });
      } else {
        const fallback = isBn
          ? `"${text}" বুঝতে পারিনি। "সাহায্য" বললে কমান্ড তালিকা শুনতে পাবেন।`
          : `I didn't understand "${text}". Say "help" for a command list.`;
        speak(fallback);
      }
    },
    [getCommands, router, speak, setLanguage, isBn]
  );

  // ── Init Recognition ──────────────────────────────
  const initRecognition = useCallback(() => {
    if (typeof window === "undefined") return null;
    const SR =
      (window.SpeechRecognition || window.webkitSpeechRecognition) as typeof SpeechRecognition | undefined;
    if (!SR) return null;

    const recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 3;
    // Support both Bangla and English
    recognition.lang = language === "bn" ? "bn-BD" : "en-US";

    recognition.onstart = () => {
      setStatus("listening");
      setTranscript("");
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }
      setTranscript(final || interim);
      if (final) {
        processTranscript(final.trim());
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.warn("Voice recognition error:", event.error);
      if (event.error === "no-speech") {
        setStatus("idle");
      } else if (event.error === "not-allowed") {
        setStatus("error");
        speak(
          isBn
            ? "মাইক্রোফোন অ্যাক্সেস দেওয়া হয়নি। ব্রাউজার সেটিংস থেকে মাইক্রোফোন অনুমতি দিন।"
            : "Microphone access denied. Please allow mic in browser settings."
        );
      } else {
        setStatus("idle");
      }
      isListeningRef.current = false;
    };

    recognition.onend = () => {
      isListeningRef.current = false;
      if (status === "listening") setStatus("idle");
    };

    return recognition;
  }, [language, processTranscript, speak, isBn, status]);

  // ── Start Listening ───────────────────────────────
  const startListening = useCallback(() => {
    if (isListeningRef.current || status === "listening") return;
    window.speechSynthesis?.cancel();

    const recognition = initRecognition();
    if (!recognition) {
      setStatus("error");
      return;
    }

    recognitionRef.current = recognition;
    isListeningRef.current = true;

    try {
      recognition.start();
    } catch (err) {
      console.error("Failed to start recognition:", err);
      isListeningRef.current = false;
      setStatus("error");
    }
  }, [status, initRecognition]);

  // ── Stop Listening ────────────────────────────────
  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current?.abort();
    isListeningRef.current = false;
    setStatus("idle");
  }, []);

  // ── Cleanup ───────────────────────────────────────
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
  }, []);

  const executeCommand = useCallback(
    (text: string) => {
      setTranscript(text);
      processTranscript(text);
    },
    [processTranscript]
  );

  return {
    status,
    transcript,
    lastResponse,
    isSupported,
    startListening,
    stopListening,
    speak,
    executeCommand,
  };
}
