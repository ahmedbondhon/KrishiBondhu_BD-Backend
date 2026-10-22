# KrishiBondhu_BD-Backend
## Project Structure

```text
project-backend/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── workers/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── ai-service/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── preprocessing/
│   │   ├── inference/
│   │   └── main.py
│   │
│   ├── model_artifacts/
│   ├── tests/
│   └── requirements.txt
│
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── schema/
│
├── docs/
│
├── infrastructure/
│   ├── github-actions/
│   └── deployment/
│
├── README.md
└── .env
```

## Local frontend integration

Run the API from the repository root with the backend on port `8000`:

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The development demo is available at <http://localhost:8000/demo> when
`DEBUG=true` and `SMS_MODE=simulator`. The demo HTML is tracked in
[`demo/frontend_demo.html`](demo/frontend_demo.html), so it is available after
clone/push and does not depend on an untracked local file.

For a separate frontend (React, Next.js, or similar), set its API base URL to
`http://localhost:8000` (the demo uses `window.KRISHIBONDHU_API_URL` for this).
Add the frontend origin to `CORS_ALLOWED_ORIGINS`, for example:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

In production, set `DEBUG=false`, use real SMS configuration, and replace the
development CORS origins with the deployed frontend URL. Never enable
`OTP_DEMO_MODE` or `SMS_MODE=simulator` in production.
