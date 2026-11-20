import clsx, { ClassValue } from "clsx";

export const cn = (...v: ClassValue[]) => clsx(v);

const BN_DIGITS = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"];
export const toBn = (n: number | string) => String(n).replace(/\d/g, (d) => BN_DIGITS[Number(d)]);

export function fmtDate(iso: string, lang: "bn" | "en" = "bn") {
  const d = new Date(iso);
  const s = d.toLocaleDateString(lang === "bn" ? "bn-BD" : "en-GB", { day: "numeric", month: "short", year: "numeric" });
  return s;
}

export function timeAgo(iso: string, lang: "bn" | "en" = "bn") {
  const mins = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  const f = (n: number) => (lang === "bn" ? toBn(n) : String(n));
  if (mins < 60) return lang === "bn" ? `${f(mins)} মিনিট আগে` : `${mins}m ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return lang === "bn" ? `${f(h)} ঘণ্টা আগে` : `${h}h ago`;
  const d = Math.round(h / 24);
  return lang === "bn" ? `${f(d)} দিন আগে` : `${d}d ago`;
}

/** Backend dashboard_path ("/dashboard", "/agent/dashboard"…) → this app's portal routes. */
export function homeFor(u: { role: string; dashboard_path?: string }): string {
  const p = u.dashboard_path ?? "";
  if (p.startsWith("/admin")) return "/admin/dashboard";
  if (p.startsWith("/expert")) return "/expert/dashboard";
  if (p.startsWith("/agent") || p === "/dashboard") return "/farmer/dashboard";
  if (u.role === "expert") return "/expert/dashboard";
  if (["admin", "administrator", "technical_admin"].includes(u.role)) return "/admin/dashboard";
  return "/farmer/dashboard";
}

export const PHONE_RE = /^(?:\+?88)?01[3-9]\d{8}$/;
export const normalizePhone = (p: string) => p.replace(/[\s-]/g, "").replace(/^\+?88/, "");
/** Farmers use a numeric PIN (6+ digits); everyone else needs 8+ chars with upper, lower and a digit. */
export const passwordOk = (role: string, pw: string) => (role === "farmer" ? /^\d{6,}$/.test(pw) : pw.length >= 8 && /[A-Z]/.test(pw) && /[a-z]/.test(pw) && /\d/.test(pw));
