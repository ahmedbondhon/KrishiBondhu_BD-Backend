"use client";

import React, { useState } from "react";
import { useAppStore, UserRole } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
    role,
    setRole,
  } = useAppStore();

  const isBn = language === "bn";

  // Form states
  const [phoneNumber, setPhoneNumber] = useState("01754890387");
  const [password, setPassword] = useState("123456");
  const [fullName, setFullName] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRole>("farmer");
  const [selectedDivision, setSelectedDivision] = useState("রাজশাহী");
  const [district, setDistrict] = useState("বগুড়া");
  const [upazila, setUpazila] = useState("শেরপুর");

  // OTP flow simulation
  const [showOtpScreen, setShowOtpScreen] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [simulatedOtp, setSimulatedOtp] = useState("123456");

  if (!authModalOpen) return null;

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedRole === "admin" || phoneNumber.trim().toLowerCase() === "admin") {
      if (phoneNumber.trim().toLowerCase() !== "admin" || password !== "admin") {
        alert(isBn ? "অ্যাডমিন লগইনের জন্য শুধুমাত্র username: admin এবং password: admin দিন।" : "For admin login, use only username: admin and password: admin.");
        return;
      }
      login({
        id: "admin-master-001",
        fullName: isBn ? "সিস্টেম অ্যাডমিনিস্ট্রেটর" : "System Administrator",
        phoneNumber: "admin",
        role: "admin",
        division: "ঢাকা",
        district: "ঢাকা সদর",
        upazila: "মতিঝিল",
      });
      setRole("admin");
      closeAuthModal();
      return;
    }
    login({
      id: "user-" + Math.floor(Math.random() * 1000),
      fullName:
        selectedRole === "farmer"
          ? "মো: আব্দুল্লাহ (কৃষক)"
          : selectedRole === "expert"
          ? "ড. রফিকুল ইসলাম (কৃষিবিদ)"
          : "অ্যাডমিন অ্যাডমিনিস্ট্রেটর",
      phoneNumber,
      role: selectedRole,
      division: selectedDivision,
      district,
      upazila,
    });
    setRole(selectedRole);
    closeAuthModal();
  };

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    setSimulatedOtp(code);
    setShowOtpScreen(true);
  };

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    login({
      id: "user-" + Math.floor(Math.random() * 1000),
      fullName: fullName || (isBn ? "কৃষক বন্ধু" : "Farmer Friend"),
      phoneNumber,
      role: selectedRole,
      division: selectedDivision,
      district,
      upazila,
    });
    setRole(selectedRole);
    setShowOtpScreen(false);
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
                <Button type="submit" className="w-1/2 bg-emerald-600 hover:bg-emerald-700">
                  {isBn ? "যাচাই ও প্রবেশ" : "Verify & Login"}
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
                className={`w-full font-bold text-white shadow-lg ${
                  selectedRole === "farmer"
                    ? "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20"
                    : selectedRole === "expert"
                    ? "bg-blue-600 hover:bg-blue-700 shadow-blue-600/20"
                    : "bg-rose-600 hover:bg-rose-700 shadow-rose-600/20"
                }`}
              >
                <span>
                  {isBn
                    ? `${selectedRole === "farmer" ? "কৃষক" : selectedRole === "expert" ? "কৃষিবিদ" : "অ্যাডমিন"} হিসেবে লগইন করুন`
                    : `Login as ${selectedRole.toUpperCase()}`}
                </span>
                <ArrowRight className="h-4 w-4 ml-1.5" />
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

              <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700">
                <span>{isBn ? "পরবর্তী: ওটিপি কোড পাঠান" : "Send Verification OTP"}</span>
                <ArrowRight className="h-4 w-4 ml-1.5" />
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
