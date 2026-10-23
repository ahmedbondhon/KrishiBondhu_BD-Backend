/**
 * lib/geoDatabase.ts
 * ==================
 * Pilot Geographic Coverage for KrishiBondhu Bangladesh (MVP):
 *
 * Divisions:
 *   1. Rajshahi (রাজশাহী)
 *   2. Khulna (খুলনা)
 *
 * Districts:
 *   - Bogura (বগুড়া) — Rajshahi Division
 *   - Satkhira (সাতক্ষীরা) — Khulna Division
 *
 * Upazilas:
 *   - Bogura:
 *       * Bogura Sadar (বগুড়া সদর)
 *       * Shibganj (শিবগঞ্জ)
 *   - Satkhira:
 *       * Sadar Satkhira (সাতক্ষীরা সদর)
 *
 * Unions (for Shibganj):
 *   * Gokul (গোকুল)
 *   * Mokamtala (মোকামতলা)
 */

export interface GeoDivision {
  id: string;
  bbs: string;
  nameEn: string;
  nameBn: string;
}

export interface GeoDistrict {
  id: string;
  divisionId: string;
  bbs: string;
  nameEn: string;
  nameBn: string;
}

export interface GeoUpazila {
  id: string;
  districtId: string;
  bbs: string;
  nameEn: string;
  nameBn: string;
}

export interface GeoUnion {
  id: string;
  upazilaId: string;
  bbs: string;
  nameEn: string;
  nameBn: string;
}

// ── Pilot Divisions ──────────────────────────────────────────
export const GEO_DIVISIONS: GeoDivision[] = [
  {
    id: "10000000-0000-0000-0000-000000000001",
    bbs: "50",
    nameEn: "Rajshahi",
    nameBn: "রাজশাহী",
  },
  {
    id: "10000000-0000-0000-0000-000000000002",
    bbs: "40",
    nameEn: "Khulna",
    nameBn: "খুলনা",
  },
];

// ── Pilot Districts ──────────────────────────────────────────
export const GEO_DISTRICTS: GeoDistrict[] = [
  {
    id: "20000000-0000-0000-0000-000000000001",
    divisionId: "10000000-0000-0000-0000-000000000001", // Rajshahi
    bbs: "5010",
    nameEn: "Bogura",
    nameBn: "বগুড়া",
  },
  {
    id: "20000000-0000-0000-0000-000000000002",
    divisionId: "10000000-0000-0000-0000-000000000002", // Khulna
    bbs: "4087",
    nameEn: "Satkhira",
    nameBn: "সাতক্ষীরা",
  },
];

// ── Pilot Upazilas ───────────────────────────────────────────
export const GEO_UPAZILAS: GeoUpazila[] = [
  {
    id: "30000000-0000-0000-0000-000000000001",
    districtId: "20000000-0000-0000-0000-000000000001", // Bogura
    bbs: "501020",
    nameEn: "Bogura Sadar",
    nameBn: "বগুড়া সদর",
  },
  {
    id: "30000000-0000-0000-0000-000000000002",
    districtId: "20000000-0000-0000-0000-000000000001", // Bogura
    bbs: "501088",
    nameEn: "Shibganj",
    nameBn: "শিবগঞ্জ",
  },
  {
    id: "30000000-0000-0000-0000-000000000003",
    districtId: "20000000-0000-0000-0000-000000000002", // Satkhira
    bbs: "408782",
    nameEn: "Sadar Satkhira",
    nameBn: "সাতক্ষীরা সদর",
  },
];

// ── Pilot Unions ─────────────────────────────────────────────
export const GEO_UNIONS: GeoUnion[] = [
  {
    id: "40000000-0000-0000-0000-000000000001",
    upazilaId: "30000000-0000-0000-0000-000000000002", // Shibganj
    bbs: "15",
    nameEn: "Gokul",
    nameBn: "গোকুল",
  },
  {
    id: "40000000-0000-0000-0000-000000000002",
    upazilaId: "30000000-0000-0000-0000-000000000002", // Shibganj
    bbs: "25",
    nameEn: "Mokamtala",
    nameBn: "মোকামতলা",
  },
];

// ── Helper functions ─────────────────────────────────────────
export function getDistrictsByDivision(divisionId: string): GeoDistrict[] {
  return GEO_DISTRICTS.filter((d) => d.divisionId === divisionId);
}

export function getUpazilasByDistrict(districtId: string): GeoUpazila[] {
  return GEO_UPAZILAS.filter((u) => u.districtId === districtId);
}

export function getUnionsByUpazila(upazilaId: string): GeoUnion[] {
  return GEO_UNIONS.filter((un) => un.upazilaId === upazilaId);
}
