import { create } from "zustand";

export type UserRole = "farmer" | "expert" | "admin";
export type Language = "bn" | "en";
export type ActiveTab =
  | "diagnosis"
  | "farms"
  | "history"
  | "expert_queue"
  | "admin_overview"
  | "admin_users";

export interface UserProfile {
  id: string;
  fullName: string;
  phoneNumber: string;
  role: UserRole;
  division?: string;
  district?: string;
  upazila?: string;
  avatarUrl?: string;
}

export interface FarmPlot {
  id: string;
  name: string;
  cropNameBn: string;
  areaDecimal: number;
  location: string;
  healthStatus: "good" | "warning" | "critical";
  lastDiagnosisDate: string;
}

export interface DiagnosisCase {
  id: string;
  caseNumber: string;
  cropName: string;
  cropNameBn: string;
  diseaseName: string;
  diseaseNameBn: string;
  confidence: number;
  status: "analyzed" | "pending_expert" | "reviewed" | "draft";
  imageUrl: string;
  rawImage?: string;
  createdAt: string;
  treatmentBn: string;
  preventionBn: string;
  expertNotesBn?: string;
  autoSelected?: boolean;
  autoSelectMessageBn?: string;
}

interface AppState {
  // Auth state
  isAuthenticated: boolean;
  currentUser: UserProfile | null;
  authModalOpen: boolean;
  authModalMode: "login" | "register";
  openAuthModal: (mode: "login" | "register") => void;
  closeAuthModal: () => void;
  login: (user: UserProfile) => void;
  logout: () => void;

  // Settings & Navigation
  role: UserRole;
  activeTab: ActiveTab;
  language: Language;
  isDark: boolean;
  setRole: (role: UserRole) => void;
  setActiveTab: (tab: ActiveTab) => void;
  setLanguage: (lang: Language) => void;
  toggleTheme: () => void;

  // Active Diagnosis Workflow
  selectedCrop: string;
  selectedCropBn: string;
  setSelectedCrop: (crop: string, cropBn: string) => void;

  selectedSymptoms: string[];
  toggleSymptom: (symptom: string) => void;
  clearSymptoms: () => void;

  activeImage: string | null;
  setActiveImage: (url: string | null) => void;

  activeCase: DiagnosisCase | null;
  setActiveCase: (c: DiagnosisCase | null) => void;

  // History & Cases
  cases: DiagnosisCase[];
  addCase: (c: DiagnosisCase) => void;
  updateCaseStatus: (id: string, status: DiagnosisCase["status"], expertNotes?: string) => void;

  // Farm Plots (Farmer feature)
  plots: FarmPlot[];
  addPlot: (plot: FarmPlot) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Default logged in demo user (Farmer)
  isAuthenticated: true,
  currentUser: {
    id: "11000000-0000-0000-0000-000000000001",
    fullName: "মো: আব্দুল্লাহ",
    phoneNumber: "01754890387",
    role: "farmer",
    division: "রাজশাহী",
    district: "বগুড়া",
    upazila: "শিবগঞ্জ",
  },
  authModalOpen: false,
  authModalMode: "login",
  openAuthModal: (mode) => set({ authModalOpen: true, authModalMode: mode }),
  closeAuthModal: () => set({ authModalOpen: false }),
  login: (user) => set({ isAuthenticated: true, currentUser: user, role: user.role }),
  logout: () => set({ isAuthenticated: false, currentUser: null }),

  role: "farmer",
  activeTab: "diagnosis",
  language: "bn",
  isDark: false,
  setRole: (role) => set({ role }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setLanguage: (language) => set({ language }),
  toggleTheme: () =>
    set((state) => {
      const next = !state.isDark;
      if (typeof document !== "undefined") {
        if (next) {
          document.documentElement.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
        }
      }
      return { isDark: next };
    }),

  selectedCrop: "potato",
  selectedCropBn: "আলু (Potato)",
  setSelectedCrop: (selectedCrop, selectedCropBn) =>
    set({ selectedCrop, selectedCropBn }),

  selectedSymptoms: [],
  toggleSymptom: (symptom) =>
    set((state) => ({
      selectedSymptoms: state.selectedSymptoms.includes(symptom)
        ? state.selectedSymptoms.filter((s) => s !== symptom)
        : [...state.selectedSymptoms, symptom],
    })),
  clearSymptoms: () => set({ selectedSymptoms: [] }),

  activeImage: null,
  setActiveImage: (activeImage) => set({ activeImage }),

  activeCase: null,
  setActiveCase: (activeCase) => set({ activeCase }),

  cases: [
    {
      id: "22000000-0000-0000-0000-000000000001",
      caseNumber: "KB-2026-000412",
      cropName: "potato",
      cropNameBn: "আলু",
      diseaseName: "Late Blight",
      diseaseNameBn: "আলুর নাবী ধসা (লেট ব্লাইট)",
      confidence: 0.94,
      status: "analyzed",
      imageUrl: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80",
      createdAt: "২০২৬-১০-২২ ১২:৩০",
      treatmentBn: "ম্যানকোজেব (Mancozeb) জাতীয় ছত্রাকনাশক প্রতি লিটার পানিতে ২ গ্রাম হারে মিশিয়ে ৭-১০ দিন পর পর স্প্রে করুন।",
      preventionBn: "জমি সবসময় পরিষ্কার ও আগাছামুক্ত রাখুন। আক্রান্ত পাতা তুলে নষ্ট করে ফেলুন। অতিরিক্ত সেচ পরিহার করুন।",
    },
    {
      id: "22000000-0000-0000-0000-000000000002",
      caseNumber: "KB-2026-000411",
      cropName: "chili",
      cropNameBn: "মরিচ",
      diseaseName: "Chili Anthracnose",
      diseaseNameBn: "মরিচের ফল পচা / অ্যানথ্রাকনোজ ও লিফ কার্ল",
      confidence: 0.68,
      status: "pending_expert",
      imageUrl: "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=600&q=80",
      createdAt: "২০২৬-১০-২১ ০৯:১৫",
      treatmentBn: "বিশেষজ্ঞ পর্যালোচনার অপেক্ষায় রয়েছে। আক্রান্ত ফল সংগ্রহ করে ধ্বংস করুন এবং ছত্রাকনাশক স্প্রে করুন।",
      preventionBn: "সুস্থ প্রত্যয়িত চারা ব্যবহার করুন এবং অতিরিক্ত আর্দ্রতা পরিহার করুন।",
    },
  ],
  addCase: (c) =>
    set((state) => {
      const existingIdx = state.cases.findIndex(
        (item) =>
          item.id === c.id ||
          (c.rawImage && item.rawImage && item.rawImage === c.rawImage) ||
          (c.imageUrl && item.imageUrl && item.imageUrl === c.imageUrl)
      );

      if (existingIdx !== -1) {
        const updatedCases = [...state.cases];
        const prev = updatedCases[existingIdx];
        const updatedItem: DiagnosisCase = {
          ...prev,
          ...c,
          id: prev.id,
          caseNumber: prev.caseNumber,
          createdAt: prev.createdAt,
        };
        updatedCases[existingIdx] = updatedItem;
        return {
          cases: updatedCases,
          activeCase: updatedItem,
        };
      }

      return {
        cases: [c, ...state.cases],
        activeCase: c,
      };
    }),
  updateCaseStatus: (id, status, expertNotes) =>
    set((state) => ({
      cases: state.cases.map((item) =>
        item.id === id
          ? {
              ...item,
              status,
              expertNotesBn: expertNotes || item.expertNotesBn,
            }
          : item
      ),
      activeCase:
        state.activeCase?.id === id
          ? {
              ...state.activeCase,
              status,
              expertNotesBn: expertNotes || state.activeCase.expertNotesBn,
            }
          : state.activeCase,
    })),

  // Plots
  plots: [
    {
      id: "33000000-0000-0000-0000-000000000001",
      name: "গোকুল মাঠের আলুর জমি",
      cropNameBn: "আলু (গ্রানোলা)",
      areaDecimal: 35,
      location: "শিবগঞ্জ, বগুড়া",
      healthStatus: "warning",
      lastDiagnosisDate: "২০২৬-১০-২২",
    },
    {
      id: "33000000-0000-0000-0000-000000000002",
      name: "মোকামতলা মরিচ বাগান",
      cropNameBn: "মরিচ (বারি ঝালকা)",
      areaDecimal: 40,
      location: "শিবগঞ্জ, বগুড়া",
      healthStatus: "good",
      lastDiagnosisDate: "২০২৬-১০-১৯",
    },
    {
      id: "33000000-0000-0000-0000-000000000003",
      name: "সাতক্ষীরা টমেটো প্লট",
      cropNameBn: "টমেটো (বারি টমেটো ১৪)",
      areaDecimal: 25,
      location: "সাতক্ষীরা সদর",
      healthStatus: "good",
      lastDiagnosisDate: "২০২৬-১০-১৫",
    },
  ],
  addPlot: (plot) => set((state) => ({ plots: [plot, ...state.plots] })),
}));
