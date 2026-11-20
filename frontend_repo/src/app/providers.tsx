"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useState } from "react";
import { useApp } from "@/store/app";

export default function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 2, staleTime: 15_000, refetchOnWindowFocus: false } } }));
  const lang = useApp((s) => s.lang);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
