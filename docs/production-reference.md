# MediSage — Production Reference

Quick reference for deployment, infrastructure, secrets, and ops. Written for SP5.

---

## Stack at a Glance

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.11, FastAPI, LangGraph | 2 uvicorn workers |
| Frontend | React 18, Vite, Tailwind + shadcn/ui | Served via nginx |
| LLM | Groq API — Llama 3.3 70B | Swappable via env vars only |
| Embeddings | Gemini `text-embedding-004` | RAG chatbot only |
| Database | Supabase (PostgreSQL) | Auth + reports + vector store |
| Vector store | Supabase pgvector | `document_chunks` table |
| Graph checkpointer | `AsyncPostgresSaver` (Supabase) | Swaps to Redis saver post-SP5 |
| Rate limiting | `slowapi` | 20 req/min per IP on `/patient/*` |
| Cache / rate store | Redis 7 | Railway plugin |
| Deployment | Railway | Two services: `backend`, `frontend` |
| CI/CD | GitHub Actions | test → docker build → railway deploy |

---

## Environment Variables

All vars must be set in Railway dashboard for each service. Copy structure from root `.env.example`.

### Backend

| Variable | Example value | Required |
|----------|--------------|----------|
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | ✅ |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | ✅ |
| `LLM_API_KEY` | `gsk_...` | ✅ |
| `SUPABASE_URL` | `https://xxxx.supabase.co` | ✅ |
| `SUPABASE_API_KEY` | anon key | ✅ |
| `SUPABASE_DB_URL` | `postgresql://postgres:[pw]@db.xxxx.supabase.co:5432/postgres` | ✅ |
| `GEMINI_API_KEY` | `AIza...` | ✅ (RAG embeddings) |
| `JWT_SECRET` | 32+ char random string | ✅ |
| `REDIS_URL` | `redis://localhost:6379` | ✅ (auto-set by Railway plugin) |
| `ALLOWED_ORIGINS` | `https://frontend.up.railway.app` | ✅ |
| `APP_ENV` | `production` | ✅ |

### Frontend (build-time)

| Variable | Example value | Required |
|----------|--------------|----------|
| `VITE_API_URL` | `https://backend.up.railway.app` | ✅ |

---

## Swapping the LLM Provider

Only two env vars change — no code edits needed.

| Provider | `LLM_BASE_URL` | `LLM_MODEL` |
|----------|---------------|------------|
| Groq (default) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Together.ai | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| Anthropic | `https://api.anthropic.com/v1` | `claude-haiku-4-5-20251001` |

> Anthropic uses a slightly different API format and may need a thin adapter in `backend/llm/client.py`.

---

## Docker

### Build images

```bash
docker build -t medisage-backend ./backend
docker build -t medisage-frontend ./my-app
```

### Run full local stack

```bash
cp backend/.env.example backend/.env   # fill in real values
docker compose up --build
```

| Service | Local URL |
|---------|-----------|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Redis | localhost:6379 |

### Useful compose commands

```bash
docker compose down          # stop all
docker compose down -v       # stop + wipe Redis data
docker compose logs backend  # tail backend logs
docker compose ps            # check health of each service
```

---

## Railway

### Project structure

```
MediSage (Railway project)
├── backend   (service)   FastAPI on port 8000
├── frontend  (service)   nginx on port 80
└── Redis     (plugin)    auto-injects REDIS_URL into backend
```

### Deploy manually

```bash
npm install -g @railway/cli
railway login
railway link    # link to your Railway project
railway up      # deploys all services
```

### Common commands

```bash
railway status                      # deployment status
railway logs --service backend      # tail backend logs in prod
railway variables --service backend # list set env vars
```

### Rollback

Railway Dashboard → Project → Deployments → click any past deployment → **Redeploy**.

---

## CI/CD Pipeline

File: `.github/workflows/ci.yml`

```
push to main
  └─ test      (pytest, backend unit tests)
       └─ build   (docker build backend + frontend — confirms images are valid)
            └─ deploy  (railway up --detach — only on main, not on PRs)
```

### Required GitHub secrets

Set at: GitHub repo → Settings → Secrets and variables → Actions

```
LLM_API_KEY
SUPABASE_URL
SUPABASE_API_KEY
SUPABASE_DB_URL
GEMINI_API_KEY
RAILWAY_TOKEN     ← Railway Dashboard → Account Settings → Tokens → New Token
```

---

## Health Check

```bash
# Local
curl http://localhost:8000/health

# Production
curl https://your-backend.up.railway.app/health
```

Healthy response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "env": "production",
  "checks": {
    "database": "ok",
    "llm": "ok"
  }
}
```

`"status": "degraded"` means one check failed — inspect Railway logs immediately.

---

## Rate Limiting

- **Rule:** 20 requests/minute per IP on all `/patient/*` endpoints
- **Library:** `slowapi`, via `@limiter.limit("20/minute")` decorators (the limiter is created in `backend/api/diagnosis_routes.py`, registered on `app.state.limiter` in `main.py`)
- **Storage:** **in-memory, per worker process.** Each uvicorn worker keeps its own counter, so with `--workers 2` the effective ceiling is ~40/min/IP. Redis is *pinged at startup* (`main.py` lifespan) as a readiness check and is reserved for the post-SP5 shared store; it is **not** yet the limiter backend.
- **Error response:** HTTP 429 — `{"error": "Rate limit exceeded: 20 per 1 minute"}`
- **To change the limit:** Edit the `@limiter.limit("20/minute")` decorators in `backend/api/diagnosis_routes.py`
- **To make limits shared across workers:** pass `storage_uri=settings.REDIS_URL` to `Limiter(...)`. Deferred because a Redis outage would then 500 every request unless guarded.

---

## Security Checklist

| Control | Status | Enforced by |
|---------|--------|-------------|
| No hardcoded secrets | ✅ | `.gitignore` covers `.env*` |
| CORS locked to production domain | ✅ | `ALLOWED_ORIGINS` env var in `config.py` |
| Rate limiting 20/min per IP | ✅ | `slowapi` on `/patient/*` |
| HTTPS | ✅ automatic | Railway TLS termination |
| RLS on `user_profiles` | ✅ | SP1 Supabase migration |
| RLS on `medical_reports` | ✅ | SP5 audit migration |
| Privacy policy gate | ✅ | `require_privacy_policy` FastAPI dependency |
| PHI disclaimer in UI | ✅ | Banner on diagnosis pages (SP2) |
| PII stripped from LLM prompts | ✅ | No name/email/DOB in prompt templates |
| JWT secret from env | ✅ | `JWT_SECRET` env var |

---

## Supabase Tables

| Table | RLS | Purpose |
|-------|-----|---------|
| `user_profiles` | ✅ | Auth profile, `privacy_policy_accepted`, age, gender |
| `medical_reports` | ✅ | Saved diagnosis history per user |
| `document_chunks` | ✅ | RAG vector store — 768-dim embeddings, per-user isolation |
| `checkpoints` | internal | LangGraph state checkpointer — no public access |

### Adding a migration

1. Write SQL in `backend/migrations/00N_description.sql`
2. Run in Supabase Dashboard → SQL Editor
3. Commit: `git add backend/migrations/ && git commit -m "chore: migration 00N"`

Migrations are applied manually. The file serves as the audit trail.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `/health` degraded on `llm` | Bad or missing `LLM_API_KEY` | Verify key in Railway vars; check status.groq.com |
| `/health` degraded on `database` | Wrong `SUPABASE_DB_URL` | Verify connection string includes the DB password |
| Every request gets 429 | Redis down, in-memory limit hit fast | Check Redis plugin health in Railway dashboard |
| Frontend blank page | `VITE_API_URL` missing or wrong | Set correct backend URL in Railway frontend vars |
| CORS error in browser | `ALLOWED_ORIGINS` trailing slash or wrong URL | Must match exactly: `https://x.railway.app` (no trailing `/`) |
| Docker image > 500MB | torch/CUDA re-introduced | `grep -i torch backend/requirements.txt` |
| LangGraph checkpoint errors | `SUPABASE_DB_URL` missing | Required for `AsyncPostgresSaver` — must be the direct Postgres URL, not the REST URL |
| CI deploy fails | Stale `RAILWAY_TOKEN` | Regenerate in Railway → Account → Tokens |

---

## SP5 Build Process & Verification Log

This is the record of how production hardening was actually executed against the
`feature/sp2-langgraph-rag` branch, in order, with the verification evidence for
each piece. Use it to re-run or audit any step.

### What was built (code, committed)

| # | Area | Files touched | Outcome |
|---|------|---------------|---------|
| 1–2 | Docker images | `backend/Dockerfile`, `backend/.dockerignore`, `my-app/Dockerfile`, `my-app/.dockerignore`, `my-app/nginx.conf` | Python 3.11-slim backend (no CUDA); Vite→nginx frontend with SPA fallback + `/health` |
| 3 | Local stack | `docker-compose.yml` | 3 services: backend, frontend, Redis 7. Root `.env.example` **skipped** — repo `.env` is already provisioned. |
| 4 | Config | `backend/config.py` | Added `REDIS_URL`, `ALLOWED_ORIGINS` (comma-split list), `APP_ENV` |
| 4 | Deps | `backend/requirements.txt` | Added `slowapi`, `redis` (asyncio is built into redis-py ≥4.2, so the `[asyncio]` extra was dropped to avoid a pip warning) |
| 4 | Rate limit | `backend/api/diagnosis_routes.py` | `Limiter(key_func=get_remote_address)` + `@limiter.limit("20/minute")` on the 4 `/patient/*` routes |
| 4 | App wiring | `backend/main.py` | Registered limiter + `RateLimitExceeded` handler; CORS now reads `settings.ALLOWED_ORIGINS`; Redis ping in lifespan |
| 5 | Logging | `main.py`, `api/auth_routes.py`, `nodes/*.py` | All `print()` in application code → `logging`; JSON log format when `APP_ENV=production`; raw user-symptom dump downgraded to `debug` (PHI) |
| 7 | Health | `backend/api/diagnosis_routes.py` | `/health` now probes Supabase + LLM, returns `degraded` (still HTTP 200) on failure |
| 8 | CI/CD | `.github/workflows/ci.yml` | `test → docker build → deploy` (deploy only on push to `main`) |
| 9 | Deploy cfg | `railway.toml` | Two-service Dockerfile build config with health checks |
| — | Tests | `backend/tests/test_diagnosis_routes.py` | Replaced the old `/health` test with two covering the new healthy/degraded contract |

### Deliberate decisions (why it isn't exactly "by the book")

- **In-memory limiter, not Redis-backed.** See [Rate Limiting](#rate-limiting). Keeps bare-metal dev (no Redis) from 500-ing; Redis stays a startup readiness signal until the shared store lands post-SP5.
- **`backend/test/*.py` left untouched.** Those are standalone GPU/llama-cpp benchmark scratch scripts (pre-SP1), not the pytest suite (`backend/tests/`) and not served code. Converting their `print()`s was out of scope.
- **Root `.env.example` not created.** The repo `.env` is already set; `docker-compose.yml` reads `./backend/.env` directly.

### Verification evidence (all green)

```bash
# Test suite
cd backend && python -m pytest tests/ -q
# → 29 passed

# Rate limit (in-process ASGI, 22 calls to /patient/textual_analysis)
# → 200 ×20, then 429 on request 21 ✓

# Security greps (all empty)
grep -rnE "gsk_|sk-[A-Za-z0-9]|AIza|eyJ" backend --include="*.py" | grep -v os.getenv   # secrets
grep -rnE "f\"(SELECT|INSERT|UPDATE|DELETE)" backend --include="*.py"                    # raw SQL
grep -rn "print(" backend/api backend/nodes backend/main.py                              # app-code prints

# .gitignore covers .env / .env.* ✓
```

### Remaining MANUAL steps (cannot be automated from the repo)

These require dashboard/account access and are **not done by the code above**:

1. **Supabase RLS audit** (Task 6, Step 3) — in the Supabase dashboard confirm RLS is
   ON for `user_profiles`, `medical_reports`, `document_chunks`, and that the LangGraph
   `checkpoints` tables have no public/anon access. Add the `medical_reports` policy if missing:
   ```sql
   ALTER TABLE medical_reports ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "Users can manage own reports"
       ON medical_reports USING (auth.uid() = user_id);
   ```
2. **GitHub Actions secrets** — repo → Settings → Secrets and variables → Actions:
   `LLM_API_KEY`, `SUPABASE_URL`, `SUPABASE_API_KEY`, `SUPABASE_DB_URL`, `GEMINI_API_KEY`, `RAILWAY_TOKEN`.
3. **Railway project setup** — create the project, add the **Redis plugin** (auto-injects
   `REDIS_URL`), set `ALLOWED_ORIGINS` / `APP_ENV=production` on the backend service and
   `VITE_API_URL` on the frontend service, then `railway up` (or let CI deploy on merge to `main`).
4. **Production smoke test** — `curl https://<backend>.up.railway.app/health` should return
   `{"status":"healthy","checks":{"database":"ok","llm":"ok"}}`; load the frontend URL and run
   one diagnosis end-to-end.

---

## First-Time Railway Deploy — Step-by-Step Runbook

One-time setup. After this, merges to `main` auto-deploy via GitHub Actions. MediSage is a
monorepo with **two services** (`backend/`, `my-app/`), so the reliable path is the **dashboard**
— Railway provisions one service per Dockerfile and you point each at its subdirectory. The
committed `railway.toml` is a reference for the build/healthcheck settings, not a full
multi-service auto-provisioner.

### Step 0 — Prerequisites
- A [railway.app](https://railway.app) account (sign in with GitHub — makes repo deploys one click).
- Railway's free trial / hobby plan is enough to start. Redis + 2 services fit the hobby tier.
- Your backend secrets handy (the same values from `backend/.env`).

### Step 1 — Create the project
**Dashboard (recommended):**
1. railway.app → **New Project**.
2. Choose **Deploy from GitHub repo** → authorize Railway → pick the `MediSage` repo.
3. When it asks what to deploy, Railway will try to build the repo root — that's fine, we'll
   fix the service to target `backend/` in Step 2. Name this first service **`backend`**.

**CLI (alternative):**
```bash
npm install -g @railway/cli
railway login                 # opens browser
cd c:/Users/user/Desktop/MediSage
railway init                  # creates a new project, prompts for a name
```

### Step 2 — Configure the **backend** service
In the service → **Settings**:
- **Source Repo:** `MediSage`, branch `main` (or your deploy branch).
- **Root Directory:** `backend`
- **Build:** Dockerfile (Railway auto-detects `backend/Dockerfile`). If asked for a path, use `backend/Dockerfile`.
- **Deploy → Healthcheck Path:** `/health`, timeout `30`.
- **Networking → Generate Domain** → gives you `https://<backend>.up.railway.app`. **Copy this URL.**

### Step 3 — Add the **frontend** service
1. In the same project → **+ New** → **GitHub Repo** → same `MediSage` repo (or **Empty Service** then set the source).
2. Service → **Settings**:
   - **Root Directory:** `my-app`
   - **Build:** Dockerfile (`my-app/Dockerfile`)
   - **Deploy → Healthcheck Path:** `/health`, timeout `10`
   - **Networking → Generate Domain** → gives you `https://<frontend>.up.railway.app`. **Copy this URL.**

### Step 4 — Add Redis
- Project canvas → **+ New** → **Database** → **Add Redis**.
- Railway auto-injects **`REDIS_URL`** into services in the same project. Confirm it appears in the
  backend service's Variables (if not, add a reference variable `REDIS_URL = ${{Redis.REDIS_URL}}`).

### Step 5 — Set environment variables
Backend service → **Variables** (paste the real values from `backend/.env`):
```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_API_KEY=...            # anon key
SUPABASE_DB_URL=postgresql://postgres:[pw]@db.xxxx.supabase.co:5432/postgres
GEMINI_API_KEY=AIza...
JWT_SECRET=...                  # 32+ chars
APP_ENV=production
ALLOWED_ORIGINS=https://<frontend>.up.railway.app    # from Step 3, NO trailing slash
# REDIS_URL is injected by the Redis plugin — don't set it by hand
```
Frontend service → **Variables**:
```
VITE_API_URL=https://<backend>.up.railway.app        # from Step 2
```
> **Chicken-and-egg:** `ALLOWED_ORIGINS` and `VITE_API_URL` need the *other* service's URL, which
> only exists after a domain is generated. If you generated both domains in Steps 2–3 you can fill
> them now. `VITE_API_URL` is **build-time** (Vite bakes it into the bundle), so after setting it
> the frontend must **rebuild/redeploy** to take effect.

### Step 6 — Deploy
- Dashboard: each service deploys automatically on save; use **Deploy** / **Redeploy** to force one.
- Choose GitHub Repository.

That's the entry that connects Railway to your MediSage repo and builds from your committed Dockerfiles. Here's the flow after you click it:

1. **GitHub Repository** → authorize Railway (if first time) → pick MediSage.
2. Railway creates a service and starts trying to build from the repo root. That first service will be your backend — go into its **Settings** and set **Root Directory** = backend so it uses backend/Dockerfile (not the repo root).
3. Then add the **second service** for the frontend: + **New → GitHub Repo → same MediSage**, and set its Root Directory = my-app.
4. Add Redis separately: + New → Database → Add Redis.
   
Why not the others:
- **Database** → only provisions Redis/Postgres, not your app.
- **Docker Image** → for a prebuilt image in a registry; yours builds from source via the Dockerfile, so skip it.
- **Template / Function / Bucket / Empty Project** → not your case. (Empty Project would work but then you'd manually attach the GitHub source anyway — GitHub Repository does that in one step.)
  
Ignore the two AI suggestions at the top ("Create to-do list…", "Deploy Redis, Postgres, and a Bucket") — those are unrelated starters.

This maps to Steps 1–2 of the runbook in docs/production-reference.md.
- CLI: `railway up` (deploys the linked service).

### Step 7 — Smoke test
```bash
curl https://<backend>.up.railway.app/health
# expect: {"status":"healthy","checks":{"database":"ok","llm":"ok"}}
```
Then open `https://<frontend>.up.railway.app`, log in, and run one diagnosis end-to-end. If the
browser shows a CORS error, re-check `ALLOWED_ORIGINS` matches the frontend URL exactly (no trailing `/`).

### Step 8 — Wire up CI auto-deploy (optional but recommended)
So pushes to `main` deploy without the CLI:
1. Railway → **Account Settings → Tokens → Create Token** (or a project token). Copy it.
2. GitHub repo → **Settings → Secrets and variables → Actions** → add `RAILWAY_TOKEN` (plus the
   other secrets listed in [CI/CD Pipeline](#cicd-pipeline)).
3. The `deploy` job in `.github/workflows/ci.yml` runs `railway up --detach` on every push to `main`.

> The CI `deploy` job deploys the **linked** service. For two services you can either run two
> `railway up --service <name>` steps, or rely on Railway's native GitHub integration (Steps 2–3
> already auto-deploy each service on push) and treat the CI deploy job as a backstop.

### Rollback
Railway Dashboard → service → **Deployments** → pick a previous green deploy → **Redeploy**.