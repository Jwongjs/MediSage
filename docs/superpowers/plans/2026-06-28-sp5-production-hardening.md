# SP5: Production Hardening — Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make MediSage deployable, observable, and secure for real traffic. Docker containers for backend + frontend, Railway deployment with GitHub Actions CI/CD, Redis for rate limiting, security audit of all endpoints, and structured logging.

**Architecture:** Two Docker images (backend: Python/FastAPI, frontend: Vite build → nginx). A `docker-compose.yml` for local dev. Railway deploys both services from the same repo. Redis added as a Railway plugin for rate limiting with `slowapi`. GitHub Actions pipeline: lint → test → docker build → deploy on merge to `main`. CORS locked to production domain via env var.

**Tech Stack:** Python 3.11, FastAPI, `slowapi`, `redis[asyncio]`, Docker 24+, nginx, Railway, GitHub Actions, Vite.

**Prerequisites:** SP1 ✅ (no CUDA), SP2 ✅ (AsyncPostgresSaver — stable graph), SP4 ✅ (Vite build works).

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `backend/Dockerfile` | Production Python image |
| Create | `my-app/Dockerfile` | Vite build → nginx |
| Create | `my-app/nginx.conf` | nginx SPA routing config |
| Create | `docker-compose.yml` | Local dev: backend + frontend + Redis |
| Create | `.env.example` (root) | All env vars documented |
| Create | `.github/workflows/ci.yml` | Test → build → deploy pipeline |
| Create | `railway.toml` | Railway multi-service config |
| Modify | `backend/main.py` | Lock CORS to env var, add Redis ping to health |
| Modify | `backend/api/diagnosis_routes.py` | Add slowapi rate limiter on `/patient/*`, upgrade health check |
| Modify | `backend/config.py` | Add REDIS_URL, ALLOWED_ORIGINS, APP_ENV |
| Modify | `backend/requirements.txt` | Add slowapi, redis |
| Audit  | All backend files | Replace print() with logging, verify no raw SQL, no hardcoded secrets |

---

## Task 1: Backend Dockerfile

**File:** `backend/Dockerfile`

- [ ] **Step 1: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

- [ ] **Step 2: Create `backend/.dockerignore`**

```
__pycache__/
*.pyc
.env
.env.*
!.env.example
migrations/
tests/
*.md
```

- [ ] **Step 3: Build and verify (under 500MB, no torch)**

```bash
cd c:/Users/user/Desktop/MediSage/backend
docker build -t medisage-backend:test .
docker images medisage-backend:test
docker run --rm medisage-backend:test python -c "import torch" 2>&1 || echo "torch not present — correct"
```

- [ ] **Step 4: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore
git commit -m "feat(sp5): backend Dockerfile — Python 3.11-slim, no CUDA"
```

---

## Task 2: Frontend Dockerfile + nginx

**Files:** `my-app/Dockerfile`, `my-app/nginx.conf`

- [ ] **Step 1: Create `my-app/nginx.conf`**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
```

- [ ] **Step 2: Create `my-app/Dockerfile`**

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 3: Create `my-app/.dockerignore`**

```
node_modules/
.env
.env.*
!.env.example
dist/
```

- [ ] **Step 4: Build and smoke-test**

```bash
cd c:/Users/user/Desktop/MediSage/my-app
docker build -t medisage-frontend:test .
docker run --rm -d -p 3001:80 --name fe-test medisage-frontend:test
curl http://localhost:3001/health
docker stop fe-test
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add my-app/Dockerfile my-app/.dockerignore my-app/nginx.conf
git commit -m "feat(sp5): frontend Dockerfile — Vite build + nginx SPA"
```

---

## Task 3: docker-compose for local dev

**File:** `docker-compose.yml` (repo root)

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./my-app
    ports:
      - "3000:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

- [ ] **Step 2: Create root `.env.example`**

```env
# ── LLM Provider ──────────────────────────────────────────────────────────────
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_your_key_here

# ── Supabase ───────────────────────────────────────────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres

# ── Gemini (RAG embeddings) ────────────────────────────────────────────────────
GEMINI_API_KEY=your-gemini-key

# ── JWT ────────────────────────────────────────────────────────────────────────
JWT_SECRET=your-jwt-secret-min-32-chars

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379

# ── App ────────────────────────────────────────────────────────────────────────
APP_ENV=development
ALLOWED_ORIGINS=http://localhost:3000
```

- [ ] **Step 3: Test full local stack**

```bash
cd c:/Users/user/Desktop/MediSage
docker compose up --build
```

Expected: three services start, `http://localhost:3000` loads, `http://localhost:8000/health` returns healthy.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat(sp5): docker-compose for local dev — backend + frontend + Redis"
```

---

## Task 4: Rate Limiting + CORS + Config

**Files:** `backend/requirements.txt`, `backend/config.py`, `backend/api/diagnosis_routes.py`, `backend/main.py`

- [ ] **Step 1: Add to `requirements.txt`**

```
slowapi
redis[asyncio]
```

- [ ] **Step 2: Update `backend/config.py`**

```python
import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()
```

- [ ] **Step 3: Add rate limiter to `diagnosis_routes.py`**

After existing imports, add:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Add `@limiter.limit("20/minute")` to all four patient routes. Each route must have `request: Request` as its first parameter for slowapi to function:

```python
@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
@limiter.limit("20/minute")
async def run_textual_analysis(request: Request, user_symptoms: str = Form(...), ...):
```

Apply the same to `followup_questions`, `overall_analysis`, `medical_report`.

- [ ] **Step 4: Register limiter + lock CORS + Redis ping in `main.py`**

Add imports:
```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
```

After `app = FastAPI(...)`:
```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Replace hardcoded CORS origins:
```python
allow_origins=settings.ALLOWED_ORIGINS,
```

In lifespan, after LLM ping, add Redis check:
```python
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        logger.info(f"Redis connected")
    except Exception as e:
        logger.warning(f"Redis ping failed: {e} — rate limiting uses in-memory fallback")
```

- [ ] **Step 5: Verify 429 is returned at limit**

```bash
for i in $(seq 1 22); do
  curl -s -o /dev/null -w "Request $i: %{http_code}\n" \
    -X POST http://localhost:8000/patient/textual_analysis \
    -F "user_symptoms=test"
done
```

Expected: request 21 or 22 returns 429.

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/config.py backend/api/diagnosis_routes.py backend/main.py
git commit -m "feat(sp5): rate limiting 20/min, CORS from env, Redis ping at startup"
```

---

## Task 5: Logging Audit

**Files:** All `backend/` Python files

- [ ] **Step 1: Find all print() calls in non-main files**

```bash
grep -rn "print(" c:/Users/user/Desktop/MediSage/backend --include="*.py" | grep -v "__pycache__" | grep -v "main.py"
```

- [ ] **Step 2: Replace each with structured logging**

Ensure every file that logs has at the top:
```python
import logging
logger = logging.getLogger(__name__)
```

Replace: `print("✅ ...")` → `logger.info("...")`  
Replace: `print("⚠️  ...")` → `logger.warning("...")`  
Replace: `print("❌ ...")` → `logger.error("...")`

Remove emoji from non-startup log lines.

- [ ] **Step 3: Add JSON log format for production in `main.py`**

Replace existing `logging.basicConfig`:
```python
if settings.APP_ENV == "production":
    logging.basicConfig(
        level=logging.INFO,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)r}',
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
```

- [ ] **Step 4: Confirm clean**

```bash
grep -rn "print(" c:/Users/user/Desktop/MediSage/backend --include="*.py" | grep -v "__pycache__" | grep -v "main.py"
```

Expected: no results.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "chore(sp5): replace print() with structured logging; JSON format in production"
```

---

## Task 6: Security Audit

- [ ] **Step 1: Scan for hardcoded secrets**

```bash
grep -rn "gsk_\|sk-\|AIza\|eyJ" c:/Users/user/Desktop/MediSage/backend --include="*.py" | grep -v "__pycache__"
grep -rn "API_KEY\s*=\s*['\"]" c:/Users/user/Desktop/MediSage/backend --include="*.py" | grep -v "os.getenv"
```

Expected: no results. If any found, move immediately to `.env`.

- [ ] **Step 2: Scan for raw SQL f-strings**

```bash
grep -rn "f\"SELECT\|f\"INSERT\|f\"UPDATE\|f\"DELETE\|f'SELECT\|f'INSERT" \
  c:/Users/user/Desktop/MediSage/backend --include="*.py" | grep -v "__pycache__"
```

Expected: no results. All DB calls use the Supabase client (parameterised).

- [ ] **Step 3: Audit Supabase RLS in dashboard**

In Supabase Dashboard → Table Editor → each table → RLS:
- `user_profiles` — ✅ RLS on, 4 policies (from SP1 migration)
- `medical_reports` — verify; if missing:

```sql
ALTER TABLE medical_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own reports"
    ON medical_reports USING (auth.uid() = user_id);
```

- LangGraph checkpoint tables — verify no public anon access.

- [ ] **Step 4: Confirm .gitignore**

```bash
grep "\.env" c:/Users/user/Desktop/MediSage/.gitignore
```

Expected: `.env` and `.env.*` listed. If not:
```
.env
.env.*
!.env.example
```

- [ ] **Step 5: Commit migrations if any were added**

```bash
git add backend/migrations/ .gitignore
git commit -m "chore(sp5): RLS policies, .gitignore hardening"
```

---

## Task 7: Health Check Upgrade

**File:** `backend/api/diagnosis_routes.py`

Replace the existing `/health` route with one that actively probes DB and LLM:

- [ ] **Step 1: Replace health_check**

```python
@diagnosis_router.get("/health")
async def health_check():
    from datetime import datetime
    health = {
        "status": "healthy",
        "version": "2.0.0",
        "env": settings.APP_ENV,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    try:
        from api.auth_routes import supabase
        supabase.table("user_profiles").select("id").limit(1).execute()
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {e}"
        health["status"] = "degraded"

    try:
        from llm.client import llm_client
        await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
        health["checks"]["llm"] = "ok"
    except Exception as e:
        health["checks"]["llm"] = f"error: {e}"
        health["status"] = "degraded"

    return health
```

- [ ] **Step 2: Verify**

```bash
curl http://localhost:8000/health | python -m json.tool
```

Expected: `{"status": "healthy", "checks": {"database": "ok", "llm": "ok"}}`

- [ ] **Step 3: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp5): health endpoint probes DB + LLM, returns degraded on failure"
```

---

## Task 8: GitHub Actions CI/CD

**File:** `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Backend Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_BASE_URL: https://api.groq.com/openai/v1
          LLM_MODEL: llama-3.3-70b-versatile
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY }}
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          JWT_SECRET: test-secret-for-ci
          REDIS_URL: redis://localhost:6379
          APP_ENV: test
        run: python -m pytest tests/ -v

  build:
    name: Docker Build Check
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t medisage-backend ./backend

      - name: Build frontend image
        run: docker build -t medisage-frontend ./my-app

  deploy:
    name: Deploy to Railway
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --detach
```

- [ ] **Step 2: Add secrets to GitHub repo**

GitHub → repo → Settings → Secrets → Actions → New repository secret:
- `LLM_API_KEY`, `SUPABASE_URL`, `SUPABASE_API_KEY`, `SUPABASE_DB_URL`, `GEMINI_API_KEY`, `RAILWAY_TOKEN`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "feat(sp5): GitHub Actions — test → docker build → deploy to Railway"
```

---

## Task 9: Railway Deployment

**File:** `railway.toml`

- [ ] **Step 1: Create `railway.toml`**

```toml
[build]
builder = "DOCKERFILE"

[[services]]
name = "backend"
source = "backend"
dockerfilePath = "backend/Dockerfile"

[services.deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "frontend"
source = "my-app"
dockerfilePath = "my-app/Dockerfile"

[services.deploy]
healthcheckPath = "/health"
healthcheckTimeout = 10
```

- [ ] **Step 2: Set env vars in Railway dashboard**

Backend service → Variables: all vars from `.env.example` plus:
- `ALLOWED_ORIGINS` = `https://your-frontend.railway.app`
- `APP_ENV` = `production`
- `REDIS_URL` = auto-set by Railway Redis plugin

Frontend service → Variables:
- `VITE_API_URL` = `https://your-backend.railway.app`

- [ ] **Step 3: Add Redis plugin**

Railway Dashboard → Project → + New → Database → Redis. Railway automatically injects `REDIS_URL` into backend.

- [ ] **Step 4: First deploy**

```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

- [ ] **Step 5: Smoke test**

```bash
curl https://your-backend.railway.app/health
```

Expected: `{"status": "healthy", "checks": {"database": "ok", "llm": "ok"}}`

- [ ] **Step 6: Commit**

```bash
git add railway.toml
git commit -m "feat(sp5): Railway multi-service deploy config"
```

---

## Task 10: Final Verification

- [ ] `docker compose up --build` starts from scratch with no manual steps
- [ ] Rate limit: 21st request in 1 minute to `/patient/*` returns 429
- [ ] `grep -r "gsk_\|sk-\|AIza"` finds no secrets in tracked files
- [ ] Push to `main` → GitHub Actions goes green (test → build → deploy)
- [ ] `https://your-backend.railway.app/health` returns `{"status": "healthy"}`
- [ ] Frontend loads at Railway URL, login works, diagnosis completes end-to-end

```bash
git add .
git commit -m "feat(sp5): complete — Docker, Railway, CI/CD, rate limiting, security hardened"
```

---

## Spec Coverage Checklist

| Requirement | Task |
|-------------|------|
| `backend/Dockerfile` < 500MB, no CUDA | 1 |
| `my-app/Dockerfile` — Vite → nginx, SPA routing | 2 |
| `docker-compose.yml` — 3-service local dev | 3 |
| Root `.env.example` all vars documented | 3 |
| slowapi 20/min per IP on `/patient/*` | 4 |
| CORS locked to `ALLOWED_ORIGINS` env var | 4 |
| Redis ping at startup | 4 |
| print() → logging across backend | 5 |
| JSON log format in production | 5 |
| No hardcoded secrets | 6 |
| No raw SQL f-strings | 6 |
| RLS on all Supabase tables | 6 |
| Health endpoint probes DB + LLM | 7 |
| GitHub Actions test → build → deploy | 8 |
| Secrets in GitHub Actions, not in code | 8 |
| `railway.toml` multi-service config | 9 |
| Redis plugin via Railway | 9 |
| Production smoke test passes | 10 |
