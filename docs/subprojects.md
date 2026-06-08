# MediSage — Production Refactor Sub-Projects

Reference doc for subagents and future sessions. Each SP is an independent unit with its own spec → plan → implementation cycle.

**Overall goal:** Transform MediSage from a local-model dev prototype into a production-grade, portfolio-ready AI medical assistant demonstrating scalable system design.

**Dependency order:** SP1 → SP2 → SP3 (SP4 and SP5 can run in parallel after SP1 is done)

---

## SP1 — API Model Migration

**Goal:** Replace all local model inference with cloud API calls. Remove every hard dependency on GPU hardware so the app can be containerised and scaled horizontally.

**Key decisions made (brainstorming session 2026-06-09):**
- Local Llama 3.1-8B GGUF → **Groq API (Llama 3.3 70B)** as primary provider
- Provider interface must be **abstracted** — swappable to Claude Haiku / GPT-4o mini via config change (no code change)
- **EfficientNet skin cancer classifier removed entirely** — not clinically validated; binary classifier output is not safe for a production health app
- **No DeepSeek API directly** — data residency in China is incompatible with healthcare PHI. DeepSeek models via Azure AI are acceptable if needed in future.
- **Privacy policy gate** — users must explicitly accept ToS/Privacy Policy before first use; policy must disclose third-party AI processing
- **PII stripping** — name/email/DOB must not be included in the same LLM API payload as symptom descriptions

**Files to remove / replace:**
- `backend/managers/model_manager.py` — loads local GGUF and EfficientNet; replace with lightweight API client wrapper
- `backend/nodes/image_classification_node.py` — remove entirely
- `backend/ai_models/` — audit; remove local model loading code
- Image upload UI + image-related workflow branches in `patient_workflow.py`

**Files to add:**
- `backend/adapters/llm_client.py` — single interface over Groq/Claude/OpenAI; provider selected by `LLM_PROVIDER` env var
- `backend/migrations/001_privacy_policy.sql` — **already created** (user_profiles table with `privacy_policy_accepted`, RLS policies)

**Open question (resolve before implementation):** Does the diagnostic workflow need real-time streaming (WebSocket / SSE) or is request-response sufficient? WebSocket code exists in `main.py` but is commented out. Answer determines whether `managers/websocket_manager.py` stays.

**Success criteria:**
- `docker build` produces an image with no CUDA dependency and under 500MB
- Full diagnosis workflow completes end-to-end via Groq API in a clean environment (no local model files)
- Privacy policy gate blocks access until accepted

---

## SP2 — LangGraph Refactor + Agentic RAG Chatbot

**Goal:** Eliminate the manual `workflow_state_manager.py` routing layer and consolidate all workflow logic into LangGraph conditional edges. Add an agentic RAG chatbot that reasons over the user's diagnostic history and uploaded context.

**Context:** LangGraph is already used (`patient_workflow.py` uses `StateGraph`) but `workflow_state_manager.py` sits alongside it as a parallel manual router — duplicating routing logic outside the graph. This must collapse into the graph itself.

**Key decisions made (brainstorming session 2026-06-09):**
- **LangGraph checkpointer (SP2):** `AsyncPostgresSaver` (Supabase) — enables proper human-in-the-loop `interrupt_before` pattern, works across multiple Uvicorn workers/containers, no new infrastructure. Client sends `session_id` only, not full `AgentState`.
- **LangGraph checkpointer (SP5):** Swap to `AsyncRedisSaver` when SP5 adds Redis. One-line change. Redis = active session checkpoint (TTL auto-expiry); Supabase = permanent record store. No dual-write needed — these are separate concerns.
- **Embedding model:** Gemini `text-embedding-004` (free tier, ~1500 req/min). Consistent with SP1 API-first direction; keeps Docker image lean. `all-MiniLM-L6-v2` ruled out: adds ~300MB and breaks SP1's no-local-model success criterion.
- **Vector store:** Supabase pgvector — `document_chunks` table with `embedding vector(768)` column, RLS for per-user isolation. No FAISS files.
- **Report auto-ingestion:** On medical report save, use FastAPI `BackgroundTasks` to chunk + embed (Gemini) + insert into `document_chunks`. User gets the report immediately; RAG retrieval available seconds later.
- **PHI / responsible design:** MediSage is a portfolio/demo app — not HIPAA-compliant. Required: (1) visible UI disclaimer "Do not enter real personal health information", (2) privacy policy must state data is processed by Groq and stored on Supabase, (3) RLS enforced on all tables, (4) PII stripping already in place (SP1). Real HIPAA compliance is out of scope.
- **Concurrent users:** Fully supported. FastAPI async event loop + `AsyncPostgresSaver` scales across multiple workers and containers. `MemorySaver` is in-process only and must not be used in production.
- **RAG chatbot conversation history:** Active chat session state → Redis TTL (SP5). Long-term chat history → Supabase (for retrieval across sessions). Separate from the diagnostic workflow checkpointer.

**Key changes:**
- Merge `workflow_state_manager.py` routing logic into LangGraph conditional edge functions; delete the file
- Compile diagnostic graph with `AsyncPostgresSaver` + `interrupt_before` at follow-up interaction node
- RAG chatbot: separate LangGraph subgraph retrieving from user's past medical reports + uploaded documents
- Embedding: Gemini `text-embedding-004` via API (no local model)
- Vector store: Supabase pgvector (`document_chunks` table, RLS, 768-dim)
- Report auto-ingestion: FastAPI `BackgroundTasks` triggered on medical report save
- Chatbot has access to: user's past reports, user-provided documents, current session context
- Chatbot and diagnostic workflow are distinct graphs — they do not share nodes

**Dependencies:** SP1 must be complete (provider abstraction layer in place)

**Success criteria:**
- `workflow_state_manager.py` deleted; all routing lives in graph conditional edge functions
- RAG chatbot returns responses that correctly reference the user's past diagnostic history
- No duplicate routing logic anywhere in the backend
- UI displays PHI disclaimer on the diagnosis page

---

## SP3 — Diagnostic Workflow Refinement

**Goal:** Add a structured patient intake step at workflow entry and clearly delineate what the diagnostic workflow handles vs what the RAG chatbot handles — eliminating any overlap.

**Key changes:**
- **Patient intake form** at the start of every session: age, biological sex, current medications, known allergies, relevant medical history
- Intake data stored in `AgentState` and passed to all downstream nodes as structured context (never re-asked)
- **Node responsibility audit:** each node must have a documented contract for what it produces and what it cannot produce
  - Diagnostic workflow: structured clinical reasoning from current symptoms + intake data
  - RAG chatbot: historical context, longitudinal patterns, user-provided documents
  - Follow-up question nodes must not ask fields already captured in intake
- Final medical report must surface intake data correctly

**Dependencies:** SP2 (RAG chatbot must exist to define the clean boundary)

**Success criteria:**
- Zero overlap between intake form fields and follow-up questions generated by any node
- Patient intake data appears correctly in generated medical reports
- Written boundary document (or inline comments) defining each node's contract

---

## SP4 — UX/UI Redesign

**Goal:** Replace the deprecated Create React App toolchain with Vite and redesign the frontend with a modern, production-appropriate look for a healthcare portfolio piece.

**Key changes:**
- **CRA → Vite** (CRA is officially deprecated)
- Stay on **React 18 SPA + Vite** (not Next.js — no SSR/SEO requirement, simpler migration)
- Styling: evaluate **Tailwind CSS + shadcn/ui** to replace styled-components, or keep styled-components
- Clean clinical/medical aesthetic — not a generic dashboard template
- Mobile responsiveness audit
- Privacy policy acceptance screen (SP1 backend gate needs a frontend counterpart)
- Patient intake form UI (SP3 backend needs a frontend counterpart)

**Dependencies:** SP1 (privacy policy gate UI), SP3 (intake form UI) — layout and design work can begin in parallel before SP1/SP3 are complete

**Success criteria:**
- `npm run build` produces a production bundle via Vite (no CRA)
- Lighthouse score ≥ 85 on performance and accessibility
- Privacy policy gate and patient intake form integrated end-to-end

---

## SP5 — Production Hardening

**Goal:** Make MediSage deployable, observable, and secure for real traffic — Docker, CI/CD, rate limiting, Redis, and a full security sweep.

**Containerisation & Deployment:**
- `Dockerfile` for backend (Python/FastAPI) — no CUDA after SP1
- `Dockerfile` for frontend (Vite build served via nginx)
- `docker-compose.yml` for local dev (backend + frontend + Redis)
- Deployment target: **Railway** or **Render** (simpler than K8s for portfolio; existing `4_deployment/kubernetes/` preserved as reference)
- Secrets via platform env vars; `.env.example` documented

**Security:**
- Rate limiting: `slowapi` middleware — per-IP and per-user limits on `/patient/*` endpoints
- Redis: session caching + rate limit counters (replaces in-memory state)
- CORS: lock `allow_origins` to production domain (currently hardcoded `localhost:3000`)
- SQL injection: all DB calls via Supabase client (parameterised by default) — audit for any raw SQL
- RLS: **partially in place** (`001_privacy_policy.sql` adds RLS to `user_profiles`) — audit all remaining tables
- HTTPS: enforced at platform level (Railway/Render handle TLS termination)
- API key audit: no hardcoded credentials anywhere in codebase

**Observability:**
- Replace all `print()` statements with structured `logging` (JSON formatter for production)
- Health check `/health` endpoint must verify DB connectivity, not just return 200
- Optional: Sentry for error tracking

**CI/CD:**
- GitHub Actions: lint → test → docker build → deploy to Railway/Render on merge to `main`

**Dependencies:** SP1 (no CUDA in image), SP2 (stable graph), SP4 (frontend build artefact)

**Success criteria:**
- `docker compose up` starts the full stack locally with no manual steps beyond copying `.env`
- Push to `main` triggers a working deploy via GitHub Actions
- Rate limiting rejects >20 req/min per IP on diagnosis endpoints
- No hardcoded secrets in any tracked file

---

## Status Tracker

| SP | Status | Blocked by | Notes |
|----|--------|-----------|-------|
| SP1 | ✅ Complete | — | Groq API migration done. EfficientNet removed. Privacy policy gate live. `001_privacy_policy.sql` applied to Supabase. |
| SP2 | 🟡 In design | SP1 | Checkpointer: AsyncPostgresSaver → AsyncRedisSaver (SP5). Embedding: Gemini text-embedding-004. Vector store: pgvector. |
| SP3 | ⬜ Not started | SP2 | — |
| SP4 | ⬜ Not started | SP1 (for gate UI) | Layout/design work can start in parallel |
| SP5 | 🟡 Partial | SP1 | RLS migration created. Rest blocked on stable codebase. |
