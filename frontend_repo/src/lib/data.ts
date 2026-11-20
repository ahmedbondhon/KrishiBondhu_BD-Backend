import type { Advisory, Crop, DiagnosisCase, Farm, Issue, Notification } from "@/types";

/** Mirrors backend/database/seeds (potato, tomato, chili — pilot crops). */
export const CROPS: Crop[] = [
  { id: "50000000-0000-0000-0000-000000000001", code: "potato", name_bn: "আলু", name_en: "Potato", emoji: "🥔" },
  { id: "50000000-0000-0000-0000-000000000002", code: "tomato", name_bn: "টমেটো", name_en: "Tomato", emoji: "🍅" },
  { id: "50000000-0000-0000-0000-000000000003", code: "chili", name_bn: "মরিচ", name_en: "Chili", emoji: "🌶️" },
];

export const STAGES = [
  { code: "seedling", bn: "চারা", en: "Seedling" },
  { code: "vegetative", bn: "বৃদ্ধি পর্যায়", en: "Vegetative" },
  { code: "flowering", bn: "ফুল আসা", en: "Flowering" },
  { code: "fruiting", bn: "ফল ধরা", en: "Fruiting" },
  { code: "harvest", bn: "ফসল তোলা", en: "Harvest" },
];

export const DISTRICTS = ["বগুড়া", "রংপুর", "যশোর", "সাতক্ষীরা", "খুলনা", "বরিশাল"];

export const ISSUES: Issue[] = [
  { id: "70000000-0000-0000-0000-000000000001", code: "potato_late_blight", crop_code: "potato", name_bn: "আলুর লেট ব্লাইট (নাবি ধসা)", name_en: "Potato Late Blight", symptoms_bn: "পাতায় পানি ভেজা দাগ, দ্রুত কালো হয়ে পচে যায়। আর্দ্র আবহাওয়ায় পাতার নিচে সাদা ছত্রাক দেখা যায়।", severity: "critical" },
  { id: "70000000-0000-0000-0000-000000000002", code: "potato_early_blight", crop_code: "potato", name_bn: "আলুর আর্লি ব্লাইট (আগাম ধসা)", name_en: "Potato Early Blight", symptoms_bn: "পুরোনো পাতায় গাঢ় বাদামি গোলাকার দাগ, দাগের ভেতরে রিংয়ের মতো বলয় থাকে।", severity: "medium" },
  { id: "70000000-0000-0000-0000-000000000005", code: "tomato_early_blight", crop_code: "tomato", name_bn: "টমেটোর আগাম ধসা রোগ", name_en: "Tomato Early Blight", symptoms_bn: "নিচের পাতায় বাদামি দাগ, দাগের চারপাশে হলুদ আভা দেখা যায়।", severity: "medium" },
  { id: "70000000-0000-0000-0000-000000000003", code: "tomato_leaf_curl", crop_code: "tomato", name_bn: "টমেটোর পাতা কোঁকড়ানো রোগ", name_en: "Tomato Leaf Curl Virus", symptoms_bn: "পাতা উপরের দিকে কুঁকড়ে ছোট হয়ে যায়, গাছ খর্বাকৃতি হয় এবং ফল কমে যায়।", severity: "high" },
  { id: "70000000-0000-0000-0000-000000000004", code: "chili_leaf_curl", crop_code: "chili", name_bn: "মরিচের পাতা কোঁকড়ানো রোগ", name_en: "Chili Leaf Curl Virus", symptoms_bn: "পাতা নৌকার মতো উপরে কুঁকড়ে যায়, নতুন পাতা ছোট হয়। সাদা মাছি এই রোগ ছড়ায়।", severity: "high" },
];

const REVIEWER = "কৃষি কর্মকর্তা (যাচাইকৃত)";

export const ADVISORIES: Record<string, Advisory> = {
  potato_late_blight: {
    title_bn: "আজ কী করবেন",
    immediate_actions_bn: ["আক্রান্ত পাতা বা গাছ তুলে মাটিতে পুঁতে ফেলুন।", "কুয়াশা বা বৃষ্টির সময় সেচ বন্ধ রাখুন।", "আজই আশেপাশের গাছগুলো ভালো করে দেখুন।"],
    prohibited_actions_bn: ["অনুমোদন ছাড়া ছত্রাকনাশক বা বাড়তি কীটনাশক দেবেন না।", "আক্রান্ত গাছ ক্ষেতের পাশে ফেলে রাখবেন না।"],
    prevention_bn: ["ক্ষেতে পানি জমতে দেবেন না, নালা পরিষ্কার রাখুন।", "পরের মৌসুমে রোগমুক্ত বীজ ব্যবহার করুন।"],
    safety_warning_bn: "রোগ দ্রুত ছড়ালে বা ক্ষেতের অর্ধেকের বেশি গাছে দেখা দিলে এখনই কৃষি কর্মকর্তার পরামর্শ নিন।",
    audio_text_bn: "আপনার আলুতে নাবি ধসা রোগের লক্ষণ দেখা যাচ্ছে। আক্রান্ত পাতা তুলে মাটিতে পুঁতে ফেলুন। কুয়াশার সময় সেচ বন্ধ রাখুন। রোগ ছড়িয়ে পড়লে কৃষি কর্মকর্তার পরামর্শ নিন।",
    reviewed_by: REVIEWER, reviewed_at: "2026-09-20",
  },
  potato_early_blight: {
    title_bn: "আজ কী করবেন",
    immediate_actions_bn: ["নিচের আক্রান্ত পাতাগুলো আলাদা করে ফেলুন।", "পাতায় সরাসরি পানি দেওয়া এড়িয়ে চলুন।", "পরের দুই দিন গাছগুলো পর্যবেক্ষণ করুন।"],
    prohibited_actions_bn: ["অনুমোদন ছাড়া অতিরিক্ত কীটনাশক ব্যবহার করবেন না।"],
    prevention_bn: ["গাছের মধ্যে পর্যাপ্ত ফাঁক রাখুন যাতে বাতাস চলাচল করে।", "সুষম সার ব্যবহার করুন।"],
    safety_warning_bn: "সমস্যা দ্রুত ছড়িয়ে পড়লে কৃষি বিশেষজ্ঞের পরামর্শ নিন।",
    audio_text_bn: "আপনার আলুতে আগাম ধসা রোগের লক্ষণ দেখা যাচ্ছে। আক্রান্ত পাতা আলাদা করুন এবং পাতায় সরাসরি পানি দেবেন না।",
    reviewed_by: REVIEWER, reviewed_at: "2026-09-20",
  },
  tomato_early_blight: {
    title_bn: "আজ কী করবেন",
    immediate_actions_bn: ["আক্রান্ত পাতা আলাদা করুন।", "পাতায় সরাসরি পানি দেওয়া এড়িয়ে চলুন।", "পরবর্তী দুই দিন গাছগুলো পর্যবেক্ষণ করুন।"],
    prohibited_actions_bn: ["অনুমোদন ছাড়া অতিরিক্ত কীটনাশক ব্যবহার করবেন না।"],
    prevention_bn: ["সকালে সেচ দিন, সন্ধ্যায় পাতা ভেজাবেন না।", "গাছের নিচের পুরোনো পাতা ছেঁটে দিন।"],
    safety_warning_bn: "সমস্যা দ্রুত ছড়িয়ে পড়লে কৃষি বিশেষজ্ঞের পরামর্শ নিন।",
    audio_text_bn: "আপনার টমেটো গাছে আগাম ধসা রোগের লক্ষণ দেখা যাচ্ছে। আক্রান্ত পাতা আলাদা করুন এবং পাতায় সরাসরি পানি দেবেন না।",
    reviewed_by: REVIEWER, reviewed_at: "2026-09-22",
  },
  tomato_leaf_curl: {
    title_bn: "আজ কী করবেন",
    immediate_actions_bn: ["আক্রান্ত গাছ তুলে ক্ষেত থেকে দূরে নষ্ট করুন।", "ক্ষেতে সাদা মাছি আছে কি না পাতার নিচে দেখুন।", "হলুদ আঠালো ফাঁদ ব্যবহার করা যেতে পারে।"],
    prohibited_actions_bn: ["অনুমোদন ছাড়া কীটনাশক ব্যবহার করবেন না।", "আক্রান্ত গাছের চারা অন্য ক্ষেতে লাগাবেন না।"],
    prevention_bn: ["চারা তৈরির সময় নেট দিয়ে ঢেকে রাখুন।", "ক্ষেতের আশপাশের আগাছা পরিষ্কার রাখুন।"],
    safety_warning_bn: "ভাইরাস রোগ দ্রুত ছড়ায়। কাছের কৃষি অফিসে যোগাযোগ করুন।",
    audio_text_bn: "আপনার টমেটোতে পাতা কোঁকড়ানো রোগের লক্ষণ দেখা যাচ্ছে। আক্রান্ত গাছ তুলে ফেলুন এবং সাদা মাছি আছে কি না দেখুন।",
    reviewed_by: REVIEWER, reviewed_at: "2026-09-22",
  },
  chili_leaf_curl: {
    title_bn: "আজ কী করবেন",
    immediate_actions_bn: ["আক্রান্ত গাছ তুলে ক্ষেত থেকে দূরে নষ্ট করুন।", "পাতার নিচে সাদা মাছি খুঁজুন।", "হলুদ আঠালো ফাঁদ ব্যবহার করা যেতে পারে।"],
    prohibited_actions_bn: ["অনুমোদন ছাড়া কীটনাশক ব্যবহার করবেন না।"],
    prevention_bn: ["রোগমুক্ত চারা ব্যবহার করুন।", "ক্ষেতের চারপাশের আগাছা পরিষ্কার রাখুন।"],
    safety_warning_bn: "রোগ ছড়িয়ে পড়লে কৃষি কর্মকর্তার পরামর্শ নিন।",
    audio_text_bn: "আপনার মরিচে পাতা কোঁকড়ানো রোগের লক্ষণ দেখা যাচ্ছে। আক্রান্ত গাছ তুলে ফেলুন এবং সাদা মাছি দমনে কৃষি কর্মকর্তার পরামর্শ নিন।",
    reviewed_by: REVIEWER, reviewed_at: "2026-09-25",
  },
};

export const SAFE_GENERAL_ADVISORY: Advisory = {
  title_bn: "আজ কী করবেন",
  immediate_actions_bn: ["আক্রান্ত অংশ আলাদা করুন এবং আশেপাশের গাছ দেখুন।", "পরিষ্কার আলোয় আরও একটি কাছ থেকে ছবি তুলুন।"],
  prohibited_actions_bn: ["রোগ নিশ্চিত না হয়ে কোনো কীটনাশক দেবেন না।"],
  prevention_bn: ["ক্ষেতে পানি জমতে দেবেন না।"],
  safety_warning_bn: "সিস্টেম নিশ্চিত হতে পারেনি। কৃষি বিশেষজ্ঞের পরামর্শ নিন।",
  audio_text_bn: "সিস্টেম রোগটি নিশ্চিতভাবে শনাক্ত করতে পারেনি। বিশেষজ্ঞের পরামর্শ নিন।",
  reviewed_by: REVIEWER, reviewed_at: "2026-09-20",
};

/** Simple generated leaf picture so demo cases have an image without any binary assets. */
export function leafPlaceholder(hue = 110, spots = 4): string {
  const dots = Array.from({ length: spots }, (_, i) => {
    const x = 90 + ((i * 53) % 120), y = 70 + ((i * 71) % 130);
    return `<circle cx='${x}' cy='${y}' r='${10 + (i % 3) * 5}' fill='#6b3a1d' opacity='.75'/>`;
  }).join("");
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 300'><rect width='300' height='300' fill='hsl(${hue},25%,22%)'/><path d='M150 30C240 80 250 200 150 275 50 200 60 80 150 30Z' fill='hsl(${hue},45%,38%)'/><path d='M150 40V270' stroke='hsl(${hue},40%,28%)' stroke-width='4'/>${dots}</svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

const ago = (h: number) => new Date(Date.now() - h * 3600_000).toISOString();
const crop = (c: Crop["code"]) => CROPS.find((x) => x.code === c)!;
const issue = (c: string) => ISSUES.find((x) => x.code === c)!;

function baseCases(): DiagnosisCase[] {
  return [
    {
      id: "c-1", case_number: "KB-2026-000124", farmer_name: "আব্দুল করিম", crop: crop("tomato"), growth_stage: "ফল ধরা",
      symptom_bn: "পাতায় বাদামি দাগ দেখা যাচ্ছে", affected_percent: 15, district: "বগুড়া", image_url: leafPlaceholder(110, 4),
      status: "diagnosed", created_at: ago(5),
      diagnosis: { issue: issue("tomato_early_blight"), confidence_score: 0.82, confidence_level: "high", urgency: "medium", requires_expert_review: false, model_version: "v1.0.0",
        candidates: [{ name_bn: "টমেটোর আগাম ধসা রোগ", probability: 0.82 }, { name_bn: "টমেটোর লেট ব্লাইট", probability: 0.11 }, { name_bn: "অন্যান্য", probability: 0.07 }] },
      advisory: ADVISORIES.tomato_early_blight,
    },
    {
      id: "c-2", case_number: "KB-2026-000118", farmer_name: "আব্দুল করিম", crop: crop("potato"), growth_stage: "বৃদ্ধি পর্যায়",
      symptom_bn: "পাতা কালো হয়ে পচে যাচ্ছে, কুয়াশার পর বেড়েছে", affected_percent: 40, district: "বগুড়া", image_url: leafPlaceholder(95, 6),
      status: "response_received", created_at: ago(52),
      diagnosis: { issue: issue("potato_late_blight"), confidence_score: 0.64, confidence_level: "medium", urgency: "high", requires_expert_review: true, model_version: "v1.0.0",
        candidates: [{ name_bn: "আলুর লেট ব্লাইট", probability: 0.64 }, { name_bn: "আলুর আর্লি ব্লাইট", probability: 0.27 }, { name_bn: "অন্যান্য", probability: 0.09 }] },
      advisory: ADVISORIES.potato_late_blight,
      expert_reply: { expert_name: "ড. রহমান, কৃষি কর্মকর্তা", decision: "approved_ai", urgency: "high", follow_up_date: "2026-10-18", created_at: ago(30),
        response_bn: "লেট ব্লাইট নিশ্চিত। আক্রান্ত অংশ আজই সরিয়ে ফেলুন এবং দুই দিনের মধ্যে স্থানীয় উপজেলা কৃষি অফিসে যোগাযোগ করে অনুমোদিত ব্যবস্থা নিন।" },
    },
    {
      id: "c-3", case_number: "KB-2026-000131", farmer_name: "রহিমা বেগম", crop: crop("chili"), growth_stage: "ফুল আসা",
      symptom_bn: "পাতা নৌকার মতো কুঁকড়ে যাচ্ছে", affected_percent: 25, district: "সাতক্ষীরা", image_url: leafPlaceholder(130, 2),
      status: "needs_expert_review", created_at: ago(2),
      diagnosis: { issue: null, confidence_score: 0.38, confidence_level: "low", urgency: "unknown", requires_expert_review: true, model_version: "v1.0.0",
        candidates: [{ name_bn: "মরিচের পাতা কোঁকড়ানো রোগ", probability: 0.38 }, { name_bn: "পুষ্টির ঘাটতি", probability: 0.31 }, { name_bn: "অন্যান্য", probability: 0.31 }] },
      advisory: SAFE_GENERAL_ADVISORY,
    },
    {
      id: "c-4", case_number: "KB-2026-000133", farmer_name: "হাসান আলী", crop: crop("potato"), growth_stage: "ফুল আসা",
      symptom_bn: "বাদামি রিংয়ের মতো দাগ", affected_percent: 10, district: "রংপুর", image_url: leafPlaceholder(100, 5),
      status: "needs_expert_review", created_at: ago(1),
      diagnosis: { issue: issue("potato_early_blight"), confidence_score: 0.57, confidence_level: "low", urgency: "medium", requires_expert_review: true, model_version: "v1.0.0",
        candidates: [{ name_bn: "আলুর আর্লি ব্লাইট", probability: 0.57 }, { name_bn: "আলুর লেট ব্লাইট", probability: 0.33 }, { name_bn: "অন্যান্য", probability: 0.1 }] },
      advisory: ADVISORIES.potato_early_blight,
    },
    {
      id: "c-5", case_number: "KB-2026-000129", farmer_name: "সালমা খাতুন", crop: crop("tomato"), growth_stage: "চারা",
      symptom_bn: "পাতা কুঁকড়ে হলুদ হচ্ছে", affected_percent: 60, district: "যশোর", image_url: leafPlaceholder(120, 3),
      status: "under_review", created_at: ago(9),
      diagnosis: { issue: issue("tomato_leaf_curl"), confidence_score: 0.71, confidence_level: "medium", urgency: "high", requires_expert_review: true, model_version: "v1.0.0",
        candidates: [{ name_bn: "টমেটোর পাতা কোঁকড়ানো রোগ", probability: 0.71 }, { name_bn: "পুষ্টির ঘাটতি", probability: 0.2 }, { name_bn: "অন্যান্য", probability: 0.09 }] },
      advisory: ADVISORIES.tomato_leaf_curl,
    },
  ];
}

export function seedNotifications(): Notification[] {
  return [
    { id: "n-1", title_bn: "বিশেষজ্ঞের উত্তর এসেছে", body_bn: "আপনার আলুর কেস KB-2026-000118-এ কৃষি কর্মকর্তা উত্তর দিয়েছেন।", read: false, created_at: ago(30), case_id: "c-2" },
    { id: "n-2", title_bn: "ফলোআপ মনে করিয়ে দিচ্ছি", body_bn: "ফলাফল জানাতে আপনার টমেটো ক্ষেতের অবস্থা আপডেট করুন।", read: true, created_at: ago(70) },
  ];
}

export function seedFarms(): Farm[] {
  return [
    { id: "f-1", name: "উত্তর মাঠ", size_decimal: 80, location: "শিবগঞ্জ, বগুড়া", crops: [
      { crop: crop("potato"), stage: "বৃদ্ধি পর্যায়", planted_at: "2026-09-12", variety: "গ্রানোলা" },
      { crop: crop("tomato"), stage: "ফল ধরা", planted_at: "2026-08-28", variety: "বারি টমেটো ১৪" } ] },
  ];
}

/* ---- Extra history so dashboards and charts have a believable shape ---- */
type Mk = [id: string, farmer: string, crop: Crop["code"], issue: string | null, score: number, daysAgo: number, status: DiagnosisCase["status"], district: string, pct: number, stage: string];
const EXTRA: Mk[] = [
  ["e1", "আব্দুল করিম", "potato", "potato_early_blight", 0.88, 26, "diagnosed", "বগুড়া", 10, "বৃদ্ধি পর্যায়"],
  ["e2", "রহিমা বেগম", "chili", "chili_leaf_curl", 0.79, 24, "diagnosed", "সাতক্ষীরা", 20, "ফুল আসা"],
  ["e3", "হাসান আলী", "potato", "potato_late_blight", 0.91, 22, "diagnosed", "রংপুর", 35, "বৃদ্ধি পর্যায়"],
  ["e4", "সালমা খাতুন", "tomato", "tomato_leaf_curl", 0.74, 20, "response_received", "যশোর", 45, "চারা"],
  ["e5", "আব্দুল করিম", "tomato", "tomato_early_blight", 0.85, 19, "diagnosed", "বগুড়া", 15, "ফল ধরা"],
  ["e6", "রহিমা বেগম", "tomato", null, 0.33, 17, "response_received", "সাতক্ষীরা", 25, "ফুল আসা"],
  ["e7", "হাসান আলী", "chili", "chili_leaf_curl", 0.83, 15, "diagnosed", "রংপুর", 30, "ফল ধরা"],
  ["e8", "আব্দুল করিম", "potato", "potato_late_blight", 0.77, 12, "response_received", "বগুড়া", 40, "বৃদ্ধি পর্যায়"],
  ["e9", "সালমা খাতুন", "potato", "potato_early_blight", 0.9, 10, "diagnosed", "যশোর", 10, "ফুল আসা"],
  ["e10", "হাসান আলী", "tomato", "tomato_early_blight", 0.69, 8, "diagnosed", "রংপুর", 20, "ফল ধরা"],
  ["e11", "রহিমা বেগম", "chili", "chili_leaf_curl", 0.92, 6, "diagnosed", "সাতক্ষীরা", 15, "ফুল আসা"],
  ["e12", "আব্দুল করিম", "potato", "potato_late_blight", 0.86, 4, "diagnosed", "বগুড়া", 25, "বৃদ্ধি পর্যায়"],
  ["e13", "সালমা খাতুন", "tomato", "tomato_leaf_curl", 0.81, 3, "diagnosed", "যশোর", 35, "চারা"],
  ["e14", "হাসান আলী", "potato", "potato_late_blight", 0.88, 2, "diagnosed", "রংপুর", 30, "বৃদ্ধি পর্যায়"],
];
const HUE = { potato: 98, tomato: 118, chili: 132 } as const;

function extraCases(): DiagnosisCase[] {
  return EXTRA.map(([id, farmer, cc, ic, score, d, status, district, pct, stage], i) => {
    const iss = ic ? issue(ic) : null;
    const level = score >= 0.8 ? "high" : score >= 0.55 ? "medium" : "low";
    const sibling = ISSUES.find((x) => x.crop_code === cc && x.code !== ic);
    const rest = 1 - score;
    return {
      id, case_number: `KB-2026-${String(100 + i).padStart(6, "0")}`, farmer_name: farmer, crop: crop(cc), growth_stage: stage,
      symptom_bn: iss ? iss.symptoms_bn.split("।")[0] : "পাতায় অস্বাভাবিক দাগ", affected_percent: pct, district,
      image_url: leafPlaceholder(HUE[cc] + (i % 4) * 4, 2 + (i % 5)), status, created_at: ago(d * 24 + (i % 5)),
      diagnosis: {
        issue: iss, confidence_score: score, confidence_level: level, urgency: iss ? (iss.severity === "medium" ? "medium" : "high") : "unknown",
        requires_expert_review: !iss || status === "response_received", model_version: "v1.0.0",
        candidates: [{ name_bn: iss?.name_bn ?? "অনিশ্চিত", probability: score }, { name_bn: sibling?.name_bn ?? "অন্যান্য", probability: Number((rest * 0.7).toFixed(2)) }, { name_bn: "অন্যান্য", probability: Number((rest * 0.3).toFixed(2)) }],
      },
      advisory: iss ? ADVISORIES[iss.code] : SAFE_GENERAL_ADVISORY,
      expert_reply: status === "response_received" ? { expert_name: "ড. রহমান, কৃষি কর্মকর্তা", decision: iss ? "approved_ai" : "corrected_ai", corrected_issue_bn: iss ? undefined : "পুষ্টির ঘাটতি (পটাশিয়াম)", response_bn: "ছবি দেখে সমস্যাটি যাচাই করা হয়েছে। আক্রান্ত অংশ আলাদা করে পর্যবেক্ষণ চালিয়ে যান।", urgency: "medium", created_at: ago(d * 24 - 6) } : undefined,
    } satisfies DiagnosisCase;
  });
}

export function seedCases(): DiagnosisCase[] {
  return [...baseCases(), ...extraCases()];
}
