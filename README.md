# MediSage

An AI medical-diagnosis assistant. Patients describe symptoms in plain language and MediSage runs a guided clinical workflow — initial analysis, adaptive follow-up questions, an overall assessment, and a structured medical report — backed by a retrieval-augmented chatbot that answers questions grounded in the patient's own saved reports.

> [!WARNING]
> **Not a medical device.** MediSage is decision-support and educational software, not a substitute for professional medical advice, diagnosis, or treatment. It surfaces possibilities and routes emergencies to "seek immediate care" — it does not make clinical decisions. Always consult a qualified clinician.

---

## Screenshots

| Home | Diagnosis intake |
|------|------------------|
| ![Home page](assets/screenshots/home.png) | ![Diagnosis intake form](assets/screenshots/diagnosis-form.png) |

| Analysis & follow-up questions | Final medical report |
|--------------------------------|----------------------|
| ![Analysis and follow-up questions](assets/screenshots/analysis.png) | ![Final medical report](assets/screenshots/report.png) |

| RAG chatbot |
|-------------|
| ![RAG chatbot grounded in saved reports](assets/screenshots/chatbot.png) |

<!-- TODO: capture and add the screenshots above (recommended width ~1200px). -->

---

## How it works

The backend is a [LangGraph](https://langchain-ai.github.io/langgraph/) state machine. Each stage is a node; routing between them is driven by confidence scores and the patient's answers, and graph state is checkpointed to Postgres so a session can pause for user input and resume cleanly.

```
symptoms ─▶ textual analysis ─▶ follow-up questions ─▶ overall analysis ─▶ medical report
                                   (adaptive, optional)        │
                                                               ▼
                          RAG chatbot  ◀──  saved reports ingested into pgvector
```

- **Textual analysis** — differential diagnosis with confidence scoring from a symptom description.
- **Follow-up questions** — LLM-generated, symptom-specific clarifying questions that re-rank the differential.
- **Overall analysis** — synthesises symptoms + answers, applies a critical-condition floor, and redirects emergencies.
- **Medical report** — a structured, layman-readable summary, exportable to PDF or Word.
- **RAG chatbot** — each saved report is chunked and embedded into pgvector; the chatbot answers follow-up questions grounded only in that patient's documents.

## Tech stack

| Layer | Choice |
|-------|--------|
| API | Python 3.11, FastAPI, LangGraph |
| LLM | Groq — Llama 3.3 70B (OpenAI-compatible; swappable by env var) |
| Embeddings | Gemini `text-embedding-004` |
| Database | Supabase (PostgreSQL) — auth, reports, and pgvector store |
| State | `AsyncPostgresSaver` checkpointer |
| Frontend | React 18, Vite, Tailwind CSS + shadcn/ui |
| Rate limiting | `slowapi` — 20 req/min per IP on `/patient/*` |
| Auth | JWT (HTTP-only cookie) + a privacy-policy gate |
| Deploy | Docker, Railway, GitHub Actions CI/CD |

## Quick start

The whole stack runs from one command with Docker.

```bash
git clone https://github.com/Jwongjs/MediSage.git
cd MediSage

cp backend/.env.example backend/.env   # fill in your keys (see below)
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### Required environment variables

Set these in `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `LLM_API_KEY` | Groq API key (`gsk_...`) |
| `LLM_BASE_URL` / `LLM_MODEL` | LLM endpoint + model (defaults to Groq + Llama 3.3 70B) |
| `SUPABASE_URL` / `SUPABASE_API_KEY` | Supabase project + anon key |
| `SUPABASE_DB_URL` | Direct Postgres URL (required by the checkpointer) |
| `GEMINI_API_KEY` | RAG embeddings |
| `JWT_SECRET` | 32+ char secret for auth cookies |
| `REDIS_URL` | Redis (auto-set in Docker / Railway) |
| `ALLOWED_ORIGINS` / `APP_ENV` | CORS origins + environment |

### Running without Docker

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload   # :8000

# Frontend
cd my-app && npm install && npm run dev                                       # :5173
```

## Project structure

```
MediSage/
├── backend/                 FastAPI + LangGraph
│   ├── api/                 auth, diagnosis, and chat routes
│   ├── graphs/              patient_workflow + rag_chatbot graphs
│   ├── nodes/               workflow node implementations
│   ├── rag/                 Gemini embedder + pgvector retriever
│   ├── llm/                 LLM client (Groq / OpenAI-compatible)
│   ├── schemas/             Pydantic models
│   ├── tests/               pytest suite
│   ├── config.py · main.py
│   └── Dockerfile
├── my-app/                  React + Vite frontend
│   ├── src/                 views, pages, components, hooks
│   ├── e2e/                 Playwright specs
│   ├── Dockerfile · nginx.conf
├── docker-compose.yml       backend + frontend + Redis
├── railway.toml             deploy config
└── .github/workflows/ci.yml test → build → deploy
```

## Testing

```bash
cd backend && python -m pytest tests/    # API + workflow unit tests
cd my-app  && npx playwright test        # end-to-end flows
```

## Deployment

Two Docker images (FastAPI backend, nginx-served frontend build) deploy to **Railway** with **Redis** as a managed plugin. GitHub Actions runs `test → docker build → deploy` on every push to `main`; CORS, rate limiting, and structured JSON logging activate when `APP_ENV=production`. The `/health` endpoint actively probes the database and LLM and reports `degraded` if either is unreachable.

## Security & privacy

- CORS locked to `ALLOWED_ORIGINS`; HTTPS terminated by the platform.
- Per-IP rate limiting on patient endpoints.
- Supabase Row-Level Security isolates each user's profile, reports, and vector chunks.
- No secrets in source; a privacy-policy gate guards diagnosis endpoints; PII is kept out of LLM prompts.

## License

See [LICENSE](LICENSE).
