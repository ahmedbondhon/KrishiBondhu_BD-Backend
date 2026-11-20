# KrishiBondhu Bangladesh — Frontend

Bangla-first, mobile-first agricultural SaaS web app (PWA) for farmers, agricultural experts and admins.
Built from the project's API/Technology, Requirements, Architecture and Database documents.

**Stack:** Next.js 14 (App Router) · React 18 · TypeScript · Tailwind CSS · TanStack Query · Zustand · lucide-react

## Run it

```bash
npm install
cp .env.example .env.local     # already set to demo (mock) mode
npm run dev                    # http://localhost:3000
```

Production check: `npm run typecheck && npm run build && npm start`.
Open `/login` and use the **Farmer / Expert / Admin** demo cards.

## Run against the real backend (demo branch)

1. Backend: put the shared `.env` in the backend folder (never in this repo), `pip install -r backend/requirements.txt`, then
   `cd backend && uvicorn app.main:app --reload --port 8000`. Check `http://localhost:8000/health` and `/docs`.
2. Frontend: `.env.local` already has `NEXT_PUBLIC_USE_MOCK=false` and `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`.
   `npm install && npm run dev` → http://localhost:3000 (allowed by the backend's default CORS list).
3. With `OTP_DEMO_MODE=true` the OTP is `123456`. Crop photos go browser → signed URL → Supabase bucket → `/files/confirm-upload`
   (the backend gatekeeper rejects non-crop images) → `/diagnosis-cases` → `/images` → `/analyze`. No Supabase key is used in the browser.

## Mock mode vs real backend

`NEXT_PUBLIC_USE_MOCK=true` runs against seeded in-browser data (the same crops, issues and Bangla advisories as
`backend/database/seeds`, plus 14 days of sample history so charts have shape). Demo data lives in `localStorage`
(`kb-mock-db-v2`); clear it to reset. To use the FastAPI backend:

```env
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

All API calls are in **`src/lib/api.ts`**. Auth follows the *KrishiBondhu Backend Handoff Guide*: OTP send/verify with
`purpose` + `verification_token`, farmer PIN / agent-expert-admin strong-password rules, expert registration (pending
admin approval), password and passwordless-OTP login with `remember_me`, forgot/reset password, automatic
`/auth/refresh` on 401 (refresh tokens rotate), logout / logout-all, language sync, `/auth/support` helpline and the
cascading `/geo/*` dropdowns. Both the raw FastAPI bodies and the `{success, data}` envelope are handled, and the
backend `dashboard_path` is mapped to this app's portal routes (`homeFor` in `src/lib/utils.ts`). Its function signatures and the types in `src/types` are unchanged by the redesign.

## Routes

| Area | Routes |
|---|---|
| Public | `/` landing · `/login` (password/PIN or OTP) · `/register` (farmer / agent / expert, OTP + consent) · `/forgot-password` |
| Farmer | `/farmer/dashboard` · `/farmer/diagnose` · `/farmer/cases` · `/farmer/cases/[id]` · `/farmer/farms` · `/farmer/notifications` · `/farmer/more` |
| Expert | `/expert/dashboard` · `/expert/cases` · `/expert/cases/[id]` |
| Admin | `/admin/dashboard` · `/admin/knowledge-base` · `/admin/users` |

## Design system ("Canopy")

- **Colour** (`tailwind.config.ts`): `canopy`/`brand` greens for structure and actions, `lime` highlight used only on dark
  surfaces, `sun`/`clay`/`sky` reserved for status. Crop identity in charts uses three validated categorical colours
  (`series-1..3`, `src/lib/analytics.ts → CROP_COLOR`).
- **Type:** Anek Bangla (headings) + Hind Siliguri (body), self-hosted via `@fontsource` — no runtime Google Fonts request.
- **Shell:** one `AppShell` (`src/components/shells.tsx`) for all three portals: sidebar on desktop, top bar + bottom tabs on mobile.
- **UI kit:** `src/components/ui.tsx` (buttons, badges, drawer, segmented control, skeletons, empty states).
- **Charts:** dependency-free SVG in `src/components/charts.tsx` (trend with crosshair tooltip, donut, bars, gauge, sparkline).
  Every chart has a table view toggle; status chips always pair colour with an icon and text.

## Requirement highlights

- One-tap photo check; 4-step wizard with drag-and-drop, camera + gallery fallback, client-side compression (<5 MB)
  and blur/dark/bright check with retake prompt; drafts saved so a dropped connection loses nothing
- High / Medium / Low confidence and urgency; low confidence is shown as "not identified", never as a diagnosis
- "Do today / Avoid / Prevent" advice, Bangla text-to-speech, expert escalation with status timeline, feedback loop
- Expert review keeps the AI prediction read-only; approve / correct / reject with a Bangla reply
- Admin: advisory publishing locked until approved, user verification, quality charts
- Offline banner, service worker + manifest, skip link, visible focus, reduced-motion support, Bangla/English toggle
- Weather and market modules stay behind feature flags (`NEXT_PUBLIC_FLAG_CLIMATE`, `NEXT_PUBLIC_FLAG_MARKET`)

## Notes

- Role redirects are a UI convenience only; the backend must enforce RBAC on every endpoint.
- `public/icon.svg` is a placeholder; add 192/512 px PNG icons for full Android PWA install.
- Have a Bangla speaker review advisory copy before showing it to farmers.
