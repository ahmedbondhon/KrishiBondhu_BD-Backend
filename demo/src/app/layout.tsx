import type { Metadata } from "next";
import QueryProvider from "@/providers/QueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "কৃষিবন্ধু বাংলাদেশ — ChashiGuard AI ফসল রোগ নির্ণয়",
  description:
    "Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query এবং Zustand চালিত স্মার্ট কৃষি সেবা প্ল্যাটফর্ম।",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="bn">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-emerald-500 selection:text-white font-sans">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
