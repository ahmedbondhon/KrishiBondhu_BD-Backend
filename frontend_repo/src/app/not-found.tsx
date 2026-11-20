"use client";
import { Compass } from "lucide-react";
import { LinkButton, Logo } from "@/components/ui";
import { useL } from "@/store/app";

export default function NotFound() {
  const L = useL();
  return (
    <main id="main" className="grid min-h-screen place-items-center px-6">
      <div className="max-w-md text-center">
        <Logo className="mx-auto mb-8 justify-center" />
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-brand-600"><Compass size={30} /></span>
        <h1 className="mt-5 text-3xl">{L("এই পাতাটি পাওয়া যায়নি", "We could not find that page")}</h1>
        <p className="mt-2 text-ink-soft">{L("লিংকটি ভুল হতে পারে বা পাতাটি সরানো হয়েছে।", "The link may be wrong or the page was moved.")}</p>
        <LinkButton href="/" className="mt-6">{L("প্রথম পাতায় ফিরুন", "Back to home")}</LinkButton>
      </div>
    </main>
  );
}
