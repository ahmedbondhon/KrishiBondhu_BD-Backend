import { create } from "zustand";
import { persist } from "zustand/middleware";

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
  setCases: (cases: DiagnosisCase[]) => void;
  addCase: (c: DiagnosisCase) => void;
  updateCaseStatus: (id: string, status: DiagnosisCase["status"], expertNotes?: string) => void;

  // Farm Plots (Farmer feature)
  plots: FarmPlot[];
  setPlots: (plots: FarmPlot[]) => void;
  addPlot: (plot: FarmPlot) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Default: Not logged in (strict real authentication flow)
      isAuthenticated: false,
      currentUser: null,
      authModalOpen: false,
      authModalMode: "login",
      openAuthModal: (mode) => set({ authModalOpen: true, authModalMode: mode }),
      closeAuthModal: () => set({ authModalOpen: false }),
      login: (user) => {
        if (typeof window !== "undefined") {
          try {
            localStorage.setItem("kb_user_profile", JSON.stringify(user));
            localStorage.setItem("kb_user_role", user.role);
          } catch {}
        }
        set({ isAuthenticated: true, currentUser: user, role: user.role });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          try {
            localStorage.removeItem("kb_user_profile");
            localStorage.removeItem("kb_user_role");
            localStorage.removeItem("kb_access_token");
            localStorage.removeItem("kb_refresh_token");
          } catch {}
        }
        set({ isAuthenticated: false, currentUser: null, role: "farmer" });
      },

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

  cases: [],
  setCases: (cases) => set({ cases }),
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
  plots: [],
  setPlots: (plots) => set({ plots }),
  addPlot: (plot) => set((state) => ({ plots: [plot, ...state.plots] })),
    }),
    {
      name: "krishibondhu_app_storage",
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        currentUser: state.currentUser,
        role: state.role,
        language: state.language,
        isDark: state.isDark,
        cases: state.cases,
        plots: state.plots,
      }),
    }
  )
);
