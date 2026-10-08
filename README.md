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