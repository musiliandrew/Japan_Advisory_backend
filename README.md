# Japan Advisory Backend (FastAPI)

FastAPI ML backend for Japan -> Kenya import decisioning.

## What this API does

- Reads inventory from Neon Postgres (`public.car_listings`).
- Normalizes listing fields (mileage/engine/fuel/transmission/body/drive/source).
- Runs model + cost engine + ROI pipeline.
- Serves dashboard and vehicle search payloads to frontend.
- Uses live USD/KES exchange rates from online providers (with cache/fallback).

  <img width="1920" height="1818" alt="image" src="https://github.com/user-attachments/assets/5c846a43-e1a2-42e6-afda-9be15630c58c" />


## Tech stack

- FastAPI
- SQLAlchemy + psycopg
- CatBoost model inference
- Neon PostgreSQL

## Setup

```bash
cd Advisory_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Required environment

Set at minimum:

- `DATABASE_URL` (must use `postgresql+psycopg://...`)
- `CORS_ORIGINS`

Example:

```env
DATABASE_URL=postgresql+psycopg://user:pass@host/db?sslmode=require
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Core endpoints

- `GET /health`
- `GET /fx-rate`
- `GET /vehicles` (supports pagination/filter/sort)
- `GET /dashboard-data`
- `POST /predict-price`
- `POST /import-cost`
- `POST /roi-analysis`
- `POST /full-analysis`

## Notes

- Live FX sources: exchangerate.host (primary), open.er-api.com (fallback).
- Inventory processing is cached and limited by `INVENTORY_MAX_ROWS` for predictable performance.
- If model input shape mismatches, backend falls back to baseline prediction instead of crashing.
