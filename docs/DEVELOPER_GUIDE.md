# KrishiBondhu Bangladesh — Backend Developer Guide
## Team Onboarding Document

> **For new team members:** Read this entire document before touching any code.
> This explains what every file does, why it was built the way it was, and how to run the app.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Project Structure — What Does What](#project-structure)
3. [How to Set Up and Run](#how-to-run)
4. [How the Database Works](#database)
5. [Authentication Flow](#authentication)
6. [The ChashiGuard AI Flow](#chashiguard-flow)
7. [API Endpoints Reference](#api-endpoints)
8. [Key Rules & Invariants](#rules)
9. [How to Add a New Feature](#adding-features)
10. [Running Tests](#tests)

---

## 1. Architecture Overview

This is a **FastAPI** (Python) REST API backend for the KrishiBondhu crop disease diagnosis platform.

```
Client (Mobile App / Web)
        │
        ▼
  FastAPI Backend (/api/v1/)          ◄── YOU ARE HERE
        │
        ├──► PostgreSQL Database (via SQLAlchemy async ORM)
        ├──► Supabase / AWS S3 (file storage — signed URLs)
        └──► AI Service (separate FastAPI app, /internal/v1/)
```

**Key design principle:** Farmers in Bangladesh are the end users. All farmer-facing messages MUST be in Bangla (বাংলা).

---

## 2. Project Structure

```
backend/
├── app/
│   ├── main.py                  ← FastAPI app entry point — starts here
│   │
│   ├── core/                    ← App-wide utilities (no business logic here)
│   │   ├── config.py            ← All settings loaded from .env file
│   │   ├── security.py          ← Password hashing + JWT tokens
│   │   ├── dependencies.py      ← FastAPI dependency injection (auth, DB sessions)
│   │   └── responses.py         ← Standardized JSON response helpers
│   │
│   ├── db/                      ← Database connection layer
│   │   ├── base.py              ← SQLAlchemy Base class + UUID/Timestamp mixins
│   │   └── session.py           ← Async DB engine + session factory
│   │
│   ├── models/                  ← SQLAlchemy ORM models (Python ↔ DB table mapping)
│   │   ├── auth.py              ← User, Role, OtpLog, ConsentType
│   │   ├── catalog.py           ← Crop, CropVariety, GrowthStage, Issue, Remedy
│   │   ├── farm.py              ← Plot, PlotCrop (cultivation cycles)
│   │   ├── system.py            ← SystemFile (uploaded files), AuditLog, Notification
│   │   ├── diagnosis.py         ← DiagnosisCase, CaseImage, ExpertReview
│   │   ├── ai.py                ← AIModel, AIPrediction (IMMUTABLE), feedback
│   │   ├── advisory.py          ← AdvisoryTemplate, Advisory, Feedback
│   │   └── __init__.py          ← Registers all models (IMPORTANT for Alembic)
│   │
│   ├── schemas/                 ← Pydantic v2 request/response validation
│   │   ├── auth.py              ← RegisterRequest, LoginRequest, UserResponse, etc.
│   │   ├── farm.py              ← CreatePlotRequest, PlotResponse, etc.
│   │   ├── files.py             ← Upload URL + Confirm Upload schemas
│   │   └── diagnosis.py         ← Case creation, AI response, expert review schemas
│   │
│   ├── services/                ← Business logic (NO HTTP code here)
│   │   ├── auth_service.py      ← Register user, verify login, refresh tokens
│   │   ├── storage_service.py   ← Generate signed upload/view URLs (Supabase/S3)
│   │   └── diagnosis_service.py ← Full ChashiGuard AI pipeline logic
│   │
│   └── api/
│       └── v1/
│           ├── __init__.py      ← Assembles all routes under /api/v1
│           ├── auth.py          ← Route handlers: /auth/register, /auth/login, etc.
│           ├── farms.py         ← Route handlers: /farms, /farms/{id}/crop-cycles
│           ├── files.py         ← Route handlers: /files/upload-url, /files/confirm-upload
│           ├── diagnosis.py     ← Route handlers: /diagnosis-cases, /expert/cases
│           └── notifications.py ← Route handlers: /notifications, /notifications/{id}/read
│
├── alembic/
│   └── env.py                   ← Alembic migration environment (connects to our models)
│
├── tests/
│   ├── test_auth.py             ← Auth endpoint tests
│   └── test_diagnosis.py        ← Diagnosis flow tests
│
├── alembic.ini                  ← Alembic configuration
├── requirements.txt             ← Python package dependencies
└── .env.example                 ← Copy to .env and fill in your values
```

### Layer Responsibility Summary

| Layer | Files | Responsibility | Can it access DB? |
|---|---|---|---|
| **Routes** (api/) | auth.py, farms.py, etc. | Parse HTTP requests, call services, return responses | No — uses `db` from dependency |
| **Services** (services/) | auth_service.py, etc. | All business logic and rules | Yes — receives `db` as argument |
| **Models** (models/) | auth.py, catalog.py, etc. | Define DB table structure | No — just definitions |
| **Schemas** (schemas/) | auth.py, farm.py, etc. | Validate input/output data | No — just data shapes |
| **Core** (core/) | config, security, deps | Config, JWT, middleware | No — utilities only |

---

## 3. How to Set Up and Run

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- Node.js (only if running the frontend)

### Step 1: Create a Virtual Environment
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate  (Mac/Linux)
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
copy .env.example .env
# Edit .env with your database URL, JWT secret, and Supabase keys
```

### Step 4: Run Database Migrations (SQL)
The SQL migrations are in `database/migrations/`. Run them in order:
```bash
psql -U postgres -d krishibondhu_db -f database/migrations/001_extensions_and_schemas.sql
psql -U postgres -d krishibondhu_db -f database/migrations/002_auth_tables.sql
# ... continue through 014_seed_data.sql
```

### Step 5: Start the Server
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Open in browser: **http://localhost:8000/api/v1/docs** (Swagger UI)

---

## 4. How the Database Works

### PostgreSQL Schemas
The database uses multiple **PostgreSQL schemas** to organize tables by domain:

| Schema | Tables | Purpose |
|---|---|---|
| `auth` | users, roles, user_consents, otp_logs | Authentication & authorization |
| `geo` | divisions, districts, upazilas, unions | Bangladesh geographic hierarchy |
| `catalog` | crops, crop_varieties, growth_stages, issues, remedies | Agricultural master data |
| `farm` | plots, plot_crops | Farmer land and crop cycles |
| `system` | files, audit_logs, notifications | File metadata + audit trail + in-app notifications |
| `ai` | models, predictions, prediction_details, model_feedback | AI inference records |
| `advisory` | templates, advisories, feedbacks | Bangla advice content |
| `case_mgmt` | diagnosis_cases, case_images, expert_reviews, case_assignments | Case management |

### ORM Models (Python ↔ DB)
Each model file in `app/models/` maps to one or more database tables.
Models inherit from `Base` (SQLAlchemy's `DeclarativeBase`) plus mixins:
- `UUIDPrimaryKeyMixin` — adds `id: UUID` primary key
- `TimestampMixin` — adds `created_at`, `updated_at` timestamps

### Async Sessions
Database queries use `AsyncSession` (non-blocking). Every request gets a fresh session via `Depends(get_db)`. The session is committed on success and rolled back on error automatically.

---

## 5. Authentication Flow

### How JWT Works in This System

```
1. POST /api/v1/auth/register  → Creates user in DB
2. POST /api/v1/auth/login     → Returns access_token + refresh_token
3. Client sends: Authorization: Bearer <access_token>  (on every protected request)
4. Dependency get_current_user() validates the token and returns the User object
5. POST /api/v1/auth/refresh   → Exchange refresh_token for a new token pair
```

### Token Types
| Token | Expiry | Purpose |
|---|---|---|
| `access_token` | 60 minutes (default) | Authenticate API requests |
| `refresh_token` | 30 days (default) | Get a new access token without logging in again |

### Role-Based Access Control (RBAC)
Use `Depends(require_roles("farmer", "expert"))` in route handlers to restrict access.

Available roles: `farmer`, `agent`, `expert`, `admin`, `tech_admin`

```python
# Example: Only experts and admins can access this route
@router.get("/expert-data", dependencies=[Depends(require_roles("expert", "admin"))])
async def get_expert_data(...):
    ...
```

---

## 6. The ChashiGuard AI Flow

This is the core of the platform. Here's the full journey of a diagnosis case:

```
FARMER SUBMITS CASE
        │
        ▼
POST /diagnosis-cases        ← Creates case with status='submitted'
        │
        ▼
POST /diagnosis-cases/{id}/images  ← Farmer uploads image (2-step: upload-url → confirm)
        │
        ▼
POST /diagnosis-cases/{id}/analyze
        │
        ├── Status → 'processing'
        ├── Call AI service: POST /internal/v1/crop-diagnosis/predict
        ├── Save AIPrediction record (IMMUTABLE — never update this)
        │
        ├── IF confidence_score >= 0.65 (high/medium):
        │       ├── Find matching AdvisoryTemplate
        │       ├── Create Advisory record
        │       ├── Status → 'ai_analyzed'
        │       └── Return diagnosis + Bangla advisory ✅
        │
        └── IF confidence_score < 0.65 (low):
                ├── Status → 'escalated'
                ├── NO advisory shown (safety rule)
                └── Return: requires_expert_review=True ⚠️

EXPERT REVIEWS (if escalated)
        │
        ▼
POST /expert/cases/{id}/review
        ├── Creates NEW ExpertReview record
        ├── AIPrediction is NEVER modified (data integrity)
        ├── If expert disagrees → creates AIModelFeedback record
        └── Status → 'expert_reviewed'

FARMER GIVES FEEDBACK
        │
        ▼
POST /diagnosis-cases/{id}/feedback  ← Rating 1-5, outcome status
```

### The Confidence Threshold
- Set in `.env` as `AI_CONFIDENCE_THRESHOLD=0.65` (65%)
- **≥ 85%** → `confidence_level: "high"` — Show full advisory
- **65–84%** → `confidence_level: "medium"` — Show advisory with caution note
- **< 65%** → `confidence_level: "low"` → Escalate, no advisory (safety first!)

---

## 7. API Endpoints Reference

### Authentication (`/api/v1/auth`)
| Method | Path | Who | Description |
|---|---|---|---|
| POST | `/auth/register` | Anyone | Create account |
| POST | `/auth/login` | Anyone | Login, get tokens |
| POST | `/auth/refresh` | Token holder | Refresh access token |
| GET | `/auth/me` | Authenticated | Get own profile |
| POST | `/auth/me/profile` | Farmer/Agent | Update location & preferences |

### Farms (`/api/v1/farms`)
| Method | Path | Who | Description |
|---|---|---|---|
| POST | `/farms` | Farmer/Agent | Create a plot |
| GET | `/farms` | Farmer | List own plots |
| POST | `/farms/{id}/crop-cycles` | Farmer/Agent | Start crop cycle |
| GET | `/farms/{id}/crop-cycles` | Farmer | List crop cycles |

### Files (`/api/v1/files`)
| Method | Path | Who | Description |
|---|---|---|---|
| POST | `/files/upload-url` | Authenticated | Step 1: Get signed upload URL |
| POST | `/files/confirm-upload` | Authenticated | Step 2: Register uploaded file |
| GET | `/files/{id}/view-url` | File owner | Get signed view URL |

### Diagnosis (`/api/v1/diagnosis-cases`)
| Method | Path | Who | Description |
|---|---|---|---|
| POST | `/diagnosis-cases` | Farmer/Agent | Create draft case |
| POST | `/diagnosis-cases/{id}/images` | Farmer/Agent | Attach image |
| POST | `/diagnosis-cases/{id}/analyze` | Farmer/Agent | Trigger AI analysis |
| GET | `/diagnosis-cases/{id}` | Authenticated | Get case result |
| GET | `/diagnosis-cases` | Farmer | List case history |
| POST | `/diagnosis-cases/{id}/request-expert-review` | Farmer | Request expert |
| POST | `/diagnosis-cases/{id}/feedback` | Farmer | Submit feedback |

### Expert (`/api/v1/expert`)
| Method | Path | Who | Description |
|---|---|---|---|
| GET | `/expert/cases` | Expert/Admin | Get pending cases queue |
| POST | `/expert/cases/{id}/review` | Expert/Admin | Submit review |

### Notifications (`/api/v1/notifications`)
| Method | Path | Who | Description |
|---|---|---|---|
| GET | `/notifications` | Authenticated | List notifications (filter: unread_only) |
| POST | `/notifications/{id}/read` | Authenticated | Mark one notification as read |
| POST | `/notifications/read-all` | Authenticated | Mark all notifications as read |

> Notifications are created automatically when an expert submits a review.

---

## 8. Key Rules & Invariants (READ THESE CAREFULLY)

### 🔴 RULE 1: AI Predictions are IMMUTABLE
> `ai.predictions` records are **NEVER updated** after creation.
> Expert corrections go into `case_mgmt.expert_reviews` as new records.
> This preserves historical AI decisions for model evaluation.

### 🔴 RULE 2: Low Confidence = No Advisory
> If `confidence_score < AI_CONFIDENCE_THRESHOLD`, the advisory MUST be `null`.
> Never show unverified chemical dosages to farmers — they could cause harm.

### 🔴 RULE 3: All Farmer Messages Must Be in Bangla
> Every `message`, `message_bn`, and advisory content field shown to farmers
> must contain valid Bangla text. English is only for developer-facing messages.

### 🟡 RULE 4: AuditLog is Append-Only
> `system.audit_logs` only receives INSERT operations.
> Never UPDATE or DELETE audit log records.

### 🟡 RULE 5: Soft Deletes Only
> Users, Plots, and Cases are never hard-deleted.
> Set `is_deleted=True` and `deleted_at=now()` instead.

---

## 9. How to Add a New Feature

Follow this checklist when adding a new endpoint:

1. **Add SQL migration** in `database/migrations/` (if new table needed)
2. **Add/update ORM model** in `app/models/` — inherit from Base + mixins
3. **Register model** in `app/models/__init__.py`
4. **Add Pydantic schemas** in `app/schemas/` — one for Request, one for Response
5. **Add service method** in `app/services/` — put all business logic here
6. **Add route handler** in `app/api/v1/` — just HTTP parsing + call service
7. **Register route** in `app/api/v1/__init__.py`
8. **Write tests** in `backend/tests/`

---

## 10. Running Tests

```bash
cd backend
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

> **Note:** Integration tests require a test database. Set `DATABASE_URL` to a test DB in your environment before running.

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `Connection refused at localhost:5432` | PostgreSQL not running | Start PostgreSQL service |
| `ModuleNotFoundError: app` | Running from wrong directory | Run from `backend/` directory |
| `JWT decode error` | Secret key mismatch | Check `JWT_SECRET_KEY` in `.env` |
| `schema 'auth' does not exist` | Migrations not run | Run SQL migrations in order |
| `AI service unavailable` | ai-service/ not running | Start the AI service separately |
