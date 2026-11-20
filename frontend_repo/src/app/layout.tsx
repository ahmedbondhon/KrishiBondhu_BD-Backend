import type { Metadata, Viewport } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: { default: "কৃষিবন্ধু বাংলাদেশ — ছবি তুলে ফসলের রোগ চিনুন", template: "%s · কৃষিবন্ধু" },
  description: "ফসলের ছবি তুলুন, বাংলায় সহজ পরামর্শ পান, প্রয়োজনে কৃষি বিশেষজ্ঞের সাহায্য নিন।",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg" },
};
export const viewport: Viewport = { themeColor: "#0C3324", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn">
      <body>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[100] focus:rounded-ctl focus:bg-white focus:px-4 focus:py-2 focus:shadow-pop">
          মূল অংশে যান / Skip to content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
