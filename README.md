# MediSage

An anonymous pre-consultation triage tool. Describe your symptoms in plain
language and MediSage returns a ranked differential with an **evidence map** —
for each candidate condition, which diagnostic criteria your account supports,
which it contradicts, and which nobody has established yet — then lets you close
the gaps that actually separate the candidates and download the result.

**No accounts. No login. Nothing is stored.** The report you download is the only
copy.

> [!WARNING]
> **Not a medical device.** MediSage is decision-support and educational
> software, not a substitute for professional medical advice, diagnosis, or
> treatment. It surfaces possibilities and flags when to seek urgent care — it
> does not make clinical decisions. Always consult a qualified clinician.

---

## Why there is no confidence score

Most symptom checkers show a percentage. MediSage deliberately does not compute,
store or display one anywhere.

The design follows Ren et al. (arXiv:2601.15645), which benchmarked 27
confidence estimators on medical consultation data. Plain confidence elicitation
— asking the model how sure it is — was the least robust method tested. More
decisively, their agent experiment found the best estimator and plain
elicitation reached **identical diagnostic accuracy**; the better number bought
only efficiency, i.e. knowing when to stop asking questions.

So MediSage keeps that method's useful half — the supported / contradicted /
unaddressed evidence map — and hands the stopping decision to the user. A
percentage is unactionable for a patient. *"We don't know whether you have
rebound tenderness"* is actionable.

Ranking is a **lexicographic comparison of evidence tallies**: no weights, no
arithmetic, nothing calibratable. A contradicted core criterion is the strongest
evidence against a candidate, so it leads. **Ties are preserved, not broken** —
"what you have told us does not separate these" is the honest statement, and it
is what motivates answering the next question.

## How it works

The backend is a [LangGraph](https://langchain-ai.github.io/langgraph/) pipeline
of three LLM nodes separated by two purely deterministic stages.

```
symptoms
   │
   ▼
[A] differential ──▶ [B] criteria profiles ──▶ merge ──▶ [C] evidence ──▶ rank ──▶ summary
      (strong)          (per candidate,      (HPO         (one batched    (lexico-   │
       1 call            cached, parallel)   canonical-    call over all    graphic)  ▼
                                             isation)      criteria)              download
                                                                                  PDF / Word
                                              ▲                                      │
                                              └──────── your yes / no answers ◀───────┘
```

- **Node A — differential.** Candidate conditions from the symptom text. No
  confidence field; the model's ordering is discarded.
- **Node B — criteria profiles.** For each candidate, its diagnostic criteria,
  each tagged `strong` / `moderate` / `weak` and typed as symptom, history, lab,
  imaging or demographic. **This node never sees the patient's text** — if it
  did, it would write criteria that fit the presentation and every criterion
  would come back "supported". The isolation is structural, not a prompt
  instruction, and there is a test that fails if it is ever broken.
- **Merge (deterministic).** Criteria are canonicalised against the
  [Human Phenotype Ontology](https://hpo.jax.org/) so the same underlying
  symptom is not judged twice under different candidates.
- **Node C — evidence.** One batched call judges every merged criterion. Every
  `supported` / `contradicted` verdict must quote the patient **verbatim**; a
  quote that cannot be located in their text is rejected and the criterion
  downgraded. The key set is fixed by the merge stage — keys the model invents
  are discarded, keys it omits default to unaddressed.
- **Rank and ask (deterministic).** Candidates are ordered lexicographically;
  open questions are ordered by how much answering them could actually reorder
  the differential.
- **Download.** The evidence table exports to PDF or Word — a ranked
  differential with quoted evidence and explicit information gaps, which is a
  better clinician handoff than generated prose.

## Tech stack

| Layer | Choice |
|-------|--------|
| API | Python 3.11, FastAPI, LangGraph |
| LLM | Groq, OpenAI-compatible; model set by `LLM_MODEL` |
| Ontology | Human Phenotype Ontology (`hp.obo`, fetched at deploy) |
| State | `MemorySaver` — in-process, deliberately not persisted |
| Frontend | React 18, Vite, Tailwind CSS + shadcn/ui |
| Rate limiting | `slowapi`, per IP; Redis when available, in-memory otherwise |
| Auth | **None.** There are no accounts. |
| Deploy | Docker, Railway, GitHub Actions CI/CD |

## Quick start

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

The backend fetches the ontology on first run:

```bash
mkdir -p backend/data
curl -L -o backend/data/hp.obo https://purl.obolibrary.org/obo/hp.obo
```

If it is absent the app still runs — criteria fall back to local keys, which
degrades merge quality without breaking anything.

### Required environment variables

Set these in `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `LLM_API_KEY` | Groq API key (`gsk_...`) |
| `LLM_MODEL` | Model id. **The historic default `llama-3.3-70b-versatile` is decommissioned** — set this explicitly. |
| `LLM_BASE_URL` | Defaults to `https://api.groq.com/openai/v1` |
| `REDIS_URL` | Optional. Rate limiting falls back to in-memory. |
| `ALLOWED_ORIGINS` / `APP_ENV` | CORS origins + environment |

There is no database, no auth secret and no embedding key to configure. If you
see `SUPABASE_*` or `GEMINI_API_KEY` in an old `.env`, they are unused.

> [!IMPORTANT]
> Do **not** set `LANGCHAIN_TRACING_V2=true`. LangGraph reads it implicitly and
> would ship every node run — including the full symptom narrative — to
> LangSmith's cloud, which defeats the point of storing nothing. `main.py`
> force-disables it, but do not fight that.

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
│   ├── api/                 diagnosis + export routes
│   ├── diagnosis/           HPO index, criterion merge, ranking  (no LLM)
│   ├── knowledge/           retrieval seam + stub corpus
│   ├── graphs/              the diagnosis workflow
│   ├── nodes/               differential, profile, evidence, summary
│   ├── llm/                 LLM client (Groq / OpenAI-compatible)
│   ├── schemas/             state model
│   ├── migrations/          SQL history (nothing is written at runtime)
│   ├── data/                hp.obo (gitignored) + criteria corpus
│   ├── tests/               pytest suite
│   ├── config.py · main.py
│   └── Dockerfile
├── my-app/                  React + Vite frontend
│   ├── src/                 views, pages, components, hooks
│   ├── Dockerfile · nginx.conf
├── docker-compose.yml
├── railway.toml
└── .github/workflows/ci.yml
```

## Testing

```bash
cd backend && python -m pytest tests/     # 123 tests
cd my-app  && npx tsc --noEmit            # the frontend has no test runner
cd my-app  && npx vite build
```

Two tests in `tests/test_rag_embedder.py` call a live API and are rate-limit
flaky; deselect them for a deterministic count.

## Deployment

Two Docker images (FastAPI backend, nginx-served frontend build) deploy to
**Railway**. GitHub Actions runs `test → docker build → deploy` on push to
`main`. CORS, rate limiting and structured JSON logging activate when
`APP_ENV=production`. `/health` probes the LLM and reports `degraded` if it is
unreachable.

> [!IMPORTANT]
> The backend must run with **one worker**. Session state lives in an
> in-process `MemorySaver`, so a second worker would not see sessions started by
> the first and roughly half of all follow-up requests would 404. Scale by
> adding container instances only behind session affinity.

## Security & privacy

- **No accounts, no login, no cookies.** Nothing to breach.
- **Nothing is persisted.** Session state is in-process and lost on restart; the
  downloaded report is the only copy.
- Symptom text is still **sent to a third-party LLM provider** for inference.
  Anonymity removes storage, not transmission — their retention is their policy.
- The session id is the only handle on a session, so it is full-entropy,
  server-generated, and never client-supplied.
- CORS locked to `ALLOWED_ORIGINS`; per-IP rate limiting on every endpoint that
  costs money or returns a document.
- No secrets in source.

## License

See [LICENSE](LICENSE).
