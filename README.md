# VolunteerMatchAI MSE-2 Prototype

VolunteerMatchAI is a context-aware volunteer recommendation prototype. It includes a FastAPI/SQLite backend and a responsive React/Vite frontend.

## Run locally

### Backend (Python 3.11+)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (Node 18+)
```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_URL` (default `http://localhost:8000/api`). The backend uses `DATABASE_URL`, `CORS_ORIGINS`, `AI_ENABLED`, and `AI_PROVIDER`. AI is intentionally disabled by default (`AI_ENABLED=false`, `AI_PROVIDER=none`); the deterministic recommendation engine is the only active provider.

## Test
```powershell
python -m pytest -q
npm --prefix frontend run build
```

See `docs/architecture.md` for the API and module overview.
