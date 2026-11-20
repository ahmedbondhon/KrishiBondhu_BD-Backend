"use client";
import type { Advisory, FarmCrop, GeoItem, SupportInfo, Crop, DiagnosisCase, ExpertReply, Farm, Level, Notification, Urgency, User } from "@/types";
import { useApp } from "@/store/app";
import { ADVISORIES, CROPS, ISSUES, SAFE_GENERAL_ADVISORY, STAGES, seedCases, seedFarms, seedNotifications } from "./data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

/* ------------------------------ real HTTP ------------------------------ */

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const ls = (fn: () => void) => { try { if (typeof window !== "undefined") fn(); } catch { /* storage blocked */ } };

let token: string | null = null;
export const setToken = (t: string | null) => {
  token = t;
  ls(() => (t ? localStorage.setItem(ACCESS_KEY, t) : localStorage.removeItem(ACCESS_KEY)));
};
export const getRefreshToken = (): string | null => (typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY));
export const setRefreshToken = (t: string | null) => ls(() => (t ? localStorage.setItem(REFRESH_KEY, t) : localStorage.removeItem(REFRESH_KEY)));
export const clearSession = () => { setToken(null); setRefreshToken(null); ls(() => localStorage.removeItem("verification_token")); };
export const loadToken = () => { if (!token && typeof window !== "undefined") token = localStorage.getItem(ACCESS_KEY); return token; };

export class ApiError extends Error {
  constructor(public code: string, message: string, public message_bn?: string, public status?: number) {
    super(message);
  }
}

const BN_STATUS: Record<number, string> = {
  400: "অনুরোধটি সঠিক নয়। তথ্য দেখে আবার চেষ্টা করুন।",
  401: "লগইনের মেয়াদ শেষ বা তথ্য সঠিক নয়।",
  403: "এই কাজের অনুমতি নেই, অথবা আপনার একাউন্ট এখনও অনুমোদিত হয়নি।",
  404: "তথ্য খুঁজে পাওয়া যায়নি।",
  409: "এই মোবাইল নম্বর বা ইমেইল আগে থেকেই ব্যবহৃত হয়েছে।",
  422: "দেওয়া তথ্যে ভুল আছে। ঘরগুলো আবার দেখুন।",
  429: "অনেকবার চেষ্টা করা হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।",
  500: "সার্ভারে সমস্যা হয়েছে। একটু পরে আবার চেষ্টা করুন।",
};

/** Backend returns FastAPI errors ({detail: string | [{msg}]}) as well as the {success,data} envelope. */
function toError(status: number, body: any): ApiError {
  let msg = "Request failed";
  let bn: string | undefined;
  const d = body?.detail;
  if (typeof d === "string") msg = d;
  else if (Array.isArray(d)) msg = d.map((x: any) => x?.msg).filter(Boolean).join("; ") || msg;
  else if (d && typeof d === "object") { msg = d.message ?? d.message_bn ?? msg; bn = d.message_bn; }
  if (typeof body?.message === "string" && msg === "Request failed") msg = body.message;
  const det = body?.error?.details;
  if (Array.isArray(det)) bn = bn ?? det.find((x: any) => x?.message_bn)?.message_bn;
  bn = bn ?? body?.error?.message_bn ?? BN_STATUS[status] ?? "কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।";
  return new ApiError(body?.error?.code ?? d?.code ?? `HTTP_${status}`, msg, bn, status);
}

let refreshing: Promise<boolean> | null = null;
async function tryRefresh(): Promise<boolean> {
  const rt = getRefreshToken();
  if (!rt) return false;
  refreshing ??= (async () => {
    try {
      const res = await fetch(`${BASE}/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ refresh_token: rt }) });
      if (!res.ok) return false;
      const raw = await res.json();
      const d = raw?.data ?? raw; // /auth/refresh wraps tokens in {success, data}
      if (!d?.access_token) return false;
      setToken(d.access_token);
      if (d.refresh_token) setRefreshToken(d.refresh_token); // refresh tokens rotate
      return true;
    } catch { return false; } finally { setTimeout(() => (refreshing = null), 0); }
  })();
  return refreshing;
}

async function http<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", ...(init.headers as Record<string, string>) };
  if (!(init.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const t = loadToken();
  if (t) headers.Authorization = `Bearer ${t}`;
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("NETWORK", `Cannot reach backend at ${BASE}`, `সার্ভারের সাথে যোগাযোগ হচ্ছে না (${BASE})। backend চালু আছে কিনা দেখুন, অথবা .env.local-এ NEXT_PUBLIC_USE_MOCK=true দিয়ে ডেমো চালান।`);
  }
  if (res.status === 401 && retry && t && !path.startsWith("/auth/login") && !path.startsWith("/auth/refresh")) {
    if (await tryRefresh()) return http<T>(path, init, false);
    clearSession();
    if (typeof window !== "undefined") { try { localStorage.removeItem("kb-app"); } catch {} window.location.href = "/login"; }
  }
  if (res.status === 204) return undefined as T;
  const body = (await res.json().catch(() => null)) as any;
  if (!res.ok) throw toError(res.status, body);
  // unwrap the optional {success, data} envelope; auth endpoints return raw bodies
  const keepRaw = body && ("tokens" in body || "access_token" in body);
  return (body && typeof body === "object" && "success" in body && "data" in body && !keepRaw ? body.data : body) as T;
}

/* ------------------------------ mock store ------------------------------ */

interface MockDB { cases: DiagnosisCase[]; notifications: Notification[]; farms: Farm[] }
function db(): MockDB {
  const raw = typeof window !== "undefined" ? localStorage.getItem("kb-mock-db-v2") : null;
  if (raw) return JSON.parse(raw);
  const fresh: MockDB = { cases: seedCases(), notifications: seedNotifications(), farms: seedFarms() };
  save(fresh);
  return fresh;
}
const save = (d: MockDB) => typeof window !== "undefined" && localStorage.setItem("kb-mock-db-v2", JSON.stringify(d));
const wait = (ms = 450) => new Promise((r) => setTimeout(r, ms));
const uid = () => Math.random().toString(36).slice(2, 10);

/* -------------------------------- auth --------------------------------- */

export const DEMO_ACCOUNTS: Record<string, User> = {
  farmer: { id: "u-farmer", name: "আব্দুল করিম", phone: "01712345678", role: "farmer", district: "বগুড়া", upazila: "শিবগঞ্জ" },
  expert: { id: "u-expert", name: "ড. রহমান", phone: "01812345678", role: "expert", district: "বগুড়া" },
  admin: { id: "u-admin", name: "প্ল্যাটফর্ম অ্যাডমিন", phone: "01912345678", role: "admin" },
};

export type OtpPurpose = "registration" | "login" | "reset_password";

/** Backend user ({full_name, phone_number, dashboard_path…}) → UI user. */
interface ApiUser { id: string; full_name: string; phone_number: string; email?: string | null; role: User["role"] | { code: User["role"] }; status?: string; preferred_language?: "bn" | "en"; dashboard_path?: string; district_id?: string }
const toUser = (u: ApiUser): User => ({ id: u.id, name: u.full_name, phone: u.phone_number, role: (typeof u.role === "object" ? u.role.code : u.role) as User["role"], email: u.email, status: u.status, preferred_language: u.preferred_language, dashboard_path: u.dashboard_path });
interface TokenBundle { access_token: string; refresh_token: string; user: ApiUser; dashboard_path?: string }

function saveSession(d: { access_token: string; refresh_token?: string }) {
  setToken(d.access_token);
  if (d.refresh_token) setRefreshToken(d.refresh_token);
}

export async function login(identifier: string, password: string, roleHint?: string, remember = false): Promise<User> {
  if (USE_MOCK) {
    await wait();
    if (password.length < 4) throw new ApiError("INVALID", "Invalid credentials", "ফোন নম্বর বা পাসওয়ার্ড সঠিক নয়।");
    const u = DEMO_ACCOUNTS[roleHint ?? "farmer"] ?? DEMO_ACCOUNTS.farmer;
    return { ...u, phone: identifier || u.phone };
  }
  const body = identifier.includes("@") ? { email: identifier, password, remember_me: remember } : { phone_number: identifier, password, remember_me: remember };
  const d = await http<TokenBundle>("/auth/login", { method: "POST", body: JSON.stringify(body) });
  saveSession(d);
  if (!d.user) return me();
  return { ...toUser(d.user), dashboard_path: d.dashboard_path ?? d.user.dashboard_path };
}

export async function loginWithOtp(phone: string, otp: string, remember = false): Promise<User> {
  if (USE_MOCK) { await wait(); return { ...DEMO_ACCOUNTS.farmer, phone }; }
  const d = await http<TokenBundle>("/auth/login/otp-verify", { method: "POST", body: JSON.stringify({ phone_number: phone, otp_code: otp, remember_me: remember }) });
  saveSession(d);
  return { ...toUser(d.user), dashboard_path: d.dashboard_path ?? d.user.dashboard_path };
}

export interface OtpSent { resend_after: number; expires_in_seconds: number; demo_mode?: boolean }
export async function requestOtp(phone: string, purpose: OtpPurpose = "registration"): Promise<OtpSent> {
  if (USE_MOCK) { await wait(500); return { resend_after: 60, expires_in_seconds: 300, demo_mode: true }; }
  if (purpose === "login") {
    const d = await http<Partial<OtpSent>>("/auth/login/otp-request", { method: "POST", body: JSON.stringify({ phone_number: phone }) });
    return { resend_after: d.resend_after ?? 60, expires_in_seconds: d.expires_in_seconds ?? 300, demo_mode: d.demo_mode };
  }
  if (purpose === "reset_password") {
    const d = await http<Partial<OtpSent>>("/auth/password/forgot", { method: "POST", body: JSON.stringify({ phone_number: phone }) });
    return { resend_after: d.resend_after ?? 60, expires_in_seconds: d.expires_in_seconds ?? 300, demo_mode: d.demo_mode };
  }
  const d = await http<Partial<OtpSent>>("/auth/otp/send", { method: "POST", body: JSON.stringify({ phone_number: phone, purpose }) });
  return { resend_after: d.resend_after ?? 60, expires_in_seconds: d.expires_in_seconds ?? 300, demo_mode: d.demo_mode };
}

/** Returns the signed verification_token (also kept in localStorage). */
export async function verifyOtp(phone: string, code: string, purpose: OtpPurpose = "registration"): Promise<string | null> {
  if (USE_MOCK) { await wait(400); return code.length === 6 ? "mock-verification-token" : null; }
  const d = await http<{ is_verified: boolean; verification_token?: string }>("/auth/otp/verify", { method: "POST", body: JSON.stringify({ phone_number: phone, otp_code: code, purpose }) });
  if (!d.is_verified || !d.verification_token) return null;
  ls(() => localStorage.setItem("verification_token", d.verification_token!));
  return d.verification_token;
}

export interface RegisterInput {
  name: string; phone: string; password: string; role: "farmer" | "agent" | "expert";
  email?: string; verification_token: string; language: "bn" | "en"; communication: "sms" | "call" | "in_app";
  division_id?: string; district_id?: string; upazila_id?: string; union_id?: string; village?: string;
  terms_accepted: boolean; privacy_accepted: boolean; location_permission_granted: boolean;
  specialization?: string; credentials?: string;
}
export interface RegisterResult { user: User | null; pending: boolean; message?: string }

export async function register(i: RegisterInput): Promise<RegisterResult> {
  if (USE_MOCK) {
    await wait();
    if (i.role === "expert") return { user: null, pending: true, message: "বিশেষজ্ঞ রেজিস্ট্রেশন জমা হয়েছে। অ্যাডমিন অনুমোদনের পর অ্যাকাউন্ট সক্রিয় হবে।" };
    return { user: { id: uid(), name: i.name, phone: i.phone, role: i.role }, pending: false };
  }
  const common: Record<string, unknown> = {
    phone_number: i.phone, verification_token: i.verification_token, password: i.password, full_name: i.name, email: i.email || undefined,
    preferred_language: i.language, preferred_communication: i.communication,
    terms_accepted: i.terms_accepted, privacy_accepted: i.privacy_accepted, location_permission_granted: i.location_permission_granted,
  };
  if (i.role === "expert") {
    const d = await http<{ message?: string }>("/auth/register/expert", { method: "POST", body: JSON.stringify({ ...common, specialization: i.specialization, credentials: i.credentials }) });
    return { user: null, pending: true, message: d?.message };
  }
  const d = await http<{ user: ApiUser; tokens: { access_token: string; refresh_token: string }; dashboard_path?: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ ...common, role: i.role, division_id: i.division_id, district_id: i.district_id, upazila_id: i.upazila_id, union_id: i.union_id, village: i.village || undefined }),
  });
  saveSession(d.tokens);
  return { user: { ...toUser(d.user), dashboard_path: d.dashboard_path ?? d.user.dashboard_path }, pending: false };
}

export async function forgotPassword(phone: string): Promise<OtpSent> { return requestOtp(phone, "reset_password"); }

export async function resetPassword(phone: string, otp: string, newPassword: string): Promise<void> {
  if (USE_MOCK) { await wait(); return; }
  await http("/auth/password/reset", { method: "POST", body: JSON.stringify({ phone_number: phone, otp_code: otp, new_password: newPassword }) });
}

export async function me(): Promise<User> {
  if (USE_MOCK) return DEMO_ACCOUNTS.farmer;
  const u = await http<ApiUser>("/auth/me");
  return toUser(u);
}

export async function logout(all = false): Promise<void> {
  const rt = getRefreshToken();
  try {
    if (!USE_MOCK) await http(all ? "/auth/logout-all" : "/auth/logout", { method: "POST", body: all ? undefined : JSON.stringify({ refresh_token: rt }) }, false);
  } catch { /* local sign-out must always succeed */ }
  clearSession();
}

export async function updateLanguage(lang: "bn" | "en"): Promise<void> {
  if (USE_MOCK || !loadToken()) return;
  await http("/auth/language", { method: "PATCH", body: JSON.stringify({ preferred_language: lang }) }).catch(() => {});
}

export async function getSupport(): Promise<SupportInfo> {
  const fallback: SupportInfo = { helpline_number: "16123", support_phone: "+8809612345678", support_email: "support@krishibondhu.gov.bd", available_hours_bn: "সকাল ৯:০০ - সন্ধ্যা ৬:০০ (শনিবার থেকে বৃহস্পতিবার)", available_hours_en: "9:00 AM - 6:00 PM (Saturday to Thursday)", title_bn: "কৃষিবন্ধু সহায়তা ও কল সেন্টার", title_en: "KrishiBondhu Support & Call Center", instructions_bn: "যেকোনো কারিগরি বা কৃষি পরামর্শের জন্য সরাসরি কল সেন্টারে যোগাযোগ করুন।", instructions_en: "For any technical or agricultural advisory, contact our call center directly." };
  if (USE_MOCK) return fallback;
  return http<SupportInfo>("/auth/support").catch(() => fallback);
}

/* --------------------------------- geo ---------------------------------- */

const MOCK_GEO: Record<string, GeoItem[]> = {
  divisions: [{ id: "d1", bbs_code: "10", name_en: "Rajshahi", name_bn: "রাজশাহী" }, { id: "d2", bbs_code: "30", name_en: "Dhaka", name_bn: "ঢাকা" }, { id: "d3", bbs_code: "55", name_en: "Rangpur", name_bn: "রংপুর" }],
  districts: [{ id: "dt1", bbs_code: "1", name_en: "Bogura", name_bn: "বগুড়া" }, { id: "dt2", bbs_code: "2", name_en: "Rangpur", name_bn: "রংপুর" }],
  upazilas: [{ id: "up1", bbs_code: "1", name_en: "Shibganj", name_bn: "শিবগঞ্জ" }, { id: "up2", bbs_code: "2", name_en: "Sherpur", name_bn: "শেরপুর" }],
  unions: [{ id: "un1", bbs_code: "1", name_en: "Maidanhatta", name_bn: "মাইদানহাটা" }, { id: "un2", bbs_code: "2", name_en: "Atmul", name_bn: "আটমূল" }],
};
type GeoLevel = "divisions" | "districts" | "upazilas" | "unions";
export async function listGeo(level: GeoLevel, parentId?: string): Promise<GeoItem[]> {
  if (USE_MOCK) { await wait(250); return MOCK_GEO[level]; }
  const q = level === "divisions" ? "" : `?${{ districts: "division_id", upazilas: "district_id", unions: "upazila_id" }[level]}=${encodeURIComponent(parentId ?? "")}`;
  return http<GeoItem[]>(`/geo/${level}${q}`);
}

/* ------------------------------- catalog -------------------------------- */

const EMOJI: Record<string, string> = { potato: "🥔", tomato: "🍅", chili: "🌶️" };
export async function listCrops(): Promise<Crop[]> {
  if (USE_MOCK) return CROPS;
  const rows = await http<{ id: string; code: string; name_bn: string; name_en: string }[]>("/catalog/crops");
  return rows.map((c) => ({ id: c.id, code: c.code as Crop["code"], name_bn: c.name_bn, name_en: c.name_en, emoji: EMOJI[c.code] ?? "🌱" }));
}

/* ---- backend → UI adapters (real mode) ---- */
const lines = (t?: string | null) => (t ?? "").split(/\n+|(?<=।)\s+/).map((x) => x.replace(/^[-•\d.\s]+/, "").trim()).filter(Boolean);
const toStatus = (st: string): DiagnosisCase["status"] => {
  const v = (st ?? "").toLowerCase();
  if (v.includes("escalat") || v.includes("pending") || v.includes("needs")) return "needs_expert_review";
  if (v.includes("under")) return "under_review";
  if (v.includes("respon") || v.includes("expert_review") || v.includes("reviewed")) return "response_received";
  if (v.includes("clos") || v.includes("resolved")) return "closed";
  if (v.includes("draft") || v.includes("created")) return "draft";
  return "diagnosed";
};
const toUrgency = (u?: string | null): Urgency => (u === "critical" ? "high" : u === "low" || u === "medium" || u === "high" ? u : "unknown");

async function viewUrl(fileId?: string): Promise<string> {
  if (!fileId) return "";
  try { const r = await http<{ view_url: string }>(`/files/${fileId}/view-url`); return r.view_url; } catch { return ""; }
}

/* eslint-disable @typescript-eslint/no-explicit-any */
async function mapCase(d: any, crops: Crop[], farmer = ""): Promise<DiagnosisCase> {
  const crop = crops.find((c) => c.id === d.crop_id) ?? { id: d.crop_id ?? "", code: "potato" as const, name_bn: "ফসল", name_en: "Crop", emoji: "🌱" };
  const primary = (d.images ?? [])[0];
  const adv = d.advisory;
  const lvl: Level = d.confidence_level === "high" || d.confidence_level === "medium" ? d.confidence_level : "low";
  const unsure = !d.issue_id || lvl === "low";
  const rev = (d.expert_reviews ?? [])[d.expert_reviews?.length - 1];
  return {
    id: d.case_id ?? d.id, case_number: d.case_number, farmer_name: farmer, crop, growth_stage: "", symptom_bn: d.farmer_notes ?? "",
    affected_percent: 0, district: "", image_url: await viewUrl(primary?.file_id), status: toStatus(d.status ?? d.case_status), created_at: d.created_at ?? new Date().toISOString(),
    diagnosis: {
      issue: d.issue_id ? { id: d.issue_id, code: d.issue_id, crop_code: crop.code, name_bn: d.issue_name_bn ?? "", name_en: d.issue_name_en ?? "", symptoms_bn: "", severity: "medium" } : null,
      confidence_score: d.confidence_score ?? 0, confidence_level: lvl, urgency: unsure && !d.issue_id ? "unknown" : toUrgency(d.urgency_level),
      requires_expert_review: !!d.requires_expert_review, model_version: "",
      candidates: (d.top_predictions ?? []).map((p: any) => ({ name_bn: p.class_label, probability: p.confidence_score })),
    },
    advisory: adv ? {
      title_bn: adv.title_bn, immediate_actions_bn: lines(adv.detailed_treatment_bn), prohibited_actions_bn: [], prevention_bn: lines(adv.preventive_measures_bn),
      safety_warning_bn: "কীটনাশক ব্যবহারের আগে লেবেল পড়ুন এবং হাত-মুখ ঢেকে স্প্রে করুন।", audio_text_bn: [adv.summary_bn, adv.detailed_treatment_bn].filter(Boolean).join(" "),
      reviewed_by: adv.source === "ai_generated" ? "এআই পরামর্শ" : "বিশেষজ্ঞ যাচাইকৃত", reviewed_at: d.created_at ?? "",
    } : null,
    expert_reply: rev ? { expert_name: rev.expert_name ?? "বিশেষজ্ঞ", decision: rev.agreed_with_ai ? "approved_ai" : "corrected_ai", response_bn: [rev.diagnosis_notes_bn, rev.prescribed_treatment_bn].filter(Boolean).join("\n"), urgency: toUrgency(d.urgency_level), created_at: rev.reviewed_at ?? "" } : undefined,
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

/* ------------------------------ diagnosis ------------------------------- */

export interface NewCaseInput {
  crop: Crop;
  growth_stage: string;
  symptom_bn: string;
  affected_percent: number;
  image_data_url: string;
  image_blob?: Blob;
  quality: "acceptable" | "blurry" | "dark" | "bright";
  farmer_name: string;
  district: string;
}

const levelOf = (s: number): Level => (s >= 0.8 ? "high" : s >= 0.55 ? "medium" : "low");

export async function createDiagnosis(input: NewCaseInput, onStage?: (s: "uploading" | "analyzing") => void): Promise<DiagnosisCase> {
  if (USE_MOCK) {
    onStage?.("uploading");
    await wait(900);
    onStage?.("analyzing");
    await wait(1500);
    const pool = ISSUES.filter((i) => i.crop_code === input.crop.code);
    const picked = pool[Math.floor(Math.random() * pool.length)];
    let score = 0.45 + Math.random() * 0.5;
    if (input.quality !== "acceptable") score -= 0.2;
    score = Math.max(0.2, Math.min(0.96, score));
    const level = levelOf(score);
    const urgency: Urgency = input.affected_percent >= 40 || picked.severity === "critical" ? "high" : picked.severity === "high" ? "high" : "medium";
    const unsure = level === "low";
    const rest = 1 - score;
    const other = pool.find((p) => p.id !== picked.id);
    const c: DiagnosisCase = {
      id: uid(), case_number: `KB-2026-${String(135 + db().cases.length).padStart(6, "0")}`,
      farmer_name: input.farmer_name, crop: input.crop, growth_stage: input.growth_stage, symptom_bn: input.symptom_bn,
      affected_percent: input.affected_percent, district: input.district, image_url: input.image_data_url,
      status: unsure ? "needs_expert_review" : "diagnosed", created_at: new Date().toISOString(),
      diagnosis: {
        issue: unsure ? null : picked, confidence_score: Number(score.toFixed(2)), confidence_level: level,
        urgency: unsure ? "unknown" : urgency, requires_expert_review: unsure || urgency === "high", model_version: "v1.0.0",
        candidates: [
          { name_bn: picked.name_bn, probability: Number(score.toFixed(2)) },
          { name_bn: other?.name_bn ?? "অন্যান্য", probability: Number((rest * 0.7).toFixed(2)) },
          { name_bn: "অন্যান্য", probability: Number((rest * 0.3).toFixed(2)) },
        ],
      },
      advisory: unsure ? SAFE_GENERAL_ADVISORY : ADVISORIES[picked.code] ?? SAFE_GENERAL_ADVISORY,
    };
    const d = db();
    d.cases.unshift(c);
    save(d);
    return c;
  }
  // 1) One-call quick diagnosis (multipart). If this backend build does not have it, fall back to the 5-step flow below.
  try {
    const qb = input.image_blob ?? (await (await fetch(input.image_data_url)).blob());
    return await quickDiagnosis(input, qb);
  } catch (e) {
    if (!(e instanceof ApiError) || ![404, 405].includes(e.status ?? 0)) throw e;
  }
  // Real flow: signed upload → confirm (gatekeeper runs server-side) → create case → attach image → analyze → fetch result
  const blob = input.image_blob ?? (await (await fetch(input.image_data_url)).blob());
  const mime = (["image/jpeg", "image/png", "image/webp"].includes(blob.type) ? blob.type : "image/jpeg");
  const name = `crop-${Date.now()}.${mime === "image/png" ? "png" : mime === "image/webp" ? "webp" : "jpg"}`;
  onStage?.("uploading");
  const up = await http<{ upload_url: string; storage_path: string }>("/files/upload-url", {
    method: "POST", body: JSON.stringify({ original_name: name, mime_type: mime, file_size_bytes: blob.size, entity_type: "diagnosis_case" }),
  });
  const put = await fetch(up.upload_url, { method: "PUT", body: blob, headers: { "Content-Type": mime } }).catch(() => null);
  if (!put || !put.ok) throw new ApiError("UPLOAD_FAILED", "Image upload failed", "ছবি আপলোড করা যায়নি। ইন্টারনেট দেখে আবার চেষ্টা করুন।");
  const file = await http<{ id?: string; file_id?: string }>("/files/confirm-upload", {
    method: "POST", body: JSON.stringify({ storage_path: up.storage_path, original_name: name, mime_type: mime, file_size_bytes: blob.size, entity_type: "diagnosis_case" }),
  });
  const fileId = file.id ?? file.file_id;
  const notes = [input.symptom_bn, input.growth_stage && `ধাপ: ${input.growth_stage}`, `আক্রান্ত: ${input.affected_percent}%`].filter(Boolean).join(" | ").slice(0, 2000);
  const created = await http<{ case_id: string }>("/diagnosis-cases", { method: "POST", body: JSON.stringify({ crop_id: input.crop.id, farmer_notes: notes }) });
  await http(`/diagnosis-cases/${created.case_id}/images`, { method: "POST", body: JSON.stringify({ file_id: fileId, image_type: "leaf", is_primary: true }) });
  onStage?.("analyzing");
  await http(`/diagnosis-cases/${created.case_id}/analyze`, { method: "POST" });
  const full = await mapCase(await http(`/diagnosis-cases/${created.case_id}`), [input.crop], input.farmer_name);
  full.image_url = full.image_url || input.image_data_url;
  full.growth_stage = input.growth_stage; full.affected_percent = input.affected_percent; full.district = input.district;
  return full;
}

export async function listCases(scope: "mine" | "expert", farmerName?: string): Promise<DiagnosisCase[]> {
  if (USE_MOCK) {
    await wait(250);
    const all = db().cases;
    return scope === "mine" ? all.filter((c) => c.farmer_name === farmerName) : all;
  }
  if (scope === "expert") return http<DiagnosisCase[]>("/expert/cases"); // expert endpoints: not yet adapted
  const [rows, crops] = await Promise.all([http<{ id: string }[]>("/diagnosis-cases?limit=30"), listCrops()]);
  const full = await Promise.all(rows.map((r) => http(`/diagnosis-cases/${r.id}`).then((d) => mapCase(d, crops, farmerName ?? "")).catch(() => null)));
  return full.filter(Boolean) as DiagnosisCase[];
}

export async function getCase(id: string): Promise<DiagnosisCase> {
  if (quickCache.has(id)) return quickCache.get(id)!;
  if (USE_MOCK) {
    await wait(200);
    const c = db().cases.find((x) => x.id === id);
    if (!c) throw new ApiError("NOT_FOUND", "Case not found", "কেসটি খুঁজে পাওয়া যায়নি।");
    return c;
  }
  const [d, crops] = await Promise.all([http(`/diagnosis-cases/${id}`), listCrops()]);
  return mapCase(d, crops, useApp.getState().user?.name ?? "");
}

export async function requestExpert(id: string): Promise<void> {
  if (USE_MOCK) {
    await wait(400);
    const d = db();
    const c = d.cases.find((x) => x.id === id);
    if (c) c.status = "needs_expert_review";
    save(d);
    return;
  }
  await http(`/diagnosis-cases/${id}/request-expert-review`, { method: "POST" });
}

export async function submitFeedback(id: string, fb: NonNullable<DiagnosisCase["feedback"]>): Promise<void> {
  if (USE_MOCK) {
    await wait(350);
    const d = db();
    const c = d.cases.find((x) => x.id === id);
    if (c) c.feedback = fb;
    save(d);
    return;
  }
  await http(`/diagnosis-cases/${id}/feedback`, { method: "POST", body: JSON.stringify({ is_helpful: fb.helpful === "yes", outcome_status: fb.outcome === "better" ? "resolved" : fb.outcome === "same" ? "partially_resolved" : "ineffective", feedback_text: fb.helpful === "need_help" ? "need_help" : undefined }) });
}

export async function expertReview(id: string, reply: Omit<ExpertReply, "created_at">): Promise<void> {
  if (USE_MOCK) {
    await wait(500);
    const d = db();
    const c = d.cases.find((x) => x.id === id);
    if (c) {
      c.expert_reply = { ...reply, created_at: new Date().toISOString() };
      c.status = "response_received";
      d.notifications.unshift({ id: uid(), title_bn: "বিশেষজ্ঞের উত্তর এসেছে", body_bn: `আপনার কেস ${c.case_number}-এ উত্তর দেওয়া হয়েছে।`, read: false, created_at: new Date().toISOString(), case_id: c.id });
    }
    save(d);
    return;
  }
  await http(`/expert/cases/${id}/review`, { method: "POST", body: JSON.stringify(reply) });
}

export async function acceptCase(id: string): Promise<void> {
  if (USE_MOCK) {
    const d = db();
    const c = d.cases.find((x) => x.id === id);
    if (c && c.status === "needs_expert_review") c.status = "under_review";
    save(d);
    return;
  }
  await http(`/expert/cases/${id}/accept`, { method: "POST" });
}

/* ----------------------------- notifications ---------------------------- */

export async function listNotifications(): Promise<Notification[]> {
  if (USE_MOCK) { await wait(150); return db().notifications; }
  const r = await http<{ notifications: { id: string; title_bn: string; body_bn: string; is_read: boolean; created_at: string; entity_type?: string; entity_id?: string }[] }>("/notifications");
  return r.notifications.map((n) => ({ id: n.id, title_bn: n.title_bn, body_bn: n.body_bn, read: n.is_read, created_at: n.created_at, case_id: n.entity_type?.includes("case") ? n.entity_id : undefined }));
}
export async function markAllRead(): Promise<void> {
  if (USE_MOCK) { const d = db(); d.notifications.forEach((n) => (n.read = true)); save(d); return; }
  await http("/notifications/read-all", { method: "POST" });
}


/* ---------------------- quick diagnosis + AI gatekeeper ---------------------- */

const quickCache = new Map<string, DiagnosisCase>(); // quick results that have no stored case id
/* eslint-disable @typescript-eslint/no-explicit-any */
async function quickDiagnosis(input: NewCaseInput, blob: Blob): Promise<DiagnosisCase> {
  const mime = ["image/jpeg", "image/png", "image/webp"].includes(blob.type) ? blob.type : "image/jpeg";
  const fd = new FormData();
  fd.append("image", blob, `crop-${Date.now()}.${mime === "image/png" ? "png" : mime === "image/webp" ? "webp" : "jpg"}`);
  fd.append("crop_id", input.crop.id);
  fd.append("farmer_notes", [input.symptom_bn, input.growth_stage && `ধাপ: ${input.growth_stage}`, `আক্রান্ত: ${input.affected_percent}%`].filter(Boolean).join(" | ").slice(0, 2000));
  const raw: any = await http("/quick-diagnosis", { method: "POST", body: fd });
  const r = raw?.data ?? raw;
  const caseId = r.case_id ?? r.id;
  let c: DiagnosisCase;
  if (caseId) {
    try { c = await mapCase(await http(`/diagnosis-cases/${caseId}`), [input.crop], input.farmer_name); }
    catch { c = await mapCase({ ...r, case_id: caseId }, [input.crop], input.farmer_name); }
  } else {
    const dg = r.diagnosis ?? r;
    const adv = r.advisory ?? r.treatment ?? {};
    let conf = Number(dg.confidence_score ?? dg.confidence ?? 0); if (conf > 1) conf /= 100;
    const name_bn = dg.issue_name_bn ?? dg.disease_name_bn ?? dg.disease_bn ?? dg.name_bn ?? "";
    c = await mapCase({
      case_id: uid(), crop_id: input.crop.id, status: "diagnosed", issue_id: name_bn ? "quick" : null, issue_name_bn: name_bn, issue_name_en: dg.issue_name_en ?? dg.disease_name_en ?? dg.name_en ?? "",
      confidence_score: conf, confidence_level: conf >= 0.8 ? "high" : conf >= 0.5 ? "medium" : "low", urgency_level: dg.urgency_level ?? dg.urgency, requires_expert_review: !!(dg.requires_expert_review ?? conf < 0.5),
      top_predictions: dg.top_predictions ?? [], farmer_notes: input.symptom_bn, created_at: new Date().toISOString(),
      advisory: { title_bn: adv.title_bn ?? name_bn, summary_bn: adv.summary_bn ?? r.summary_bn ?? "", detailed_treatment_bn: adv.detailed_treatment_bn ?? adv.treatment_bn ?? r.treatment_bn ?? r.recommendation_bn ?? (typeof adv === "string" ? adv : ""), preventive_measures_bn: adv.preventive_measures_bn ?? r.prevention_bn ?? "", source: "ai_generated" },
    }, [input.crop], input.farmer_name);
    quickCache.set(c.id, c);
  }
  c.image_url = c.image_url || input.image_data_url;
  c.growth_stage = input.growth_stage; c.affected_percent = input.affected_percent; c.district = input.district;
  return c;
}
/* eslint-enable @typescript-eslint/no-explicit-any */

/** Backend AI gatekeeper: rejects selfies/animals/non-plants and a photo that does not match the chosen crop. Only a definite rejection (422) blocks the user. */
export async function verifyCropImage(dataUrl: string, crop: Crop): Promise<void> {
  if (USE_MOCK) return;
  try {
    await http("/files/verify-crop-image", { method: "POST", body: JSON.stringify({ image_base64: dataUrl, selected_crop: crop.name_en, mime_type: dataUrl.slice(5, dataUrl.indexOf(";")) || "image/jpeg", strict_crop_match: true }) });
  } catch (e) {
    if (e instanceof ApiError && e.status === 422) throw e; // not a crop / wrong crop
    // gatekeeper unavailable (network, AI quota, 5xx): do not block the farmer
  }
}

/* ------------------------- catalog sub-resources ------------------------- */

export interface StageOpt { id: string; code: string; name_bn: string; name_en: string }
export interface VarietyOpt { id: string; code: string; name_bn: string; name_en: string }
export interface IssueOpt { id: string; code: string; name_bn: string; name_en: string; symptoms_bn?: string; issue_type?: string }
const STAGE_FALLBACK: StageOpt[] = STAGES.map((s) => ({ id: s.code, code: s.code, name_bn: s.bn, name_en: s.en }));
const real = (cropId?: string) => !USE_MOCK && !!cropId && /^[0-9a-f-]{36}$/i.test(cropId);

export async function listGrowthStages(cropId?: string): Promise<StageOpt[]> {
  if (!real(cropId)) return STAGE_FALLBACK;
  try {
    const rows = await http<{ id: string; stage_code: string; name_bn: string; name_en: string }[]>(`/catalog/crops/${cropId}/growth-stages`);
    return rows.length ? rows.map((r) => ({ id: r.id, code: r.stage_code, name_bn: r.name_bn, name_en: r.name_en })) : STAGE_FALLBACK;
  } catch { return STAGE_FALLBACK; }
}
export async function listVarieties(cropId?: string): Promise<VarietyOpt[]> {
  if (!real(cropId)) return [];
  try { return await http<VarietyOpt[]>(`/catalog/crops/${cropId}/varieties`); } catch { return []; }
}
export async function listCropIssues(cropId?: string): Promise<IssueOpt[]> {
  if (!real(cropId)) return [];
  try {
    const rows = await http<IssueOpt[]>(`/catalog/crops/${cropId}/issues`);
    return rows;
  } catch { return []; }
}

/* ------------------------- farmer profile + avatar ------------------------ */

export interface FarmerProfile {
  full_name: string; phone_number: string; preferred_language: "bn" | "en"; preferred_communication?: string; avatar_url?: string | null;
  geo: { division_id: string; district_id: string; upazila_id: string; union_id: string };
  names: { division?: string; district?: string; upazila?: string; union?: string };
  stats: { label_bn: string; label_en: string; value: number }[];
}
/* eslint-disable @typescript-eslint/no-explicit-any */
function toProfile(r: any, lang: "bn" | "en"): FarmerProfile {
  const p = r?.profile ?? r?.data ?? r;
  const m = p.meta ?? {};
  const nm = (g: any) => (g ? (lang === "bn" ? g.name_bn : g.name_en) : undefined);
  const st = p.stats ?? p.statistics ?? {};
  const LABELS: Record<string, [string, string]> = { total_plots: ["মোট জমি", "Plots"], plots: ["মোট জমি", "Plots"], total_cases: ["রোগ নির্ণয়", "Diagnoses"], cases: ["রোগ নির্ণয়", "Diagnoses"], total_diagnoses: ["রোগ নির্ণয়", "Diagnoses"], total_farms: ["মোট জমি", "Plots"] };
  return {
    full_name: p.full_name, phone_number: p.phone_number, preferred_language: p.preferred_language === "en" ? "en" : "bn", preferred_communication: p.preferred_communication, avatar_url: p.avatar_url ?? null,
    geo: { division_id: m.division_id ?? "", district_id: m.district_id ?? "", upazila_id: m.upazila_id ?? "", union_id: m.union_id ?? "" },
    names: { division: nm(p.division), district: nm(p.district), upazila: nm(p.upazila), union: nm(p.union) },
    stats: Object.entries(st).filter(([k, v]) => typeof v === "number" && LABELS[k]).map(([k, v]) => ({ label_bn: LABELS[k][0], label_en: LABELS[k][1], value: v as number })),
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

export async function getFarmerProfile(): Promise<FarmerProfile> {
  const u = useApp.getState().user; const lang = useApp.getState().lang;
  if (USE_MOCK) {
    const d = db();
    return { full_name: u?.name ?? "", phone_number: u?.phone ?? "", preferred_language: lang, preferred_communication: "sms", avatar_url: u?.avatar_url ?? null, geo: { division_id: "", district_id: "", upazila_id: "", union_id: "" }, names: { district: u?.district, upazila: u?.upazila }, stats: [{ label_bn: "মোট জমি", label_en: "Plots", value: d.farms.length }, { label_bn: "রোগ নির্ণয়", label_en: "Diagnoses", value: d.cases.length }] };
  }
  return toProfile(await http("/farmer/profile"), lang);
}
export async function updateFarmerProfile(p: { full_name?: string; preferred_language?: "bn" | "en"; division_id?: string; district_id?: string; upazila_id?: string; union_id?: string }): Promise<FarmerProfile> {
  const lang = useApp.getState().lang;
  if (USE_MOCK) { await wait(300); const cur = await getFarmerProfile(); return { ...cur, full_name: p.full_name ?? cur.full_name }; }
  const body: Record<string, unknown> = {};
  Object.entries(p).forEach(([k, v]) => { if (v) body[k] = v; });
  return toProfile(await http("/farmer/profile", { method: "PUT", body: JSON.stringify(body) }), lang);
}
export async function updateContactPrefs(p: { preferred_communication?: string; preferred_language?: "bn" | "en" }): Promise<void> {
  if (USE_MOCK) return;
  await http("/auth/me/profile", { method: "POST", body: JSON.stringify(p) });
}
export async function uploadAvatar(file: File): Promise<string | null> {
  if (USE_MOCK) {
    return new Promise((res) => { const r = new FileReader(); r.onload = () => res(String(r.result)); r.readAsDataURL(file); });
  }
  const fd = new FormData(); fd.append("file", file);
  const r = await http<any>("/farmer/profile/avatar", { method: "POST", body: fd }); // eslint-disable-line @typescript-eslint/no-explicit-any
  return (r?.profile ?? r?.data ?? r)?.avatar_url ?? r?.avatar_url ?? null;
}
export async function deleteAvatar(): Promise<void> {
  if (USE_MOCK) return;
  await http("/farmer/profile/avatar", { method: "DELETE" });
}

/* --------------------------------- farms -------------------------------- */

const SQM_PER_DECIMAL = 40.4686; // 1 decimal (শতাংশ) in square metres
export interface FarmInput { name: string; size_decimal: number; soil_type?: string; irrigation_source?: string; location?: string }
export interface CycleInput { crop: Crop; stage: string; stage_id?: string; planted_at: string; variety?: string; variety_id?: string; expected_harvest?: string }
/* eslint-disable @typescript-eslint/no-explicit-any */
async function toFarm(p: any, crops: Crop[]): Promise<Farm> {
  const cycles: any[] = await http<any[]>(`/farms/${p.id}/crop-cycles`).catch(() => []);
  const stageCache = new Map<string, StageOpt[]>();
  const out: FarmCrop[] = [];
  for (const cy of cycles) {
    const crop = crops.find((c) => c.id === cy.crop_id) ?? { id: cy.crop_id, code: "potato" as const, name_bn: "ফসল", name_en: "Crop", emoji: "🌱" };
    if (!stageCache.has(cy.crop_id)) stageCache.set(cy.crop_id, await listGrowthStages(cy.crop_id));
    const st = stageCache.get(cy.crop_id)!.find((x) => x.id === cy.current_stage_id);
    out.push({ cycle_id: cy.id, crop, stage: st?.name_bn ?? "", stage_id: cy.current_stage_id ?? undefined, planted_at: cy.sowing_date ?? cy.created_at ?? "", status: cy.status, yield_kg: cy.yield_kg != null ? Number(cy.yield_kg) : undefined, expected_harvest: cy.expected_harvest_date ?? undefined, actual_harvest: cy.actual_harvest_date ?? undefined });
  }
  const sqm = p.area_sqm != null ? Number(p.area_sqm) : p.area_bigha != null ? Number(p.area_bigha) * 1337.8 : 0;
  return { id: p.id, name: p.name, size_decimal: Math.round(sqm / SQM_PER_DECIMAL), location: [p.soil_type, p.irrigation_source].filter(Boolean).join(" · "), soil_type: p.soil_type ?? undefined, irrigation_source: p.irrigation_source ?? undefined, crops: out };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

export async function listFarms(): Promise<Farm[]> {
  if (USE_MOCK) { await wait(200); return db().farms; }
  const [plots, crops] = await Promise.all([http<any[]>("/farms"), listCrops()]); // eslint-disable-line @typescript-eslint/no-explicit-any
  return Promise.all((Array.isArray(plots) ? plots : []).map((p) => toFarm(p, crops)));
}
export async function addFarm(f: FarmInput): Promise<Farm> {
  if (USE_MOCK) {
    await wait(300);
    const d = db();
    const farm: Farm = { id: uid(), crops: [], name: f.name, size_decimal: f.size_decimal, location: f.location ?? [f.soil_type, f.irrigation_source].filter(Boolean).join(" · "), soil_type: f.soil_type, irrigation_source: f.irrigation_source };
    d.farms.push(farm);
    save(d);
    return farm;
  }
  const p = await http("/farms", { method: "POST", body: JSON.stringify({ name: f.name, area_sqm: Math.round(f.size_decimal * SQM_PER_DECIMAL), soil_type: f.soil_type || undefined, irrigation_source: f.irrigation_source || undefined }) });
  return toFarm(p, await listCrops());
}
export async function updateFarm(id: string, f: Partial<FarmInput>): Promise<void> {
  if (USE_MOCK) { const d = db(); const x = d.farms.find((v) => v.id === id); if (x) { Object.assign(x, { name: f.name ?? x.name, size_decimal: f.size_decimal ?? x.size_decimal, soil_type: f.soil_type ?? x.soil_type, irrigation_source: f.irrigation_source ?? x.irrigation_source }); save(d); } return; }
  await http(`/farms/${id}`, { method: "PATCH", body: JSON.stringify({ name: f.name, area_sqm: f.size_decimal ? Math.round(f.size_decimal * SQM_PER_DECIMAL) : undefined, soil_type: f.soil_type, irrigation_source: f.irrigation_source }) });
}
export async function deleteFarm(id: string): Promise<void> {
  if (USE_MOCK) { const d = db(); d.farms = d.farms.filter((v) => v.id !== id); save(d); return; }
  await http(`/farms/${id}`, { method: "DELETE" });
}
export async function addCropCycle(farmId: string, c: CycleInput): Promise<void> {
  if (USE_MOCK) {
    const d = db();
    d.farms.find((f) => f.id === farmId)?.crops.push({ cycle_id: uid(), crop: c.crop, stage: c.stage, planted_at: c.planted_at, variety: c.variety, status: "active", expected_harvest: c.expected_harvest });
    save(d);
    return;
  }
  await http(`/farms/${farmId}/crop-cycles`, { method: "POST", body: JSON.stringify({ crop_id: c.crop.id, variety_id: c.variety_id || undefined, current_stage_id: c.stage_id || undefined, sowing_date: c.planted_at || undefined, expected_harvest_date: c.expected_harvest || undefined }) });
}
/** Move a cycle to another growth stage, or finish it (harvested / failed) with the yield in kg. */
export async function updateCropCycle(farmId: string, cycleId: string, p: { stage_id?: string; stage?: string; status?: "active" | "harvested" | "failed"; yield_kg?: number; actual_harvest?: string }): Promise<void> {
  if (USE_MOCK) {
    const d = db(); const cy = d.farms.find((f) => f.id === farmId)?.crops.find((x) => x.cycle_id === cycleId);
    if (cy) { if (p.stage) cy.stage = p.stage; if (p.status) cy.status = p.status; if (p.yield_kg != null) cy.yield_kg = p.yield_kg; if (p.actual_harvest) cy.actual_harvest = p.actual_harvest; save(d); }
    return;
  }
  await http(`/farms/${farmId}/crop-cycles/${cycleId}`, { method: "PATCH", body: JSON.stringify({ current_stage_id: p.stage_id, status: p.status, yield_kg: p.yield_kg, actual_harvest_date: p.actual_harvest }) });
}

/* --------------------------------- admin -------------------------------- */

export type ArticleStatus = "approved" | "pending_review" | "draft";
export interface AdminArticle { id: string; issue: string; crop: string; status: ArticleStatus; reviewer: string; updated: string; advisory: Advisory }

export async function listArticles(): Promise<AdminArticle[]> {
  await wait(200);
  return ISSUES.map((i, idx) => ({
    id: i.id, issue: i.name_bn, crop: CROPS.find((c) => c.code === i.crop_code)!.name_bn,
    status: (idx === 3 ? "pending_review" : idx === 4 ? "draft" : "approved") as ArticleStatus,
    reviewer: idx >= 3 ? "—" : "ড. রহমান", updated: ADVISORIES[i.code].reviewed_at, advisory: ADVISORIES[i.code],
  }));
}

export const DEMO_USERS = [
  { name: "আব্দুল করিম", phone: "01712345678", role: "farmer" as Role2, status: "active" },
  { name: "রহিমা বেগম", phone: "01611111111", role: "farmer" as Role2, status: "active" },
  { name: "সালমা খাতুন", phone: "01511111111", role: "farmer" as Role2, status: "active" },
  { name: "ড. রহমান", phone: "01812345678", role: "expert" as Role2, status: "verified" },
  { name: "মিজানুর রহমান", phone: "01911111111", role: "agent" as Role2, status: "active" },
  { name: "নুসরাত জাহান", phone: "01311111111", role: "expert" as Role2, status: "pending" },
];
type Role2 = "farmer" | "agent" | "expert";
