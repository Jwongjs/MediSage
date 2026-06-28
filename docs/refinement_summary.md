# MediSage — Production Refactor: SP1–SP5 Summary

Quick-reference guide for all five sub-projects. Each section covers what changed, why, and the key files involved.

---

## SP1 — API Model Migration ✅ Complete

**What:** Replaced every local model with cloud API calls so the app runs without GPU hardware.

**Why:** Local Llama 3.1-8B GGUF + EfficientNet skin classifier made the app impossible to containerise, scale, or run on standard servers. The classifier was also clinically unsafe (binary output, not validated).

### Key changes

| Change | Detail |
|--------|--------|
| Llama 3.1-8B GGUF → Groq API | Model: `llama-3.3-70b-versatile`. Provider abstracted so it can swap to Claude Haiku or GPT-4o mini via `LLM_PROVIDER` env var. |
| EfficientNet removed entirely | `image_classification_node.py` deleted. Image upload UI removed. Not clinically safe. |
| `model_manager.py` deleted | Loaded local GGUF and EfficientNet. Replaced by `backend/adapters/llm_client.py`. |
| `websocket_manager.py` deleted | WebSocket code was commented out; removed dead infrastructure. |
| Privacy policy gate | Users must accept ToS/Privacy Policy before first use. Stored in `user_profiles.privacy_policy_accepted`. |
| PII stripping | Name/email/DOB never included in the same LLM API payload as symptoms. |

### Key files

- `backend/adapters/llm_client.py` — unified provider interface (Groq/Claude/OpenAI via config)
- `backend/migrations/001_privacy_policy.sql` — `user_profiles` table, RLS policies
- `my-app/src/components/medical/PrivacyPolicyModal.tsx` — frontend gate

### Docker target

`docker build` produces an image with no CUDA dependency, under 500 MB.

---

## SP2 — LangGraph Refactor + Agentic RAG Chatbot ✅ Complete

**What:** Eliminated manual routing middleware and added an agentic RAG chatbot that answers questions from the user's diagnostic history.

**Why:** `workflow_state_manager.py` was a parallel manual router sitting alongside LangGraph, duplicating routing logic outside the graph. That's a maintenance nightmare. The RAG chatbot lets users interrogate their past reports without re-running diagnostics.

### Part A — Diagnostic Workflow Consolidation

| Change | Detail |
|--------|--------|
| `workflow_state_manager.py` deleted | All routing now lives in `patient_workflow.py` as two pure functions: `_route_after_diagnosis` and `_route_after_followup`. |
| `AsyncPostgresSaver` checkpointer | LangGraph state persisted to Supabase PostgreSQL. Compiled at startup, stored in `app.state.patient_graph`. Scales across multiple Uvicorn workers. |
| `interrupt_before` pattern | Graph pauses before follow-up and analysis nodes, waiting for user input. Frontend resumes via `POST /patient/followup-questions` etc. |
| Session-based resumption | Client sends only `session_id`. No more `previous_state` in request bodies. |

Routing logic in plain English:
- After `llm_diagnosis` → go to `generate_followup_questions` (if follow-up needed) or `overall_analysis` (if done)
- After `process_followup_responses` → loop back to `generate_followup_questions` (more questions) or forward to `overall_analysis` (done)

### Part B — Agentic RAG Chatbot

| Change | Detail |
|--------|--------|
| Supabase pgvector | `document_chunks` table, `embedding vector(768)`, `ivfflat` index, RLS per user. |
| Gemini `text-embedding-004` | Free tier (~1500 req/min). 768-dimensional embeddings. No local model — keeps Docker lean. |
| RAG subgraph | Two-node LangGraph: `retrieve` → `synthesize` → END. Separate from the diagnostic graph. |
| Auto-ingestion | On medical report save, FastAPI `BackgroundTasks` chunks + embeds + inserts to `document_chunks`. User gets the report immediately; RAG retrieval ready seconds later. |
| Chat UI | `ChatPanel` component + `useChat` hook on the diagnosis page. |

### Key files

- `backend/graphs/patient_workflow.py` — consolidated routing + graph compilation
- `backend/graphs/rag_chatbot.py` — RAG retrieve → synthesize subgraph
- `backend/rag/embedder.py` — Gemini text-embedding-004 (lazy init)
- `backend/rag/retriever.py` — chunk/embed/upsert + similarity search via Supabase RPC
- `backend/api/chat_routes.py` — `POST /chat/ask`, `POST /chat/ingest-report/{id}`
- `backend/api/diagnosis_routes.py` — all 4 endpoints use `session_id` as `thread_id`
- `backend/migrations/002_rag_pgvector.sql` — **must be run manually in Supabase SQL Editor**
- `my-app/src/components/medical/ChatPanel.tsx` — chat UI component
- `my-app/src/hooks/useChat.ts` — chat state hook

### PHI note

MediSage is a portfolio/demo app — not HIPAA-compliant. The UI shows "Do not enter real personal health information". Privacy policy discloses Groq + Supabase processing. RLS enforced on all tables.

---

## SP3 — Diagnostic Workflow Refinement ⬜ Not started

**Blocked by:** SP2 (RAG chatbot must exist to define the clean boundary)

**What:** Add a structured patient intake step at the start of every session and enforce clear contracts between the diagnostic workflow and the RAG chatbot.

### Planned changes

| Change | Detail |
|--------|--------|
| Patient intake form | Age, biological sex, current medications, known allergies, relevant medical history — collected once at session start. |
| Intake data in `AgentState` | Passed as structured context to all downstream nodes. Never re-asked. |
| Node contract audit | Each node gets a documented contract: what it produces, what it cannot produce. |
| Follow-up question audit | Follow-up nodes must not ask fields already captured in intake. Zero overlap. |
| Report surface | Intake data correctly appears in the generated medical report. |

### Clean boundary

- **Diagnostic workflow** → structured clinical reasoning from current symptoms + intake data
- **RAG chatbot** → historical context, longitudinal patterns, user-provided documents

---

## SP4 — UX/UI Redesign ⬜ Not started

**Blocked by:** SP1 (privacy policy gate UI), SP3 (intake form UI) — layout/design work can start in parallel

**What:** Replace deprecated Create React App toolchain with Vite and redesign the frontend with a modern clinical aesthetic.

### Planned changes

| Change | Detail |
|--------|--------|
| CRA → Vite | CRA is officially deprecated. Vite provides faster builds, HMR, and modern bundling. |
| Styling decision | Evaluate Tailwind CSS + shadcn/ui vs. keeping styled-components. Clean clinical/medical aesthetic — not a generic dashboard. |
| Mobile responsiveness | Full audit and fix. |
| Privacy policy screen | Frontend counterpart to SP1 backend gate. |
| Patient intake form UI | Frontend counterpart to SP3 backend. |

### Success criteria

- `npm run build` produces a production bundle via Vite (no CRA)
- Lighthouse score ≥ 85 on performance and accessibility

---

## SP5 — Production Hardening ⬜ Not started

**Blocked by:** SP1 (no CUDA in image), SP2 (stable graph), SP4 (frontend build artefact)

**What:** Make MediSage deployable, observable, and secure for real traffic.

### Planned changes

**Containerisation**
- `Dockerfile` for backend (FastAPI, no CUDA)
- `Dockerfile` for frontend (Vite build served via nginx)
- `docker-compose.yml` for local dev (backend + frontend + Redis)
- Deployment target: Railway or Render

**Redis**
- Swap `AsyncPostgresSaver` → `AsyncRedisSaver` (one-line change in `main.py`)
- Redis = active session checkpoints with TTL auto-expiry
- Supabase = permanent record store (reports, document chunks, user profiles)
- RAG chat history: active session → Redis TTL; long-term → Supabase

**Security**
- Rate limiting via `slowapi` — per-IP and per-user limits on `/patient/*` endpoints
- CORS: lock `allow_origins` to production domain (currently `localhost:3000`)
- RLS audit: all remaining tables need RLS policies
- API key audit: no hardcoded credentials anywhere
- HTTPS: enforced at platform level (Railway/Render handle TLS)

**Observability**
- Replace all `print()` with structured `logging` (JSON formatter for production)
- `/health` endpoint must verify DB connectivity, not just return 200
- Optional: Sentry for error tracking

**CI/CD**
- GitHub Actions: lint → test → docker build → deploy to Railway/Render on merge to `main`

### Success criteria

- `docker compose up` starts full stack locally with no manual steps beyond copying `.env`
- Push to `main` triggers a working deploy via GitHub Actions
- Rate limiting rejects >20 req/min per IP on diagnosis endpoints
- No hardcoded secrets in any tracked file

---

## Status at a Glance

| SP | Status | What it delivers |
|----|--------|-----------------|
| SP1 | ✅ Complete | Groq API, no local models, privacy policy gate |
| SP2 | ✅ Complete | LangGraph graph-only routing, AsyncPostgresSaver, RAG chatbot |
| SP3 | ⬜ Next | Patient intake form, node contracts, zero follow-up overlap |
| SP4 | ⬜ After SP1/SP3 | Vite migration, clinical UI redesign |
| SP5 | ⬜ After SP2/SP4 | Docker, CI/CD, Redis, rate limiting, observability |

**Dependency order:** SP1 → SP2 → SP3, then SP4 and SP5 in parallel after SP1.
