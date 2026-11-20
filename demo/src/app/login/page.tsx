"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import bcrypt from "bcryptjs";
import { GEO_DIVISIONS, GEO_DISTRICTS, GEO_UPAZILAS } from "@/lib/geoDatabase";
import { useAppStore, UserRole } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sprout,
  UserCheck,
  ShieldAlert,
  Lock,
  AlertCircle,
  LogIn,
  Languages,
  Database,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, setRole, language, setLanguage } = useAppStore();
  const isBn = language === "bn";

  const [selectedRole, setSelectedRole] = useState<UserRole>("farmer");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Switch role tabs & default demo credentials from Supabase
  const handleRoleTabChange = (r: UserRole) => {
    setSelectedRole(r);
    setErrorMsg("");
    setPhoneNumber("");
    setPassword("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    // Admin login: authenticates against backend or Supabase
    if (selectedRole === "admin" || phoneNumber.trim().toLowerCase() === "admin") {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      try {
        const backendResp = await fetch(`${backendUrl}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: phoneNumber.trim(),
            password: password,
          }),
        });
        if (backendResp.ok) {
          const resData = await backendResp.json();
          const authData = resData.data || resData;
          if (authData.access_token && typeof window !== "undefined") {
            localStorage.setItem("kb_access_token", authData.access_token);
          }
          const u = authData.user || {};
          login({
            id: u.id || "admin",
            fullName: u.full_name || (isBn ? "সিস্টেম অ্যাডমিনিস্ট্রেটর" : "System Administrator"),
            phoneNumber: u.phone_number || "admin",
            role: "admin",
            division: u.division || "ঢাকা",
            district: u.district || "ঢাকা সদর",
          });
          setRole("admin");
          router.push("/admin");
          setIsLoading(false);
          return;
        } else {
          setErrorMsg(
            isBn
              ? "অ্যাডমিন ইউজারনেম বা পাসওয়ার্ড সঠিক নয়।"
              : "Invalid admin username or password."
          );
          setIsLoading(false);
          return;
        }
      } catch {
        setErrorMsg(
          isBn
            ? "অ্যাডমিন লগইনের জন্য ব্যাকএন্ড সার্ভার চালু থাকতে হবে।"
            : "Backend server must be running for admin login."
        );
        setIsLoading(false);
        return;
      }
    }

    const cleanPhone = phoneNumber.replace(/[^0-9]/g, "");
    const coreDigits = cleanPhone.length >= 10 ? cleanPhone.slice(-10) : cleanPhone;
    const bdOperatorRegex = /^[3-9]\d{8}$/; // last 9 digits after 01

    if (cleanPhone.length < 10 || (coreDigits.startsWith("1") && !bdOperatorRegex.test(coreDigits.slice(1)))) {
      setErrorMsg(
        isBn
          ? "শুধুমাত্র বাংলাদেশের বৈধ মোবাইল নম্বর দিন (যেমন: 017XXXXXXXX, 018XXXXXXXX)।"
          : "Please enter a valid Bangladesh mobile number (e.g. 017XXXXXXXX)."
      );
      setIsLoading(false);
      return;
    }

    const pLocal = "0" + coreDigits;
    const pE164 = "+880" + coreDigits;
    const p880 = "880" + coreDigits;
    const pCore = coreDigits;

    try {
      // 1. First attempt login through FastAPI Backend
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      let backendFailed = false;

      try {
        const backendResp = await fetch(`${backendUrl}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone_number: pLocal,
            password: password,
          }),
        });

        if (backendResp.ok) {
          const resData = await backendResp.json();
          const authData = resData.data || resData;
          if (authData?.user) {
            const u = authData.user;
            const rawRole = typeof u.role === "object" ? u.role?.code : u.role;
            const dbRole: UserRole =
              rawRole === "admin" || rawRole === "administrator"
                ? "admin"
                : rawRole === "expert"
                ? "expert"
                : "farmer";

            if (authData.access_token && typeof window !== "undefined") {
              localStorage.setItem("kb_access_token", authData.access_token);
            }

            const divName = u.division || (GEO_DIVISIONS.find((d) => d.id === u.division_id)?.nameBn) || "রাজশাহী";
            const distName = u.district || (GEO_DISTRICTS.find((d) => d.id === u.district_id)?.nameBn) || "বগুড়া";
            const upzName = u.upazila || (GEO_UPAZILAS.find((up) => up.id === u.upazila_id)?.nameBn) || "";

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
            if ((dbRole as string) === "admin") router.push("/admin");
            else if (dbRole === "expert") router.push("/expert");
            else router.push("/");
            return;
          }
        } else if (backendResp.status === 401 || backendResp.status === 403 || backendResp.status === 400) {
          // Backend actively rejected with invalid credentials — STRICT rejection!
          const errData = await backendResp.json().catch(() => ({}));
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
        // Backend server offline (network error)
        backendFailed = true;
      }

      // 2. Direct REST query to Supabase users table (only if backend is offline)
      if (backendFailed) {
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

            const divName = GEO_DIVISIONS.find((d) => d.id === user.division_id)?.nameBn || "রাজশাহী";
            const distName = GEO_DISTRICTS.find((d) => d.id === user.district_id)?.nameBn || "বগুড়া";
            const upzName = GEO_UPAZILAS.find((up) => up.id === user.upazila_id)?.nameBn || "";

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

            if ((dbRole as string) === "admin") router.push("/admin");
            else if (dbRole === "expert") router.push("/expert");
            else router.push("/");
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
      }
    } catch (err) {
      console.error("Login process error:", err);
    }

    // Default error if neither backend nor database verified the user
    setErrorMsg(
      isBn
        ? "লগইন ব্যর্থ হয়েছে। ফোন নম্বর বা পাসওয়ার্ড সঠিক নয়।"
        : "Login failed. Invalid phone number or password."
    );
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10 p-4">
      {/* Top Brand & Language Bar */}
      <div className="w-full max-w-md flex items-center justify-between mb-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-500 flex items-center justify-center text-white shadow-md">
            <Sprout className="h-5 w-5" />
          </div>
          <span className="font-black text-xl text-foreground tracking-tight">
            {isBn ? "কৃষিবন্ধু বাংলাদেশ" : "KrishiBondhu BD"}
          </span>
        </Link>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setLanguage(isBn ? "en" : "bn")}
          className="h-8 text-xs font-semibold"
        >
          <Languages className="h-3.5 w-3.5 mr-1" />
          <span>{isBn ? "EN" : "বাংলা"}</span>
        </Button>
      </div>

      {/* Main Login Card */}
      <Card className="w-full max-w-md border border-emerald-500/20 shadow-xl bg-card">
        <CardContent className="p-6 sm:p-8 space-y-6">
          <div className="text-center space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 text-[11px] font-bold mb-1">
              <Database className="h-3 w-3" />
              <span>{isBn ? "সুপাবেস লাইভ ডাটাবেজ সংযুক্ত" : "Live Supabase Connected"}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-foreground">
              {isBn ? "অ্যাকাউন্টে প্রবেশ করুন" : "Sign In to Your Account"}
            </h1>
            <p className="text-xs text-muted-foreground">
              {isBn
                ? "আপনার সুনির্দিষ্ট রোল ও রেজিস্টার্ড মোবাইল নম্বর দিন"
                : "Select role and enter your verified credentials"}
            </p>
          </div>

          {/* Role Tabs */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-muted-foreground block">
              {isBn ? "১. আপনি কোন রোলে লগইন করতে চান?" : "1. Select Account Role:"}
            </span>
            <div className="grid grid-cols-3 gap-1.5 p-1 bg-muted rounded-xl text-xs font-medium">
              <button
                type="button"
                onClick={() => handleRoleTabChange("farmer")}
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
                onClick={() => handleRoleTabChange("expert")}
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
                onClick={() => handleRoleTabChange("admin")}
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

          {/* Error Message Alert */}
          {errorMsg && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start gap-2 text-xs text-rose-600 dark:text-rose-400 animate-in fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium mb-1 block text-foreground">
                {selectedRole === "admin"
                  ? isBn
                    ? "ইউজারনেম (Username)"
                    : "Username"
                  : isBn
                  ? "সুপাবেসে রেজিস্টার্ড মোবাইল নম্বর"
                  : "Registered Phone"}
              </label>
              <div className="relative">
                {selectedRole !== "admin" && (
                  <span className="absolute left-3 top-2.5 text-xs text-muted-foreground font-semibold">
                    +880
                  </span>
                )}
                <Input
                  className={selectedRole === "admin" ? "text-sm" : "pl-14 text-sm font-mono"}
                  placeholder={selectedRole === "admin" ? "admin" : "17XXXXXXXX"}
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block text-foreground">
                {selectedRole === "admin"
                  ? isBn
                    ? "পাসওয়ার্ড (Password)"
                    : "Password"
                  : isBn
                  ? "পাসওয়ার্ড / পিন (PIN)"
                  : "Password / PIN"}
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  className="pl-9 text-sm"
                  placeholder={selectedRole === "admin" ? "admin" : "••••••••"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {selectedRole === "admin" && (
                <p className="text-[11px] text-muted-foreground mt-1.5 font-medium">
                  {isBn
                    ? "🔒 শুধুমাত্র অ্যাডমিন ক্রেডেনশিয়াল: ইউজারনেম: admin এবং পাসওয়ার্ড: admin"
                    : "🔒 Only Admin credentials: username: admin and password: admin"}
                </p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className={`w-full font-bold text-white shadow-lg h-10 ${
                selectedRole === "farmer"
                  ? "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20"
                  : selectedRole === "expert"
                  ? "bg-blue-600 hover:bg-blue-700 shadow-blue-600/20"
                  : "bg-rose-600 hover:bg-rose-700 shadow-rose-600/20"
              }`}
            >
              <LogIn className="h-4 w-4 mr-1.5" />
              <span>
                {isLoading
                  ? isBn
                    ? "সুপাবেসে যাচাই করা হচ্ছে..."
                    : "Verifying with Supabase..."
                  : isBn
                  ? `${selectedRole === "farmer" ? "কৃষক" : selectedRole === "expert" ? "কৃষিবিদ" : "অ্যাডমিন"} হিসেবে প্রবেশ করুন`
                  : `Sign In as ${selectedRole.toUpperCase()}`}
              </span>
            </Button>
          </form>


          {/* Registration Option */}
          <div className="text-center pt-3 border-t text-xs text-muted-foreground">
            {isBn ? "নতুন অ্যাকাউন্ট প্রয়োজন?" : "Don't have an account?"}{" "}
            <Link
              href="/register"
              className="text-emerald-600 hover:underline font-bold"
            >
              {isBn ? "বিনামূল্যে নিবন্ধন করুন" : "Register Free"}
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
