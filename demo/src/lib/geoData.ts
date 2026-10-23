/**
 * lib/geoData.ts
 * ==============
 * Pilot Geographic Coverage for KrishiBondhu Bangladesh (MVP):
 *
 * Divisions:
 *   - Rajshahi (রাজশাহী)
 *   - Khulna (খুলনা)
 *
 * Districts:
 *   - Bogura (বগুড়া)
 *   - Satkhira (সাতক্ষীরা)
 *
 * Upazilas:
 *   - Bogura Sadar (বগুড়া সদর)
 *   - Shibganj (শিবগঞ্জ)
 *   - Sadar Satkhira (সাতক্ষীরা সদর)
 *
 * Unions:
 *   - Gokul (গোকুল)
 *   - Mokamtala (মোকামতলা)
 */

export interface DivisionData {
  id: string;
  nameBn: string;
  nameEn: string;
}

export interface DistrictData {
  id: string;
  divisionId: string;
  nameBn: string;
  nameEn: string;
}

export const DIVISIONS_LIST: DivisionData[] = [
  { id: "10000000-0000-0000-0000-000000000001", nameBn: "রাজশাহী", nameEn: "Rajshahi" },
  { id: "10000000-0000-0000-0000-000000000002", nameBn: "খুলনা", nameEn: "Khulna" },
];

export const DISTRICTS_LIST: Record<string, string[]> = {
  রাজশাহী: ["বগুড়া"],
  খুলনা: ["সাতক্ষীরা"],
};

export const UPAZILAS_SAMPLE: Record<string, string[]> = {
  বগুড়া: ["বগুড়া সদর", "শিবগঞ্জ"],
  সাতক্ষীরা: ["সাতক্ষীরা সদর"],
};

export const UNIONS_SAMPLE: Record<string, string[]> = {
  শিবগঞ্জ: ["গোকুল", "মোকামতলা"],
  "বগুড়া সদর": ["গোকুল", "মোকামতলা"],
  "সাতক্ষীরা সদর": ["সাতক্ষীরা পৌরসভা"],
};
