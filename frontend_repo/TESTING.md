# KrishiBondhu Frontend — Testing Guide

## Run it (2 minutes, no backend needed)
```
npm install
cp .env.example .env.local      # Windows: copy .env.example .env.local
npm run dev                     # open http://localhost:3000
```
`.env.example` ships with `NEXT_PUBLIC_USE_MOCK=true` (demo data). On the login page use the Farmer / Expert / Admin demo cards.

## Run it against the real backend
1. Backend running at `http://localhost:8000` (check `http://localhost:8000/api/v1/geo/divisions` lists divisions).
2. In `.env.local`: `NEXT_PUBLIC_USE_MOCK=false` and `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`.
3. Restart `npm run dev` (env changes need a restart) and hard-refresh (Ctrl+Shift+R).
Demo OTP is `123456` while the backend has `OTP_DEMO_MODE=true`.

## Test checklist (mark Pass / Fail, add a screenshot + browser console error for any Fail)
| # | Area | Steps | Expected |
|---|------|-------|----------|
| 1 | Register farmer | Name, phone 01XXXXXXXXX, 6+ digit PIN, pick Division → District → Upazila → Union, OTP, accept terms + privacy | Lands on farmer dashboard |
| 2 | Geo dropdown | Change Division after choosing lower levels | Children reset and reload |
| 3 | PIN rules | Farmer PIN `12345` or `abc123`; agent password without uppercase/number | Clear Bangla error, no submit |
| 4 | Login (PIN) | Log out, log in with same phone + PIN; try "remember me" | Dashboard opens |
| 5 | Login (OTP) | OTP tab, send code, enter code | Dashboard opens; resend button counts down 60s |
| 6 | Wrong password | Enter wrong PIN | Bangla "phone or password wrong" message |
| 7 | Duplicate phone | Register an existing phone | Readable conflict message |
| 8 | Forgot password | /forgot-password → OTP → new PIN → login with new PIN | Works |
| 9 | Expert register | Role Expert, email required | "Pending admin approval", cannot log in yet |
| 10 | Session | Refresh the page; wait for token expiry | Stays logged in (auto refresh) |
| 11 | Logout | More → Log out; also "all devices" | Returns to home, protected pages redirect to login |
| 12 | Language | Switch Bangla ↔ English on every page | No untranslated or overflowing text |
| 13 | Crop photo | Upload a real leaf photo | Result with disease name, confidence, advice |
| 14 | Non-crop photo | Upload a face / table photo | Rejected with a Bangla message |
| 15 | History | Open a past case | Image + result shown |
| 16 | Support | More → helpline | Shows 16123 and a working call link |
| 17 | Profile | More → "View and edit profile": change name, location (Division → Union), language, contact method, Save | "Profile saved"; reload shows the new values |
| 18 | Avatar | Profile → add photo (JPG/PNG/WebP under 3 MB), change it, remove it | Photo appears, changes, disappears; a PDF or huge file is rejected with a message |
| 19 | Farm plot | My farm → Add farm (name, size, soil, irrigation); delete a farm | Appears in the list; delete asks for confirmation |
| 20 | Crop cycle | Add a crop to a farm (crop, growth stage, variety, planting + expected harvest date) | Shows crop, stage badge and dates |
| 21 | Change stage / harvest | On a crop: change the stage; mark harvested with yield in kg | Stage badge updates; "Harvested" badge and yield shown |
| 22 | Growth stages | Diagnose → pick a crop | Stage chips come from the backend (names differ per crop) |
| 23 | AI gatekeeper | Diagnose → pick Potato, then upload a tomato leaf / a selfie | Rejected immediately with a Bangla reason, before any upload |
| 24 | Quick diagnosis | Upload a correct leaf photo | Result in one step (no separate upload stages) |
| 25 | Mobile | Phone-size window (DevTools) | Everything usable, buttons easy to tap |

Known gaps: expert review and admin screens still use demo data. Items 13–15 and 23–24 need the backend AI key and storage bucket configured.
