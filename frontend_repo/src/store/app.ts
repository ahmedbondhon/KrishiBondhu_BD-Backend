"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AppState {
  lang: "bn" | "en";
  user: User | null;
  setLang: (l: "bn" | "en") => void;
  setUser: (u: User | null) => void;
}

export const useApp = create<AppState>()(
  persist(
    (set) => ({
      lang: "bn",
      user: null,
      setLang: (lang) => set({ lang }),
      setUser: (user) => set({ user }),
    }),
    { name: "kb-app" }
  )
);

/** Bangla-first inline translation: L("বাংলা", "English") */
export function useL() {
  const lang = useApp((s) => s.lang);
  return (bn: string, en: string) => (lang === "bn" ? bn : en);
}
