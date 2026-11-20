"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { CheckCircle2, Clock, Stethoscope, Sprout, Users } from "lucide-react";
import { AuthFrame, EMPTY_GEO, GeoCascade, GeoValue, ResendButton, useCountdown } from "@/components/auth";
import { Button } from "@/components/ui";
import { ApiError, register, requestOtp, verifyOtp } from "@/lib/api";
import { PHONE_RE, cn, homeFor, normalizePhone, passwordOk } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

type Step = "details" | "otp" | "consent" | "pending";
type Role = "farmer" | "agent" | "expert";
const COMM = [["sms", "এসএমএস", "SMS"], ["call", "ফোন কল", "Phone call"], ["in_app", "অ্যাপে", "In-app"]] as const;

export default function RegisterPage() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const router = useRouter();
  const setUser = useApp((s) => s.setUser);
  const [step, setStep] = useState<Step>("details");
  const [role, setRole] = useState<Role>("farmer");
  const [f, setF] = useState({ name: "", phone: "", email: "", password: "", village: "", specialization: "", credentials: "", communication: "sms" as "sms" | "call" | "in_app" });
  const [geo, setGeo] = useState<GeoValue>(EMPTY_GEO);
  const [otp, setOtp] = useState("");
  const [vtoken, setVtoken] = useState("");
  const [consent, setConsent] = useState({ terms: false, privacy: false, location: false, ai: false });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingMsg, setPendingMsg] = useState("");
  const cd = useCountdown();

  const phone = normalizePhone(f.phone);
  const fail = (e: unknown) => { const ae = e as ApiError; setErr(lang === "bn" ? ae.message_bn ?? "কিছু একটা ভুল হয়েছে।" : ae.message); };
  const pwHint = role === "farmer"
    ? L("পিন (শুধু সংখ্যা, কমপক্ষে ৬ ডিজিট)", "PIN (digits only, at least 6)")
    : L("পাসওয়ার্ড (৮+ অক্ষর, বড় ও ছোট হাতের অক্ষর এবং সংখ্যা)", "Password (8+ chars with upper, lower case and a number)");

  async function sendCode() {
    const r = await requestOtp(phone, "registration");
    cd.reset(r.resend_after);
  }
  async function details(e: FormEvent) {
    e.preventDefault();
    setErr("");
    if (!PHONE_RE.test(f.phone.replace(/[\s-]/g, ""))) return setErr(L("মোবাইল নম্বর ১১ ডিজিটের হতে হবে, যেমন 01712345678।", "Enter an 11-digit mobile number, like 01712345678."));
    if (!passwordOk(role, f.password)) return setErr(role === "farmer" ? L("পিন শুধু সংখ্যার হতে হবে এবং কমপক্ষে ৬ ডিজিট।", "PIN must be digits only, at least 6 long.") : L("পাসওয়ার্ডে কমপক্ষে ৮ অক্ষর, একটি বড় হাতের অক্ষর, একটি ছোট হাতের অক্ষর ও একটি সংখ্যা থাকতে হবে।", "Password needs 8+ characters, an uppercase and lowercase letter, and a number."));
    setBusy(true);
    try { await sendCode(); setStep("otp"); } catch (e2) { fail(e2); }
    setBusy(false);
  }
  async function otpSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const t = await verifyOtp(phone, otp, "registration");
      if (!t) setErr(L("কোডটি সঠিক নয়। ৬ ডিজিটের কোড আবার লিখুন।", "That code is not right. Re-enter the 6-digit code."));
      else { setVtoken(t); setStep("consent"); }
    } catch (e2) { fail(e2); }
    setBusy(false);
  }
  async function resend() { setErr(""); try { await sendCode(); } catch (e) { fail(e); } }
  async function finish() {
    setBusy(true); setErr("");
    try {
      const r = await register({
        name: f.name, phone, password: f.password, role, email: f.email.trim() || undefined, verification_token: vtoken,
        language: lang, communication: f.communication, village: f.village.trim() || undefined,
        ...(role === "expert" ? { specialization: f.specialization, credentials: f.credentials } : { division_id: geo.division_id || undefined, district_id: geo.district_id || undefined, upazila_id: geo.upazila_id || undefined, union_id: geo.union_id || undefined }),
        terms_accepted: consent.terms, privacy_accepted: consent.privacy, location_permission_granted: consent.location,
      });
      if (r.pending) { setPendingMsg(r.message ?? ""); setStep("pending"); }
      else if (r.user) { setUser(r.user); router.push(homeFor(r.user)); }
    } catch (e) { fail(e); }
    setBusy(false);
  }

  const alertBox = err && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 ring-1 ring-inset ring-clay-100">{err}</p>;
  const steps: Step[] = ["details", "otp", "consent"];
  const roles = [["farmer", "আমি কৃষক", "I am a farmer", Sprout], ["agent", "কৃষি সহায়ক", "Farm agent", Users], ["expert", "বিশেষজ্ঞ", "Expert", Stethoscope]] as const;

  if (step === "pending") {
    return (
      <AuthFrame title={L("আবেদন জমা হয়েছে", "Application submitted")} sub="">
        <div className="space-y-4 rounded-card bg-sun-50 p-5 text-sun-800 ring-1 ring-inset ring-sun-100">
          <Clock size={28} />
          <p>{pendingMsg || L("বিশেষজ্ঞ রেজিস্ট্রেশন জমা হয়েছে। অ্যাডমিন অনুমোদনের পর অ্যাকাউন্ট সক্রিয় হবে।", "Expert registration submitted. Your account will be active after admin approval.")}</p>
        </div>
        <Link href="/login" className="mt-6 block text-center font-bold text-brand-700 hover:underline">{L("লগইন পাতায় যান", "Go to log in")}</Link>
      </AuthFrame>
    );
  }

  return (
    <AuthFrame title={L("একাউন্ট খুলুন", "Create your account")} sub={L("এক মিনিটেই শুরু করা যায়।", "It takes about a minute.")}>
      <ol className="mb-7 flex gap-2" aria-label="Progress">
        {steps.map((s, i) => <li key={s} className={cn("h-1.5 flex-1 rounded-full", steps.indexOf(step) >= i ? "bg-brand-600" : "bg-line-strong")} />)}
      </ol>

      {step === "details" && (
        <form onSubmit={details} className="space-y-4">
          <div className="grid grid-cols-3 gap-2">
            {roles.map(([v, b, e, I]) => (
              <button key={v} type="button" onClick={() => { setRole(v); setF({ ...f, password: "" }); }} aria-pressed={role === v} className={cn("flex min-h-[64px] flex-col items-center justify-center gap-1 rounded-ctl border-2 px-2 text-center text-[15px] font-semibold", role === v ? "border-brand-600 bg-brand-50 text-brand-700" : "border-line-strong bg-white")}><I size={20} />{L(b, e)}</button>
            ))}
          </div>
          <div><label className="label" htmlFor="n">{L("আপনার নাম", "Your name")}</label><input id="n" className="field" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required /></div>
          <div><label className="label" htmlFor="p">{L("মোবাইল নম্বর", "Mobile number")}</label><input id="p" className="field" inputMode="tel" placeholder="01XXXXXXXXX" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} required /></div>
          <div><label className="label" htmlFor="em">{role === "expert" ? L("ইমেইল", "Email") : L("ইমেইল (ঐচ্ছিক)", "Email (optional)")}</label><input id="em" type="email" required={role === "expert"} className="field" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
          <div><label className="label" htmlFor="pw">{pwHint}</label><input id="pw" type="password" inputMode={role === "farmer" ? "numeric" : "text"} autoComplete="new-password" className="field" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></div>

          {role === "expert" ? (
            <>
              <div><label className="label" htmlFor="sp">{L("বিশেষায়িত ক্ষেত্র", "Specialization")}</label><input id="sp" className="field" placeholder={L("যেমন: উদ্ভিদ রোগতত্ত্ব", "e.g. Plant Pathology")} value={f.specialization} onChange={(e) => setF({ ...f, specialization: e.target.value })} required /></div>
              <div><label className="label" htmlFor="cr">{L("শিক্ষাগত যোগ্যতা / প্রতিষ্ঠান", "Credentials")}</label><input id="cr" className="field" placeholder="PhD in Agriculture, BARI" value={f.credentials} onChange={(e) => setF({ ...f, credentials: e.target.value })} required /></div>
            </>
          ) : (
            <>
              <GeoCascade value={geo} onChange={setGeo} />
              <div><label className="label" htmlFor="vl">{L("গ্রাম / পাড়া", "Village")}</label><input id="vl" className="field" value={f.village} onChange={(e) => setF({ ...f, village: e.target.value })} /></div>
            </>
          )}
          <div>
            <span className="label">{L("যোগাযোগের মাধ্যম", "Preferred contact")}</span>
            <div className="grid grid-cols-3 gap-2">
              {COMM.map(([v, b, e]) => <button key={v} type="button" aria-pressed={f.communication === v} onClick={() => setF({ ...f, communication: v })} className={cn("min-h-[48px] rounded-ctl border-2 font-semibold", f.communication === v ? "border-brand-600 bg-brand-50 text-brand-700" : "border-line-strong bg-white")}>{L(b, e)}</button>)}
            </div>
          </div>
          {alertBox}
          <Button type="submit" loading={busy} size="lg" className="w-full">{L("কোড পাঠান", "Send code")}</Button>
        </form>
      )}

      {step === "otp" && (
        <form onSubmit={otpSubmit} className="space-y-4">
          <p className="rounded-ctl bg-sky-50 px-4 py-3 text-sky-700">{L(`${phone} নম্বরে ৬ ডিজিটের কোড পাঠানো হয়েছে (৫ মিনিট বৈধ)।`, `We sent a 6-digit code to ${phone} (valid for 5 minutes).`)}{process.env.NEXT_PUBLIC_USE_MOCK !== "false" && <span className="block text-[14px] opacity-80">{L("ডেমোতে যেকোনো ৬ সংখ্যা চলবে।", "In the demo, any 6 digits work.")}</span>}</p>
          <input aria-label="OTP" className="field text-center font-display text-3xl tracking-[0.5em] !min-h-[60px]" inputMode="numeric" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} autoFocus />
          {alertBox}
          <Button type="submit" loading={busy} disabled={otp.length !== 6} size="lg" className="w-full">{L("যাচাই করুন", "Verify")}</Button>
          <ResendButton left={cd.left} onClick={resend} />
          <button type="button" onClick={() => { setStep("details"); setOtp(""); setErr(""); }} className="block w-full text-center text-ink-soft hover:underline">{L("নম্বর বদলান", "Change number")}</button>
        </form>
      )}

      {step === "consent" && (
        <div className="space-y-3">
          <p className="text-ink-soft">{L("আপনার তথ্য কীভাবে ব্যবহার হবে তা আপনি ঠিক করেন। * চিহ্নিতগুলো সেবার জন্য দরকার।", "You decide how your data is used. Items marked * are needed for the service.")}</p>
          {([
            ["terms", "ব্যবহারের শর্তে সম্মত", "I accept the terms of use", true],
            ["privacy", "গোপনীয়তা নীতিতে সম্মত (ছবি ও তথ্য বিশ্লেষণ ও সংরক্ষণসহ)", "I accept the privacy policy (including photo analysis and storage)", true],
            ["location", "আমার এলাকার তথ্য ব্যবহারে সম্মত (ঐচ্ছিক)", "My location may be used for local advice (optional)", false],
            ["ai", "নাম গোপন রেখে সিস্টেম উন্নয়নে ছবি ব্যবহার করা যাবে (ঐচ্ছিক)", "Anonymised photos may improve the system (optional)", false],
          ] as const).map(([k, b, e, req]) => (
            <label key={k} className="flex cursor-pointer items-start gap-3 rounded-card border border-line-strong bg-white p-4 has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50">
              <input type="checkbox" className="mt-1 h-6 w-6 accent-[#178049]" checked={consent[k]} onChange={(ev) => setConsent({ ...consent, [k]: ev.target.checked })} />
              <span>{L(b, e)} {req && <span className="text-clay-600">*</span>}</span>
            </label>
          ))}
          {alertBox}
          <Button onClick={finish} loading={busy} disabled={!(consent.terms && consent.privacy)} size="lg" className="w-full"><CheckCircle2 size={20} />{role === "expert" ? L("আবেদন জমা দিন", "Submit application") : L("শুরু করুন", "Get started")}</Button>
        </div>
      )}
      <p className="mt-6 text-center text-ink-soft">{L("আগে থেকেই একাউন্ট আছে?", "Already registered?")} <Link href="/login" className="font-bold text-brand-700 hover:underline">{L("লগইন", "Log in")}</Link></p>
    </AuthFrame>
  );
}
