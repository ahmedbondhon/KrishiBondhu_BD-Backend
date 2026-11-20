import type { DiagnosisCase } from "@/types";

export const CROP_COLOR = { potato: "#2a78d6", tomato: "#eb6834", chili: "#1baf7a" } as const;

const dayKey = (d: Date) => d.toISOString().slice(0, 10);

/** Cases per day for the last `days` days, oldest first. */
export function dailyCounts(cases: DiagnosisCase[], days = 14) {
  const out: { date: string; label: Date; value: number }[] = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
    out.push({ date: dayKey(d), label: d, value: 0 });
  }
  const idx = new Map(out.map((o, i) => [o.date, i]));
  for (const c of cases) {
    const k = dayKey(new Date(c.created_at));
    const i = idx.get(k);
    if (i !== undefined) out[i].value++;
  }
  return out;
}

export function cropMix(cases: DiagnosisCase[]) {
  return (["potato", "tomato", "chili"] as const).map((code) => ({ code, value: cases.filter((c) => c.crop.code === code).length }));
}

export function confidenceMix(cases: DiagnosisCase[]) {
  return (["high", "medium", "low"] as const).map((level) => ({ level, value: cases.filter((c) => c.diagnosis.confidence_level === level).length }));
}

export function topIssues(cases: DiagnosisCase[], n = 5) {
  const m = new Map<string, { name: string; crop: DiagnosisCase["crop"]["code"]; value: number }>();
  for (const c of cases) {
    if (!c.diagnosis.issue) continue;
    const k = c.diagnosis.issue.code;
    const cur = m.get(k) ?? { name: c.diagnosis.issue.name_bn, crop: c.crop.code, value: 0 };
    cur.value++;
    m.set(k, cur);
  }
  return [...m.values()].sort((a, b) => b.value - a.value).slice(0, n);
}

export function avgConfidence(cases: DiagnosisCase[]) {
  if (!cases.length) return 0;
  return cases.reduce((s, c) => s + c.diagnosis.confidence_score, 0) / cases.length;
}
