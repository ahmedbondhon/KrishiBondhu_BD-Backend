"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Eye, EyeOff, Shield, Sprout, Stethoscope } from "lucide-react";
import { AuthFrame, ResendButton, useCountdown } from "@/components/auth";
import { Button } from "@/components/ui";
import { ApiError, login, loginWithOtp, requestOtp } from "@/lib/api";
import { PHONE_RE, homeFor, normalizePhone } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import { cn } from "@/lib/utils";

type Mode = "password" | "otp";

export default function LoginPage() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const setUser = useApp((s) => s.setUser);
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("password");
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [remember, setRemember] = useState(false);
  const [show, setShow] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const cd = useCountdown();

  const fail = (e: unknown) => {
    const ae = e as ApiError;
    setErr(lang === "bn" ? ae.message_bn ?? "লগইন করা যায়নি। আবার চেষ্টা করুন।" : ae.message);
    setBusy(null);
  };
  const phoneInvalid = !id.includes("@") && !PHONE_RE.test(id.replace(/[\s-]/g, ""));
  const idValue = id.includes("@") ? id.trim() : normalizePhone(id);

  async function go(identifier: string, pw: string, role?: string) {
    setErr(""); setBusy(role ?? "form");
    try {
      const u = await login(identifier, pw, role, remember);
      setUser(u);
      router.push(homeFor(u));
    } catch (e) { fail(e); }
  }
  const submitPw = (e: FormEvent) => {
    e.preventDefault();
    if (phoneInvalid) return setErr(L("সঠিক মোবাইল নম্বর বা ইমেইল দিন, যেমন 01712345678।", "Enter a valid mobile number or email, like 01712345678."));
    go(idValue, password);
  };
  async function sendOtp() {
    if (!PHONE_RE.test(id.replace(/[\s-]/g, ""))) return setErr(L("সঠিক মোবাইল নম্বর দিন, যেমন 01712345678।", "Enter a valid mobile number, like 01712345678."));
    setErr(""); setBusy("send");
    try { const r = await requestOtp(normalizePhone(id), "login"); cd.reset(r.resend_after); setOtpSent(true); setBusy(null); } catch (e) { fail(e); }
  }
  async function verifyOtp(e: FormEvent) {
    e.preventDefault(); setErr(""); setBusy("otp");
    try {
      const u = await loginWithOtp(normalizePhone(id), otp, remember);
      setUser(u);
      router.push(homeFor(u));
    } catch (e2) { fail(e2); }
  }

  const demos = [
    { role: "farmer", I: Sprout, bn: "কৃষক", en: "Farmer", dbn: "ছবি তুলে পরীক্ষা", den: "Check crops by photo" },
    { role: "expert", I: Stethoscope, bn: "বিশেষজ্ঞ", en: "Expert", dbn: "কেস দেখে উত্তর", den: "Review cases and reply" },
    { role: "admin", I: Shield, bn: "অ্যাডমিন", en: "Admin", dbn: "কনটেন্ট ও ব্যবহারকারী", den: "Content and users" },
  ];
  const mock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
  const alertBox = err && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 ring-1 ring-inset ring-clay-100">{err}</p>;
  const rememberBox = (
    <label className="flex cursor-pointer items-center gap-2.5 text-ink-soft">
      <input type="checkbox" className="h-5 w-5 accent-[#178049]" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
      {L("আমাকে মনে রাখুন (৩০ দিন)", "Remember me (30 days)")}
    </label>
  );

  return (
    <AuthFrame title={L("আবার স্বাগতম", "Welcome back")} sub={L("মোবাইল নম্বর বা ইমেইল দিয়ে লগইন করুন।", "Log in with your mobile number or email.")}>
      <div className="mb-5 grid grid-cols-2 gap-1 rounded-ctl bg-brand-50 p-1" role="tablist">
        {([["password", "পাসওয়ার্ড / পিন", "Password / PIN"], ["otp", "ওটিপি কোড", "OTP code"]] as const).map(([m, b, e]) => (
          <button key={m} role="tab" aria-selected={mode === m} type="button" onClick={() => { setMode(m); setErr(""); }} className={cn("min-h-[44px] rounded-lg font-semibold", mode === m ? "bg-white text-brand-700 shadow-sm" : "text-ink-soft")}>{L(b, e)}</button>
        ))}
      </div>

      {mode === "password" ? (
        <form onSubmit={submitPw} className="space-y-4">
          <div><label className="label" htmlFor="phone">{L("মোবাইল নম্বর বা ইমেইল", "Mobile number or email")}</label><input id="phone" className="field" autoComplete="username" placeholder="01XXXXXXXXX" value={id} onChange={(e) => setId(e.target.value)} required /></div>
          <div>
            <label className="label" htmlFor="pw">{L("পাসওয়ার্ড / পিন", "Password / PIN")}</label>
            <div className="relative">
              <input id="pw" className="field pr-12" type={show ? "text" : "password"} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              <button type="button" onClick={() => setShow(!show)} className="absolute right-1.5 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-lg text-ink-mute hover:bg-brand-50" aria-label={show ? L("পাসওয়ার্ড লুকান", "Hide password") : L("পাসওয়ার্ড দেখুন", "Show password")}>{show ? <EyeOff size={19} /> : <Eye size={19} />}</button>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2">{rememberBox}<Link href="/forgot-password" className="font-semibold text-brand-700 hover:underline">{L("পাসওয়ার্ড ভুলে গেছেন?", "Forgot password?")}</Link></div>
          {alertBox}
          <Button type="submit" loading={busy === "form"} size="lg" className="w-full">{L("লগইন করুন", "Log in")}</Button>
        </form>
      ) : (
        <form onSubmit={verifyOtp} className="space-y-4">
          <div><label className="label" htmlFor="ophone">{L("মোবাইল নম্বর", "Mobile number")}</label><input id="ophone" className="field" inputMode="tel" autoComplete="tel" placeholder="01XXXXXXXXX" value={id} onChange={(e) => setId(e.target.value)} disabled={otpSent} required /></div>
          {!otpSent ? (
            <>{alertBox}<Button type="button" onClick={sendOtp} loading={busy === "send"} size="lg" className="w-full">{L("কোড পাঠান", "Send code")}</Button></>
          ) : (
            <>
              <p className="rounded-ctl bg-sky-50 px-4 py-3 text-sky-700">{L("৬ ডিজিটের কোড পাঠানো হয়েছে।", "We sent a 6-digit code.")}</p>
              <input aria-label="OTP" className="field text-center font-display text-3xl tracking-[0.5em] !min-h-[60px]" inputMode="numeric" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} autoFocus />
              {rememberBox}{alertBox}
              <Button type="submit" loading={busy === "otp"} disabled={otp.length !== 6} size="lg" className="w-full">{L("লগইন করুন", "Log in")}</Button>
              <ResendButton left={cd.left} onClick={sendOtp} busy={busy === "send"} />
              <button type="button" onClick={() => { setOtpSent(false); setOtp(""); }} className="block w-full text-center text-ink-soft hover:underline">{L("নম্বর বদলান", "Change number")}</button>
            </>
          )}
        </form>
      )}
      <p className="mt-4 text-center text-ink-soft">{L("নতুন?", "New here?")} <Link href="/register" className="font-semibold text-brand-700 hover:underline">{L("একাউন্ট খুলুন", "Create an account")}</Link></p>

      {mock && (
        <div className="mt-9">
          <div className="mb-3 flex items-center gap-3 text-[14px] font-semibold text-ink-mute"><span className="h-px flex-1 bg-line-strong" />{L("অথবা ডেমো দিয়ে দেখুন", "Or explore the demo")}<span className="h-px flex-1 bg-line-strong" /></div>
          <div className="grid gap-2.5">
            {demos.map(({ role, I, bn, en, dbn, den }) => (
              <button key={role} onClick={() => go("", "demo1234", role)} disabled={!!busy} className="card flex items-center gap-3.5 p-3.5 text-left transition hover:shadow-pop disabled:opacity-60">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-700"><I size={22} /></span>
                <span className="flex-1 leading-tight"><span className="block font-display text-lg font-bold">{L(bn, en)}</span><span className="text-[14px] text-ink-mute">{L(dbn, den)}</span></span>
                <span className="text-[14px] font-semibold text-brand-700">{busy === role ? "…" : L("ঢুকুন", "Enter")}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </AuthFrame>
  );
}
