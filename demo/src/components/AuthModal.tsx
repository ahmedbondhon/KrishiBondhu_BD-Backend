"use client";

import React, { useState } from "react";
import bcrypt from "bcryptjs";
import { GEO_DIVISIONS, GEO_DISTRICTS, GEO_UPAZILAS } from "@/lib/geoDatabase";
import { useAppStore, UserRole } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BACKEND_URL } from "@/lib/api";
import {
  X,
  Phone,
  Lock,
  User,
  MapPin,
  CheckCircle2,
  KeyRound,
  ShieldCheck,
  ArrowRight,
  Sprout,
  UserCheck,
  ShieldAlert,
  Loader2,
  AlertCircle,
} from "lucide-react";

const DIVISIONS = ["ঢাকা", "চট্টগ্রাম", "রাজশাহী", "খুলনা", "বরিশাল", "সিলেট", "রংপুর", "ময়মনসিংহ"];

export default function AuthModal() {
  const {
    authModalOpen,
    authModalMode,
    closeAuthModal,
    openAuthModal,
    login,
    language,
    setRole,
  } = useAppStore();

  const isBn = language === "bn";

  // Form states
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRole>("farmer");
  const [selectedDivision, setSelectedDivision] = useState("রাজশাহী");
  const [district, setDistrict] = useState("বগুড়া");
  const [upazila, setUpazila] = useState("শেরপুর");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // OTP flow
  const [showOtpScreen, setShowOtpScreen] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [simulatedOtp, setSimulatedOtp] = useState("");
  const [pendingRegisterData, setPendingRegisterData] = useState<{
    phone: string; fullName: string; password: string; role: UserRole; division: string; district: string; upazila: string;
  } | null>(null);

  if (!authModalOpen) return null;

  // ─── Login ───────────────────────────────────────────────
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    // Admin login
    if (selectedRole === "admin" || phoneNumber.trim().toLowerCase() === "admin") {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: phoneNumber.trim(), password: password }),
        });
        if (res.ok) {
          const data = await res.json();
          const authData = data.data || data;
          if (authData?.access_token && typeof window !== "undefined") {
            localStorage.setItem("kb_access_token", authData.access_token);
          }
          const u = authData?.user;
          login({
            id: u?.id || "admin",
            fullName: u?.full_name || (isBn ? "সিস্টেম অ্যাডমিনিস্ট্রেটর" : "System Administrator"),
            phoneNumber: u?.phone_number || "admin",
            role: "admin",
            division: u?.division || "ঢাকা",
            district: u?.district || "ঢাকা সদর",
            upazila: u?.upazila || "মতিঝিল",
          });
          setRole("admin");
          setIsLoading(false);
          closeAuthModal();
          return;
        } else {
          setErrorMsg(isBn ? "ভুল অ্যাডমিন ইউজারনেম বা পাসওয়ার্ড।" : "Invalid admin username or password.");
          setIsLoading(false);
          return;
        }
      } catch {
        setErrorMsg(isBn ? "অ্যাডমিন লগইনের জন্য ব্যাকএন্ড সার্ভার সচল থাকা আবশ্যক।" : "Backend server must be running for admin login.");
        setIsLoading(false);
        return;
      }
    }
      closeAuthModal();
      return;
    }

    // Farmer / Expert login via Backend & Supabase fallback
    const cleanPhone = phoneNumber.replace(/[^0-9]/g, "");
    const coreDigits = cleanPhone.length >= 10 ? cleanPhone.slice(-10) : cleanPhone;
    const bdOperatorRegex = /^[3-9]\d{8}$/;

    if (cleanPhone.length < 10 || (coreDigits.startsWith("1") && !bdOperatorRegex.test(coreDigits.slice(1)))) {
      setErrorMsg(
        isBn
          ? "শুধুমাত্র বাংলাদেশের বৈধ মোবাইল নম্বর দিন (যেমন: 017XXXXXXXX)।"
          : "Please enter a valid Bangladesh mobile number (e.g. 017XXXXXXXX)."
      );
      setIsLoading(false);
      return;
    }

    const pLocal = "0" + coreDigits;
    const pE164 = "+880" + coreDigits;
    const p880 = "880" + coreDigits;
    const pCore = coreDigits;

    let backendFailed = false;

    // 1. First attempt login through FastAPI Backend
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: pLocal, password }),
      });
      if (res.ok) {
        const data = await res.json();
        const authData = data.data || data;
        if (authData?.access_token && typeof window !== "undefined") {
          localStorage.setItem("kb_access_token", authData.access_token);
        }

        const u = authData?.user;
        if (u) {
          const rawRole = typeof u.role === "object" ? u.role?.code : u.role;
          const dbRole: UserRole =
            rawRole === "admin" || rawRole === "administrator" ? "admin"
            : rawRole === "expert" ? "expert" : "farmer";

          const divName = u.division || (GEO_DIVISIONS.find((d) => d.id === u.division_id)?.nameBn) || selectedDivision;
          const distName = u.district || (GEO_DISTRICTS.find((d) => d.id === u.district_id)?.nameBn) || district;
          const upzName = u.upazila || (GEO_UPAZILAS.find((up) => up.id === u.upazila_id)?.nameBn) || upazila;

          login({
            id: u.id,
            fullName: u.full_name,
            phoneNumber: u.phone_number,
            role: dbRole,
            division: divName,
            district: distName,
            upazila: upzName,
          });
          setRole(dbRole);
          setIsLoading(false);
          closeAuthModal();
          return;
        }
      } else if (res.status === 401 || res.status === 403 || res.status === 400) {
        // Backend actively evaluated and rejected the credentials — STRICT!
        const errData = await res.json().catch(() => ({}));
        const msg =
          errData?.detail?.message_bn ||
          errData?.message ||
          (isBn
            ? "ফোন নম্বর বা পাসওয়ার্ড ভুল হয়েছে। অনুগ্রহ করে সঠিক তথ্য দিন।"
            : "Invalid phone number or password. Please try again.");
        setErrorMsg(typeof msg === "string" ? msg : JSON.stringify(msg));
        setIsLoading(false);
        return;
      } else {
        backendFailed = true;
      }
    } catch {
      // Backend not running (network error); fallback to Supabase
      backendFailed = true;
    }

    // 2. Direct REST query to Supabase users table (only if backend is offline)
    if (backendFailed) {
      try {
        const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
        const sbKey =
          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

        const queryFilter = `or=(phone_number.eq.${pLocal},phone_number.eq.${pE164},phone_number.eq.${p880},phone_number.eq.${pCore},phone_number.eq.${cleanPhone})`;
        const resp = await fetch(
          `${sbUrl}/users?${queryFilter}&select=id,phone_number,password_hash,full_name,status,division_id,district_id,upazila_id,roles(code,name)`,
          {
            headers: {
              apikey: sbKey,
              Authorization: `Bearer ${sbKey}`,
              "Content-Type": "application/json",
            },
          }
        );
        if (resp.ok) {
          const users = await resp.json();
          if (users && users.length > 0) {
            const user = users[0];

            // STRICT Password Verification against user.password_hash
            if (!user.password_hash) {
              setErrorMsg(
                isBn
                  ? "এই অ্যাকাউন্টের কোনো পাসওয়ার্ড সেট করা নেই।"
                  : "No password set for this account."
              );
              setIsLoading(false);
              return;
            }

            let isPasswordMatch = false;
            try {
              isPasswordMatch = bcrypt.compareSync(password, user.password_hash);
            } catch {
              isPasswordMatch = false;
            }

            if (!isPasswordMatch) {
              setErrorMsg(
                isBn
                  ? "পাসওয়ার্ড ভুল হয়েছে। অনুগ্রহ করে সঠিক পাসওয়ার্ড দিন।"
                  : "Invalid password. Please enter the correct password."
              );
              setIsLoading(false);
              return;
            }

            if (user.status === "suspended") {
              setErrorMsg(
                isBn
                  ? "আপনার অ্যাকাউন্টটি স্থগিত (Suspended) রয়েছে।"
                  : "Your account has been suspended."
              );
              setIsLoading(false);
              return;
            }

            const rawRole = user.roles?.code || "farmer";
            const dbRole: UserRole =
              rawRole === "administrator" || rawRole === "admin" || rawRole === "technical_admin"
                ? "admin"
                : rawRole === "expert"
                ? "expert"
                : "farmer";

            const divName = GEO_DIVISIONS.find((d) => d.id === user.division_id)?.nameBn || selectedDivision;
            const distName = GEO_DISTRICTS.find((d) => d.id === user.district_id)?.nameBn || district;
            const upzName = GEO_UPAZILAS.find((up) => up.id === user.upazila_id)?.nameBn || upazila;

            login({
              id: user.id,
              fullName: user.full_name || (isBn ? "কৃষক বন্ধু" : "Farmer Friend"),
              phoneNumber: user.phone_number || pLocal,
              role: dbRole,
              division: divName,
              district: distName,
              upazila: upzName,
            });
            setRole(dbRole);
            setIsLoading(false);
            closeAuthModal();
            return;
          } else {
            setErrorMsg(
              isBn
                ? "এই মোবাইল নম্বরটি ডাটাবেজে পাওয়া যায়নি। আপনি কি আগে নিবন্ধন (Register) করেছেন?"
                : "Mobile number not found in database. Have you registered an account?"
            );
            setIsLoading(false);
            return;
          }
        }
      } catch (err) {
        console.error("Supabase fallback error:", err);
      }
    }

    setErrorMsg(
      isBn
        ? "লগইন ব্যর্থ হয়েছে। ফোন নম্বর বা পাসওয়ার্ড সঠিক নয়।"
        : "Login failed. Invalid phone number or password."
    );
    setIsLoading(false);
  };

  // ─── Register Step 1: Send OTP ────────────────────────────
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    const cleanPhone = phoneNumber.replace(/[^0-9]/g, "");

    // Save pending data for step 2
    setPendingRegisterData({ phone: cleanPhone, fullName, password, role: selectedRole, division: selectedDivision, district, upazila });

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/otp/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: cleanPhone, purpose: "registration" }),
      });
      const data = await res.json();

      if (!res.ok || data.success === false) {
        // Backend may show demo OTP in response
        if (data?.otp_code || data?.demo_otp) {
          setSimulatedOtp(data.otp_code || data.demo_otp);
        } else {
          const msg = data?.detail?.message_bn || data?.error?.message_bn || data?.detail || (isBn ? "OTP পাঠাতে সমস্যা হয়েছে।" : "Failed to send OTP.");
          setErrorMsg(typeof msg === "string" ? msg : JSON.stringify(msg));
          setIsLoading(false);
          return;
        }
      }

      // Show OTP from backend demo_otp if available
      if (data?.data?.otp_code) setSimulatedOtp(data.data.otp_code);
      else if (!simulatedOtp) {
        // Fallback simulated OTP for demo
        setSimulatedOtp(Math.floor(100000 + Math.random() * 900000).toString());
      }

      setShowOtpScreen(true);
    } catch {
      // Backend not reachable — fallback simulated OTP
      const fallbackOtp = Math.floor(100000 + Math.random() * 900000).toString();
      setSimulatedOtp(fallbackOtp);
      setShowOtpScreen(true);
    }
    setIsLoading(false);
  };

  // ─── Register Step 2: Verify OTP & Complete Registration ──
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    const data = pendingRegisterData;
    if (!data) { setIsLoading(false); return; }

    try {
      // 1. Verify OTP
      const verifyRes = await fetch(`${BACKEND_URL}/api/v1/auth/otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: data.phone, otp_code: otpCode, purpose: "registration" }),
      });
      const verifyData = await verifyRes.json();
      const verificationToken = verifyData?.data?.verification_token || verifyData?.verification_token;

      // 2. Complete registration
      const regRes = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone_number: data.phone,
          password: data.password,
          full_name: data.fullName || (isBn ? "কৃষক বন্ধু" : "Farmer Friend"),
          role: data.role,
          verification_token: verificationToken || otpCode,
          terms_accepted: true,
          district: data.district,
          upazila: data.upazila,
        }),
      });
      const regData = await regRes.json();

      if (regRes.ok && (regData.success !== false)) {
        const authData = regData.data || regData;
        const u = authData?.user || regData?.user;
        if (authData?.access_token && typeof window !== "undefined") {
          localStorage.setItem("kb_access_token", authData.access_token);
        }
        login({
          id: u?.id || "user-" + data.phone,
          fullName: u?.full_name || data.fullName || (isBn ? "কৃষক বন্ধু" : "Farmer Friend"),
          phoneNumber: u?.phone_number || data.phone,
          role: data.role,
          division: data.division,
          district: data.district,
          upazila: data.upazila,
        });
      } else {
        const msg =
          regData?.detail?.message_bn ||
          regData?.error?.message_bn ||
          regData?.message ||
          (isBn ? "নিবন্ধন ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।" : "Registration failed. Please try again.");
        setErrorMsg(typeof msg === "string" ? msg : JSON.stringify(msg));
        setIsLoading(false);
        return;
      }
    } catch {
      // Backend unreachable: attempt direct Supabase insert
      try {
        const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
        const sbKey =
          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

        const roleResp = await fetch(`${sbUrl}/roles?code=eq.${data.role}&select=id`, {
          headers: { apikey: sbKey, Authorization: `Bearer ${sbKey}` },
        });
        const roles = await roleResp.json();
        const roleId =
          roles?.[0]?.id ||
          (data.role === "expert"
            ? "11000000-0000-0000-0000-000000000002"
            : "11000000-0000-0000-0000-000000000001");

        const salt = bcrypt.genSaltSync(12);
        const hashedPassword = bcrypt.hashSync(data.password, salt);

        const insertResp = await fetch(`${sbUrl}/users`, {
          method: "POST",
          headers: {
            apikey: sbKey,
            Authorization: `Bearer ${sbKey}`,
            "Content-Type": "application/json",
            Prefer: "return=representation",
          },
          body: JSON.stringify({
            phone_number: data.phone,
            password_hash: hashedPassword,
            full_name: data.fullName,
            role_id: roleId,
            status: "active",
            phone_verified: true,
            preferred_language: "bn",
          }),
        });

        if (insertResp.ok) {
          const createdUsers = await insertResp.json();
          const newId = createdUsers?.[0]?.id || "user-" + data.phone;
          login({
            id: newId,
            fullName: data.fullName || (isBn ? "কৃষক বন্ধু" : "Farmer Friend"),
            phoneNumber: data.phone,
            role: data.role,
            division: data.division,
            district: data.district,
            upazila: data.upazila,
          });
        } else {
          setErrorMsg(
            isBn
              ? "রেজিস্ট্রেশন ডাটাবেজে সংরক্ষণ করা যায়নি। নম্বরটি ইতিমধ্যে ব্যবহৃত হতে পারে।"
              : "Registration could not be saved to database."
          );
          setIsLoading(false);
          return;
        }
      } catch (sbErr) {
        console.error("Direct Supabase register error:", sbErr);
        setErrorMsg(
          isBn
            ? "সার্ভারের সাথে সংযোগ স্থাপন করা যায়নি।"
            : "Could not connect to server."
        );
        setIsLoading(false);
        return;
      }
    }

    setRole(data.role);
    setShowOtpScreen(false);
    setIsLoading(false);
    closeAuthModal();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-card border border-emerald-500/20 rounded-2xl shadow-2xl p-6 sm:p-8 overflow-hidden text-card-foreground">
        {/* Glow decor */}
        <div className="absolute top-0 right-0 w-36 h-36 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {showOtpScreen ? (
          /* OTP Screen */
          <div className="space-y-5">
            <div className="text-center space-y-2">
              <div className="mx-auto w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold tracking-tight">
                {isBn ? "ওটিপি (OTP) যাচাই করুন" : "Verify Phone OTP"}
              </h2>
              <p className="text-xs text-muted-foreground">
                {isBn
                  ? `+880 ${phoneNumber} নম্বরে পাঠানো ৬-সংখ্যার কোডটি লিখুন`
                  : `Enter the 6-digit code sent to +880 ${phoneNumber}`}
              </p>
            </div>

            {/* Simulated SMS Alert Banner */}
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-800 dark:text-amber-200 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold">
                <span>📱 {isBn ? "সিমুলেটেড এসএমএস:" : "Simulated SMS:"}</span>
              </div>
              <p>
                {isBn
                  ? `কৃষিবন্ধু ভেরিফিকেশন কোড: ${simulatedOtp}। এটি ৫ মিনিটের জন্য কার্যকর থাকবে।`
                  : `Your KrishiBondhu code is: ${simulatedOtp}. Valid for 5 minutes.`}
              </p>
            </div>

            {errorMsg && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start gap-2 text-xs text-rose-600 dark:text-rose-400 animate-in fade-in">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label className="text-xs font-medium mb-1 block">
                  {isBn ? "৬-সংখ্যার কোড" : "6-Digit Code"}
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-9 text-center tracking-widest text-lg font-mono font-bold"
                    placeholder="123456"
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOtpCode(simulatedOtp)}
                  className="w-1/2 text-xs"
                >
                  {isBn ? "অটো-ফিল কোড" : "Auto-fill Code"}
                </Button>
                <Button type="submit" disabled={isLoading} className="w-1/2 bg-emerald-600 hover:bg-emerald-700">
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : (isBn ? "যাচাই ও প্রবেশ" : "Verify & Login")}
                </Button>
              </div>
            </form>
          </div>
        ) : authModalMode === "login" ? (
          /* Login Screen */
          <div className="space-y-5">
            <div className="text-center space-y-1">
              <div className="inline-flex p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-500 text-white shadow-md mb-2">
                <Sprout className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold tracking-tight">
                {isBn ? "কৃষিবন্ধুতে লগইন করুন" : "Login to KrishiBondhu"}
              </h2>
              <p className="text-xs text-muted-foreground">
                {isBn
                  ? "আপনার রোল নির্বাচন করে অ্যাকাউন্টে প্রবেশ করুন"
                  : "Select role and enter credentials to access your dashboard"}
              </p>
            </div>

            {/* Role Tab Selector in Login */}
            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground block">
                {isBn ? "লগইন রোল নির্বাচন করুন:" : "Select Account Role:"}
              </span>
              <div className="grid grid-cols-3 gap-1.5 p-1 bg-muted rounded-xl text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setSelectedRole("farmer")}
                  className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                    selectedRole === "farmer"
                      ? "bg-emerald-600 text-white font-bold shadow-md"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Sprout className="h-3.5 w-3.5" />
                  <span>{isBn ? "কৃষক" : "Farmer"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRole("expert")}
                  className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                    selectedRole === "expert"
                      ? "bg-blue-600 text-white font-bold shadow-md"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <UserCheck className="h-3.5 w-3.5" />
                  <span>{isBn ? "কৃষিবিদ" : "Expert"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedRole("admin");
                    setPhoneNumber("admin");
                    setPassword("admin");
                  }}
                  className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                    selectedRole === "admin"
                      ? "bg-rose-600 text-white font-bold shadow-md"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <ShieldAlert className="h-3.5 w-3.5" />
                  <span>{isBn ? "অ্যাডমিন" : "Admin"}</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleLoginSubmit} className="space-y-3.5">
              {errorMsg && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start gap-2 text-xs text-rose-600 dark:text-rose-400 animate-in fade-in">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}
              <div>
                <label className="text-xs font-medium mb-1 block">
                  {selectedRole === "admin"
                    ? isBn
                      ? "ইউজারনেম (Username)"
                      : "Username"
                    : isBn
                    ? "মোবাইল নম্বর"
                    : "Mobile Number"}
                </label>
                <div className="relative">
                  {selectedRole !== "admin" && (
                    <span className="absolute left-3 top-2.5 text-xs text-muted-foreground font-semibold">
                      +880
                    </span>
                  )}
                  <Input
                    className={selectedRole === "admin" ? "text-sm" : "pl-14 text-sm"}
                    placeholder={selectedRole === "admin" ? "admin" : "17XXXXXXXX"}
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block">
                  {selectedRole === "admin"
                    ? isBn
                      ? "পাসওয়ার্ড (Password)"
                      : "Password"
                    : selectedRole === "farmer"
                    ? isBn
                      ? "৬-সংখ্যার পিন (PIN)"
                      : "6-Digit Numeric PIN"
                    : isBn
                    ? "পাসওয়ার্ড"
                    : "Password"}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    className="pl-9 text-sm"
                    placeholder={selectedRole === "admin" ? "admin" : "••••••"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className={`w-full font-bold text-white shadow-lg ${
                  selectedRole === "farmer"
                    ? "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20"
                    : selectedRole === "expert"
                    ? "bg-blue-600 hover:bg-blue-700 shadow-blue-600/20"
                    : "bg-rose-600 hover:bg-rose-700 shadow-rose-600/20"
                }`}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>
                      {isBn
                        ? `${selectedRole === "farmer" ? "কৃষক" : selectedRole === "expert" ? "কৃষিবিদ" : "অ্যাডমিন"} হিসেবে লগইন করুন`
                        : `Login as ${selectedRole.toUpperCase()}`}
                    </span>
                    <ArrowRight className="h-4 w-4 ml-1.5" />
                  </>
                )}
              </Button>
            </form>

            <div className="text-center pt-2 border-t text-xs text-muted-foreground">
              {isBn ? "নতুন অ্যাকাউন্ট প্রয়োজন?" : "Don't have an account?"}{" "}
              <button
                type="button"
                onClick={() => openAuthModal("register")}
                className="text-emerald-600 hover:underline font-semibold"
              >
                {isBn ? "বিনামূল্যে নিবন্ধন করুন" : "Register Free"}
              </button>
            </div>
          </div>
        ) : (
          /* Register Screen */
          <div className="space-y-4">
            <div className="text-center space-y-1">
              <h2 className="text-xl font-bold tracking-tight">
                {isBn ? "নতুন কৃষক নিবন্ধন" : "Farmer Registration"}
              </h2>
              <p className="text-xs text-muted-foreground">
                {isBn
                  ? "আপনার তথ্য দিয়ে বিনামূল্যে রেজিস্টার করুন"
                  : "Register for free smart agronomy advisory"}
              </p>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              <div>
                <label className="text-xs font-medium mb-1 block">
                  {isBn ? "আপনার পুরো নাম" : "Full Name"}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-9 text-sm"
                    placeholder={isBn ? "যেমন: মো: আব্দুল্লাহ" : "e.g. Md. Abdullah"}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block">
                  {isBn ? "মোবাইল নম্বর" : "Mobile Number"}
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-xs text-muted-foreground font-semibold">
                    +880
                  </span>
                  <Input
                    className="pl-14 text-sm"
                    placeholder="17XXXXXXXX"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-medium mb-1 block">
                    {isBn ? "বিভাগ" : "Division"}
                  </label>
                  <select
                    value={selectedDivision}
                    onChange={(e) => setSelectedDivision(e.target.value)}
                    className="w-full text-xs rounded-md border border-input bg-background px-3 py-2"
                  >
                    {DIVISIONS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block">
                    {isBn ? "জেলা" : "District"}
                  </label>
                  <Input
                    className="text-xs h-9"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    required
                  />
                </div>
              </div>

              <Button type="submit" disabled={isLoading} className="w-full bg-emerald-600 hover:bg-emerald-700">
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>{isBn ? "পরবর্তী: ওটিপি কোড পাঠান" : "Send Verification OTP"}</span>
                    <ArrowRight className="h-4 w-4 ml-1.5" />
                  </>
                )}
              </Button>
            </form>

            <div className="text-center pt-2 border-t text-xs text-muted-foreground">
              {isBn ? "আগের অ্যাকাউন্ট আছে?" : "Already registered?"}{" "}
              <button
                type="button"
                onClick={() => openAuthModal("login")}
                className="text-emerald-600 hover:underline font-semibold"
              >
                {isBn ? "লগইন করুন" : "Login here"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
