export type Role = "farmer" | "agent" | "expert" | "admin" | "administrator" | "technical_admin" | "tech_admin";
export type Level = "high" | "medium" | "low";
export type Urgency = "low" | "medium" | "high" | "unknown";
export type CaseStatus =
  | "draft"
  | "diagnosed"
  | "needs_expert_review"
  | "under_review"
  | "response_received"
  | "closed";

export interface User {
  id: string;
  name: string;
  phone: string;
  role: Role;
  district?: string;
  upazila?: string;
  email?: string | null;
  avatar_url?: string | null;
  preferred_communication?: string;
  status?: string;
  preferred_language?: "bn" | "en";
  dashboard_path?: string;
}

export interface GeoItem { id: string; bbs_code: string; name_en: string; name_bn: string }
export interface SupportInfo {
  helpline_number: string; support_phone: string; support_email: string;
  available_hours_bn: string; available_hours_en: string; title_bn: string; title_en: string;
  instructions_bn: string; instructions_en: string;
}

export interface Crop {
  id: string;
  code: "potato" | "tomato" | "chili";
  name_bn: string;
  name_en: string;
  emoji: string;
}

export interface Issue {
  id: string;
  code: string;
  crop_code: Crop["code"];
  name_bn: string;
  name_en: string;
  symptoms_bn: string;
  severity: "medium" | "high" | "critical";
}

export interface Advisory {
  title_bn: string;
  immediate_actions_bn: string[];
  prohibited_actions_bn: string[];
  prevention_bn: string[];
  safety_warning_bn: string;
  audio_text_bn: string;
  reviewed_by: string;
  reviewed_at: string;
}

export interface Diagnosis {
  issue: Issue | null;
  confidence_score: number;
  confidence_level: Level;
  urgency: Urgency;
  requires_expert_review: boolean;
  model_version: string;
  candidates: { name_bn: string; probability: number }[];
}

export interface ExpertReply {
  expert_name: string;
  decision: "approved_ai" | "corrected_ai" | "rejected_ai";
  corrected_issue_bn?: string;
  response_bn: string;
  urgency: Urgency;
  follow_up_date?: string;
  created_at: string;
}

export interface DiagnosisCase {
  id: string;
  case_number: string;
  farmer_name: string;
  crop: Crop;
  growth_stage: string;
  symptom_bn: string;
  affected_percent: number;
  district: string;
  image_url: string;
  status: CaseStatus;
  diagnosis: Diagnosis;
  advisory: Advisory | null;
  expert_reply?: ExpertReply;
  feedback?: { helpful: "yes" | "no" | "need_help"; outcome: "better" | "same" | "worse" };
  created_at: string;
}

export interface Notification {
  id: string;
  title_bn: string;
  body_bn: string;
  read: boolean;
  created_at: string;
  case_id?: string;
}

export interface Farm {
  id: string;
  name: string;
  size_decimal: number;
  location: string;
  soil_type?: string;
  irrigation_source?: string;
  crops: FarmCrop[];
}
export interface FarmCrop {
  cycle_id?: string; crop: Crop; stage: string; stage_id?: string; planted_at: string; variety?: string;
  status?: "planned" | "active" | "harvested" | "failed"; yield_kg?: number; expected_harvest?: string; actual_harvest?: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: { request_id: string; timestamp: string };
  error?: { code: string; message_bn?: string; message_en?: string };
}
