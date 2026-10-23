"use client";

import React, { useState, useEffect, useRef } from "react";
import Navbar from "@/components/Navbar";
import AuthModal from "@/components/AuthModal";
import { useAppStore } from "@/store/useAppStore";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  User,
  Phone,
  MapPin,
  ShieldCheck,
  Calendar,
  Languages,
  Database,
  CheckCircle2,
  RefreshCw,
  Loader2,
  Lock,
  Camera,
  UploadCloud,
  KeyRound,
  Trash2,
} from "lucide-react";
import {
  GEO_DIVISIONS,
  getDistrictsByDivision,
  getUpazilasByDistrict,
  getUnionsByUpazila,
} from "@/lib/geoDatabase";
import { uploadToSupabaseStorage } from "@/lib/supabaseStorage";
import bcrypt from "bcryptjs";

export default function ProfilePage() {
  const { currentUser, language, setLanguage, login } = useAppStore();
  const isBn = language === "bn";
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const [loading, setLoading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Profile data
  const [fullName, setFullName] = useState(currentUser?.fullName || "মো: আব্দুর রহিম");
  const [avatarUrl, setAvatarUrl] = useState(currentUser?.avatarUrl || "");

  // Password change state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Geographic state with IDs
  const defaultDiv = GEO_DIVISIONS[0]?.id || "";
  const [divisionId, setDivisionId] = useState(defaultDiv);
  const currentDistricts = getDistrictsByDivision(divisionId);

  const defaultDist = currentDistricts[0]?.id || "";
  const [districtId, setDistrictId] = useState(defaultDist);
  const currentUpazilas = getUpazilasByDistrict(districtId);

  const defaultUpz = currentUpazilas[0]?.id || "";
  const [upazilaId, setUpazilaId] = useState(defaultUpz);
  const currentUnions = getUnionsByUpazila(upazilaId);

  const defaultUnion = currentUnions[0]?.id || "";
  const [unionId, setUnionId] = useState(defaultUnion);

  // Fetch full live profile from Supabase
  const loadProfile = async () => {
    if (!currentUser?.phoneNumber) return;
    setLoading(true);
    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      const cleanPhone = currentUser.phoneNumber.replace(/[^0-9]/g, "");
      const formattedPhone = cleanPhone.startsWith("880")
        ? "+" + cleanPhone
        : cleanPhone.startsWith("01")
        ? "+88" + cleanPhone
        : "+880" + cleanPhone;

      const resp = await fetch(
        `${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})&select=*`,
        {
          headers: { apikey: sbKey, Authorization: `Bearer ${sbKey}` },
        }
      );
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.length > 0) {
          const u = data[0];
          setFullName(u.full_name || fullName);
          if (u.avatar_url) setAvatarUrl(u.avatar_url);

          if (u.division_id) {
            setDivisionId(u.division_id);
            if (u.district_id) setDistrictId(u.district_id);
            if (u.upazila_id) setUpazilaId(u.upazila_id);
            if (u.union_id) setUnionId(u.union_id);
          }
        }
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    const fetchProfile = async () => {
      if (!currentUser?.phoneNumber) return;
      try {
        const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
        const sbKey =
          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

        const cleanPhone = currentUser.phoneNumber.replace(/[^0-9]/g, "");
        const formattedPhone = cleanPhone.startsWith("880")
          ? "+" + cleanPhone
          : cleanPhone.startsWith("01")
          ? "+88" + cleanPhone
          : "+880" + cleanPhone;

        const resp = await fetch(
          `${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})&select=*`,
          {
            headers: { apikey: sbKey, Authorization: `Bearer ${sbKey}` },
          }
        );
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.length > 0 && !ignore) {
            const u = data[0];
            setFullName(u.full_name || fullName);
            if (u.avatar_url) setAvatarUrl(u.avatar_url);

            if (u.division_id) {
              setDivisionId(u.division_id);
              if (u.district_id) setDistrictId(u.district_id);
              if (u.upazila_id) setUpazilaId(u.upazila_id);
              if (u.union_id) setUnionId(u.union_id);
            }
          }
        }
      } catch {
        // ignore
      }
    };
    fetchProfile();
    return () => {
      ignore = true;
    };
  }, [currentUser?.phoneNumber]);

  const handleDivisionChange = (newDivId: string) => {
    setDivisionId(newDivId);
    const dists = getDistrictsByDivision(newDivId);
    const firstDist = dists[0]?.id || "";
    setDistrictId(firstDist);

    const upzs = getUpazilasByDistrict(firstDist);
    const firstUpz = upzs[0]?.id || "";
    setUpazilaId(firstUpz);

    const uns = getUnionsByUpazila(firstUpz);
    setUnionId(uns[0]?.id || "");
  };

  const handleDistrictChange = (newDistId: string) => {
    setDistrictId(newDistId);
    const upzs = getUpazilasByDistrict(newDistId);
    const firstUpz = upzs[0]?.id || "";
    setUpazilaId(firstUpz);

    const uns = getUnionsByUpazila(firstUpz);
    setUnionId(uns[0]?.id || "");
  };

  const handleUpazilaChange = (newUpzId: string) => {
    setUpazilaId(newUpzId);
    const uns = getUnionsByUpazila(newUpzId);
    setUnionId(uns[0]?.id || "");
  };

  // Avatar Upload to Supabase Storage "avatars" folder
  const handleAvatarFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setErrorMsg(isBn ? "ছবির সাইজ সর্বোচ্চ ২ মেগাবাইট (2MB) হতে পারবে।" : "Avatar size max 2MB.");
      return;
    }

    setAvatarLoading(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const uploadRes = await uploadToSupabaseStorage("avatars", file);
      const publicUrl = uploadRes.publicUrl;
      setAvatarUrl(publicUrl);

      // Save avatar_url to Supabase user row
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      const cleanPhone = (currentUser?.phoneNumber || "").replace(/[^0-9]/g, "");
      const formattedPhone = cleanPhone.startsWith("880")
        ? "+" + cleanPhone
        : cleanPhone.startsWith("01")
        ? "+88" + cleanPhone
        : "+880" + cleanPhone;

      await fetch(`${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})`, {
        method: "PATCH",
        headers: {
          apikey: sbKey,
          Authorization: `Bearer ${sbKey}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          avatar_url: publicUrl,
          updated_at: new Date().toISOString(),
        }),
      });

      if (currentUser) {
        login({
          ...currentUser,
          avatarUrl: publicUrl,
        });
      }

      setSuccessMsg(
        isBn
          ? "প্রোফাইল ছবি সুপাবেস স্টোরেজ বাকেটের 'avatars' ফোল্ডারে সফলভাবে সংরক্ষিত হয়েছে!"
          : "Avatar stored successfully into Supabase Storage 'avatars' folder!"
      );
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to upload avatar");
    } finally {
      setAvatarLoading(false);
    }
  };

  // Remove avatar
  const handleRemoveAvatar = async () => {
    setAvatarLoading(true);
    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      const cleanPhone = (currentUser?.phoneNumber || "").replace(/[^0-9]/g, "");
      const formattedPhone = cleanPhone.startsWith("880")
        ? "+" + cleanPhone
        : cleanPhone.startsWith("01")
        ? "+88" + cleanPhone
        : "+880" + cleanPhone;

      await fetch(`${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})`, {
        method: "PATCH",
        headers: {
          apikey: sbKey,
          Authorization: `Bearer ${sbKey}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          avatar_url: null,
          updated_at: new Date().toISOString(),
        }),
      });

      setAvatarUrl("");
      if (currentUser) {
        login({ ...currentUser, avatarUrl: undefined });
      }
      setSuccessMsg(isBn ? "প্রোফাইল ছবি সফলভাবে মুছে ফেলা হয়েছে।" : "Avatar removed.");
    } finally {
      setAvatarLoading(false);
    }
  };

  // Password / PIN Update
  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (newPassword.length < 6) {
      setErrorMsg(
        isBn
          ? "নতুন পাসওয়ার্ড বা পিন কমপক্ষে ৬ সংখ্যার হতে হবে।"
          : "Password must be at least 6 characters."
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg(
        isBn ? "উভয় পাসওয়ার্ড একই হতে হবে।" : "Passwords do not match."
      );
      return;
    }

    setPasswordLoading(true);

    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      // Hash password with bcryptjs
      const salt = bcrypt.genSaltSync(12);
      const passwordHash = bcrypt.hashSync(newPassword, salt);

      const cleanPhone = (currentUser?.phoneNumber || "").replace(/[^0-9]/g, "");
      const formattedPhone = cleanPhone.startsWith("880")
        ? "+" + cleanPhone
        : cleanPhone.startsWith("01")
        ? "+88" + cleanPhone
        : "+880" + cleanPhone;

      const resp = await fetch(
        `${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})`,
        {
          method: "PATCH",
          headers: {
            apikey: sbKey,
            Authorization: `Bearer ${sbKey}`,
            "Content-Type": "application/json",
            Prefer: "return=minimal",
          },
          body: JSON.stringify({
            password_hash: passwordHash,
            updated_at: new Date().toISOString(),
          }),
        }
      );

      if (resp.ok) {
        setSuccessMsg(
          isBn
            ? "পাসওয়ার্ড সফলভাবে পরিবর্তন ও সুপাবেস ডাটাবেজে হ্যাশ আকারে সংরক্ষিত হয়েছে!"
            : "Password updated successfully in Supabase with secure bcrypt hash!"
        );
        setNewPassword("");
        setConfirmPassword("");
      } else {
        throw new Error("Failed to update password");
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Password update error");
    } finally {
      setPasswordLoading(false);
    }
  };

  // Full Profile Update (Name & Geography)
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg("");
    setErrorMsg("");

    const selectedDivObj = GEO_DIVISIONS.find((d) => d.id === divisionId);
    const selectedDistObj = currentDistricts.find((d) => d.id === districtId);
    const selectedUpzObj = currentUpazilas.find((u) => u.id === upazilaId);

    try {
      const sbUrl = "https://damfsrzakxxccalogghh.supabase.co/rest/v1";
      const sbKey =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";

      const cleanPhone = (currentUser?.phoneNumber || "").replace(/[^0-9]/g, "");
      const formattedPhone = cleanPhone.startsWith("880")
        ? "+" + cleanPhone
        : cleanPhone.startsWith("01")
        ? "+88" + cleanPhone
        : "+880" + cleanPhone;

      await fetch(`${sbUrl}/users?or=(phone_number.eq.${cleanPhone},phone_number.eq.${formattedPhone})`, {
        method: "PATCH",
        headers: {
          apikey: sbKey,
          Authorization: `Bearer ${sbKey}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          full_name: fullName,
          division_id: divisionId || null,
          district_id: districtId || null,
          upazila_id: upazilaId || null,
          union_id: unionId || null,
          updated_at: new Date().toISOString(),
        }),
      });

      if (currentUser) {
        login({
          ...currentUser,
          fullName,
          division: selectedDivObj?.nameBn,
          district: selectedDistObj?.nameBn,
          upazila: selectedUpzObj?.nameBn,
        });
      }
      setSuccessMsg(
        isBn
          ? "আপনার নাম, বিভাগ, জেলা, উপজেলা এবং ইউনিয়ন তথ্য সুপাবেস ডাটাবেজে সফলভাবে আপডেট হয়েছে!"
          : "Profile details (Name, Division, District, Upazila, Union) updated successfully in Supabase!"
      );
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const selectedDivObj = GEO_DIVISIONS.find((d) => d.id === divisionId);
  const selectedDistObj = currentDistricts.find((d) => d.id === districtId);
  const selectedUpzObj = currentUpazilas.find((u) => u.id === upazilaId);
  const selectedUnionObj = currentUnions.find((un) => un.id === unionId);

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background via-emerald-50/20 to-background dark:via-emerald-950/10">
      <Navbar />
      <AuthModal />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl space-y-6">
        {/* Header */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white shadow-xl border border-emerald-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
              <Database className="h-3.5 w-3.5 text-emerald-400" />
              <span>{isBn ? "সুপাবেস লাইভ ব্যাকএন্ড প্রোফাইল" : "Supabase Live Profile"}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">
              {isBn ? "আমার প্রোফাইল ও নিরাপত্তা ব্যবস্থাপনা" : "My Profile & Account Security"}
            </h1>
            <p className="text-xs text-slate-300 max-w-xl">
              {isBn
                ? "আপনার ব্যক্তিগত তথ্য, ছবি, বিভাগ-জেলা-উপজেলা-ইউনিয়ন এলাকা এবং অ্যাকাউন্ট পাসওয়ার্ড পরিচালনা করুন।"
                : "Manage account identity, avatar storage, geographic assignment, and security credentials."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge className="bg-emerald-500 text-black font-bold text-xs py-1 px-3">
              ● Active {currentUser?.role?.toUpperCase()}
            </Badge>
          </div>
        </div>

        {/* Notifications */}
        {successMsg && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-300 animate-in fade-in">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-2 text-xs font-semibold text-red-600 animate-in fade-in">
            <Lock className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User ID & Avatar Card */}
          <Card className="border-border shadow-sm">
            <CardContent className="p-6 text-center space-y-4">
              <div className="relative mx-auto w-24 h-24">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt={fullName}
                    className="w-24 h-24 rounded-full object-cover border-4 border-emerald-500/30 shadow-md mx-auto"
                  />
                ) : (
                  <div className="w-24 h-24 mx-auto rounded-full bg-emerald-500/10 text-emerald-600 text-3xl font-black flex items-center justify-center border-4 border-emerald-500/30">
                    {(fullName || "U").charAt(0)}
                  </div>
                )}

                {/* Upload Button overlay */}
                <button
                  type="button"
                  onClick={() => avatarInputRef.current?.click()}
                  disabled={avatarLoading}
                  className="absolute bottom-0 right-0 p-2 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg transition-transform hover:scale-105"
                  title="Upload Avatar to Supabase"
                >
                  {avatarLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Camera className="h-4 w-4" />
                  )}
                </button>
              </div>

              <input
                ref={avatarInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleAvatarFileSelected}
              />

              {avatarUrl && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveAvatar}
                  disabled={avatarLoading}
                  className="text-xs text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 h-7"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  {isBn ? "ছবি মুছুন" : "Remove"}
                </Button>
              )}

              <div>
                <h3 className="font-bold text-lg text-foreground">{fullName}</h3>
                <p className="text-xs font-mono text-muted-foreground mt-0.5">
                  {currentUser?.phoneNumber || "017XXXXXXXX"}
                </p>
                <Badge
                  variant="outline"
                  className="mt-2 uppercase text-[10px] font-bold text-emerald-600 border-emerald-500/30"
                >
                  {currentUser?.role || "FARMER"}
                </Badge>
              </div>

              <div className="pt-4 border-t text-left text-xs space-y-2 text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>অবস্থা:</span>
                  <span className="font-semibold text-emerald-600">● সক্রিয় (Active)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>স্টোরেজ ফোল্ডার:</span>
                  <span className="font-mono text-[10px] bg-muted px-1.5 py-0.5 rounded">
                    avatars/
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>ফোন ভেরিফায়েড:</span>
                  <span className="font-semibold text-foreground">হ্যাঁ (Yes)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>বর্তমান এলাকা:</span>
                  <span className="font-medium text-foreground text-right">
                    {selectedUpzObj?.nameBn || "শেরপুর"}, {selectedDistObj?.nameBn || "বগুড়া"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Forms Section */}
          <div className="md:col-span-2 space-y-6">
            {/* Edit Profile Info & Geography */}
            <Card className="border-border shadow-sm">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <User className="h-4 w-4 text-emerald-600" />
                  <span>
                    {isBn
                      ? "ব্যক্তিগত তথ্য ও এলাকা সম্পাদন"
                      : "Edit Personal & Geographic Information"}
                  </span>
                </h2>

                <form onSubmit={handleUpdate} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium mb-1 block text-foreground">
                      {isBn ? "পুরো নাম (Full Name)" : "Full Name"}
                    </label>
                    <Input
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="text-sm h-10"
                      required
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium mb-1 block text-foreground">
                      {isBn ? "রেজিস্টার্ড মোবাইল নম্বর (পরিবর্তনযোগ্য নয়)" : "Phone (Immutable)"}
                    </label>
                    <div className="relative">
                      <Phone className="h-4 w-4 absolute left-3 top-3 text-muted-foreground" />
                      <Input
                        disabled
                        value={currentUser?.phoneNumber || "017XXXXXXXX"}
                        className="pl-9 text-sm font-mono bg-muted"
                      />
                    </div>
                  </div>

                  {/* Geography Cascading Selector */}
                  <div className="space-y-3 pt-2 border-t">
                    <div className="text-xs font-bold flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400">
                      <MapPin className="h-3.5 w-3.5" />
                      <span>
                        {isBn
                          ? "ভৌগোলিক এলাকা (Division -> District -> Upazila -> Union)"
                          : "Geographic Hierarchy"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-medium mb-1 block text-muted-foreground">
                          {isBn ? "বিভাগ" : "Division"}
                        </label>
                        <select
                          value={divisionId}
                          onChange={(e) => handleDivisionChange(e.target.value)}
                          className="w-full text-xs rounded-md border border-input bg-background p-2 text-foreground"
                        >
                          {GEO_DIVISIONS.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.nameBn} ({d.nameEn})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-medium mb-1 block text-muted-foreground">
                          {isBn ? "জেলা" : "District"}
                        </label>
                        <select
                          value={districtId}
                          onChange={(e) => handleDistrictChange(e.target.value)}
                          className="w-full text-xs rounded-md border border-input bg-background p-2 text-foreground"
                        >
                          {currentDistricts.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.nameBn} ({d.nameEn})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-medium mb-1 block text-muted-foreground">
                          {isBn ? "উপজেলা" : "Upazila"}
                        </label>
                        <select
                          value={upazilaId}
                          onChange={(e) => handleUpazilaChange(e.target.value)}
                          className="w-full text-xs rounded-md border border-input bg-background p-2 text-foreground"
                        >
                          {currentUpazilas.map((u) => (
                            <option key={u.id} value={u.id}>
                              {u.nameBn} ({u.nameEn})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-[11px] font-medium mb-1 block text-muted-foreground">
                          {isBn ? "ইউনিয়ন / ওয়ার্ড" : "Union / Ward"}
                        </label>
                        <select
                          value={unionId}
                          onChange={(e) => setUnionId(e.target.value)}
                          className="w-full text-xs rounded-md border border-input bg-background p-2 text-foreground"
                        >
                          {currentUnions.map((un) => (
                            <option key={un.id} value={un.id}>
                              {un.nameBn} ({un.nameEn})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button
                      type="submit"
                      disabled={loading}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold h-10 px-6"
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                      )}
                      <span>{isBn ? "প্রোফাইল আপডেট করুন" : "Save Changes to Supabase"}</span>
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Change Password / PIN Card */}
            <Card className="border-border shadow-sm">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <KeyRound className="h-4 w-4 text-emerald-600" />
                  <span>
                    {isBn ? "পাসওয়ার্ড / পিন পরিবর্তন (Password / PIN)" : "Change Password / PIN"}
                  </span>
                </h2>
                <p className="text-xs text-muted-foreground">
                  {isBn
                    ? "নতুন পাসওয়ার্ডটি সুপাবেস ডাটাবেজে নিরাপদ bcrypt ($2b$12$) অ্যালগরিদমে হ্যাশ হয়ে সংরক্ষিত হবে।"
                    : "The password will be safely hashed into Supabase using bcryptjs."}
                </p>

                <form onSubmit={handlePasswordUpdate} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium mb-1 block text-foreground">
                        {isBn ? "নতুন পাসওয়ার্ড বা পিন" : "New Password / PIN"}
                      </label>
                      <Input
                        type="password"
                        placeholder="কমপক্ষে ৬ ডিজিট বা অক্ষর"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="text-sm h-10"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-xs font-medium mb-1 block text-foreground">
                        {isBn ? "পাসওয়ার্ড নিশ্চিত করুন" : "Confirm Password"}
                      </label>
                      <Input
                        type="password"
                        placeholder="পুনরায় লিখুন"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="text-sm h-10"
                        required
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={passwordLoading}
                    variant="outline"
                    className="border-emerald-600 text-emerald-700 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 font-bold h-10"
                  >
                    {passwordLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <KeyRound className="h-4 w-4 mr-2" />
                    )}
                    <span>{isBn ? "পাসওয়ার্ড আপডেট করুন" : "Update Password in Supabase"}</span>
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
