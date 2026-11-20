"use client";
import { TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui";
import { useL } from "@/store/app";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  const L = useL();
  return (
    <main id="main" className="grid min-h-screen place-items-center px-6">
      <div className="max-w-md text-center">
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-clay-50 text-clay-600"><TriangleAlert size={30} /></span>
        <h1 className="mt-5 text-3xl">{L("কিছু একটা ঠিক হয়নি", "Something went wrong")}</h1>
        <p className="mt-2 text-ink-soft">{L("আপনার তথ্য হারায়নি। আবার চেষ্টা করুন।", "Your data is safe. Please try again.")}</p>
        <Button onClick={reset} className="mt-6">{L("আবার চেষ্টা করুন", "Try again")}</Button>
      </div>
    </main>
  );
}
