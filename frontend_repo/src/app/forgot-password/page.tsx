"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthFrame, ResendButton, useCountdown } from "@/components/auth";
import { Button } from "@/components/ui";
import { ApiError, forgotPassword, resetPassword } from "@/lib/api";
import { PHONE_RE, normalizePhone } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

export default function ForgotPassword() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const router = useRouter();
  const [step, setStep] = useState<"phone" | "reset" | "done">("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const cd = useCountdown();
  const p = normalizePhone(phone);
  const fail = (e: unknown) => { const ae = e as ApiError; setErr(lang === "bn" ? ae.message_bn ?? "কিছু একটা ভুল হয়েছে।" : ae.message); };

  async function send(e?: FormEvent) {
    e?.preventDefault(); setErr("");
    if (!PHONE_RE.test(phone.replace(/[\s-]/g, ""))) return setErr(L("সঠিক মোবাইল নম্বর দিন, যেমন 01712345678।", "Enter a valid mobile number, like 01712345678."));
    setBusy(true);
    try { const r = await forgotPassword(p); cd.reset(r.resend_after); setStep("reset"); } catch (e2) { fail(e2); }
    setBusy(false);
  }
  async function reset(e: FormEvent) {
    e.preventDefault(); setErr("");
    // Farmers use a numeric PIN, other roles a strong password; the backend decides by role and returns a 422 if invalid.
    if (pw.length < 6) return setErr(L("কমপক্ষে ৬ ডিজিটের পিন (কৃষক) বা ৮ অক্ষরের পাসওয়ার্ড দিন।", "Enter a PIN of 6+ digits (farmers) or a password of 8+ characters."));
    setBusy(true);
    try { await resetPassword(p, otp, pw); setStep("done"); setTimeout(() => router.push("/login"), 2500); } catch (e2) { fail(e2); }
    setBusy(false);
  }
  const alertBox = err && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 ring-1 ring-inset ring-clay-100">{err}</p>;

  return (
    <AuthFrame title={L("পাসওয়ার্ড রিসেট", "Reset password")} sub={L("মোবাইলে পাঠানো কোড দিয়ে নতুন পাসওয়ার্ড দিন।", "Use the code sent to your phone to set a new password.")}>
      {step === "phone" && (
        <form onSubmit={send} className="space-y-4">
          <div><label className="label" htmlFor="fp">{L("মোবাইল নম্বর", "Mobile number")}</label><input id="fp" className="field" inputMode="tel" placeholder="01XXXXXXXXX" value={phone} onChange={(e) => setPhone(e.target.value)} required /></div>
          {alertBox}
          <Button type="submit" loading={busy} size="lg" className="w-full">{L("কোড পাঠান", "Send code")}</Button>
        </form>
      )}
      {step === "reset" && (
        <form onSubmit={reset} className="space-y-4">
          <p className="rounded-ctl bg-sky-50 px-4 py-3 text-sky-700">{L(`${p} নম্বরে কোড পাঠানো হয়েছে।`, `We sent a code to ${p}.`)}</p>
          <input aria-label="OTP" className="field text-center font-display text-3xl tracking-[0.5em] !min-h-[60px]" inputMode="numeric" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} autoFocus />
          <div><label className="label" htmlFor="np">{L("নতুন পাসওয়ার্ড / পিন", "New password / PIN")}</label><input id="np" type="password" autoComplete="new-password" className="field" value={pw} onChange={(e) => setPw(e.target.value)} required /></div>
          {alertBox}
          <Button type="submit" loading={busy} disabled={otp.length !== 6} size="lg" className="w-full">{L("পাসওয়ার্ড পরিবর্তন করুন", "Change password")}</Button>
          <ResendButton left={cd.left} onClick={() => send()} busy={busy} />
        </form>
      )}
      {step === "done" && <p role="status" className="rounded-ctl bg-brand-50 px-4 py-4 text-brand-800">{L("পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে। নতুন পাসওয়ার্ড দিয়ে লগইন করুন।", "Password changed. Log in with your new password.")}</p>}
      <p className="mt-6 text-center"><Link href="/login" className="font-bold text-brand-700 hover:underline">{L("লগইনে ফিরে যান", "Back to log in")}</Link></p>
    </AuthFrame>
  );
}
