# SP2 — LangGraph Refactor + Agentic RAG Chatbot

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual `workflow_state_manager.py` routing with LangGraph conditional edges + `AsyncPostgresSaver` checkpointer, then add a separate RAG chatbot subgraph that retrieves from the user's medical history.

**Architecture:** The diagnostic graph is compiled once with an `AsyncPostgresSaver` (Supabase direct DB connection) and stored in `app.state`. Each of the 4 diagnosis HTTP endpoints resumes the graph from its checkpoint using `session_id` as `thread_id`; `interrupt_before` on all continuation nodes ensures the graph pauses between steps. Routing logic that currently lives in `workflow_state_manager.py` moves into two routing functions inside `patient_workflow.py`. The RAG chatbot is a completely separate LangGraph subgraph using Gemini `text-embedding-004` + Supabase pgvector.

**Tech Stack:** LangGraph, `langgraph-checkpoint-postgres`, Supabase (pgvector + direct DB connection), Gemini `text-embedding-004`, FastAPI `BackgroundTasks`

> **Scope note:** Part A (Tasks 1-6) and Part B (Tasks 7-13) are independently shippable. Part A eliminates `workflow_state_manager.py` and is safe to merge alone.

---

## File Map

**Part A — Diagnostic Workflow Consolidation**

| File | Action | Purpose |
|---|---|---|
| `backend/requirements.txt` | Modify | Add `langgraph-checkpoint-postgres` |
| `backend/config.py` | Modify | Add `SUPABASE_DB_URL` and `GEMINI_API_KEY` settings |
| `backend/main.py` | Modify | Init `AsyncPostgresSaver`, store compiled graph in `app.state` |
| `backend/graphs/patient_workflow.py` | Rewrite | New StateGraph with conditional edges + `interrupt_before` |
| `backend/api/diagnosis_routes.py` | Modify | Resume graph per endpoint; remove `workflow_state_manager`, `session_states`, `previous_state` params |
| `backend/managers/workflow_state_manager.py` | Delete | Routing logic now in graph conditional edge functions |
| `my-app/src/services/api.ts` | Modify | Remove `state: AgentState` param from 3 methods |
| `my-app/src/hooks/useDiagnosis.ts` | Modify | Remove `result` from API call sites |
| `backend/tests/test_workflow_routing.py` | Create | Unit tests for routing functions |

**Part B — RAG Chatbot**

| File | Action | Purpose |
|---|---|---|
| `backend/migrations/002_rag_pgvector.sql` | Create | Enable pgvector; create `document_chunks` table with RLS |
| `backend/rag/__init__.py` | Create | Package marker |
| `backend/rag/embedder.py` | Create | Gemini `text-embedding-004` client + chunker |
| `backend/rag/retriever.py` | Create | pgvector ingest + similarity search |
| `backend/schemas/chat_schemas.py` | Create | `ChatState` TypedDict |
| `backend/graphs/rag_chatbot.py` | Create | RAG chatbot LangGraph subgraph |
| `backend/api/chat_routes.py` | Create | `POST /chat/ask`, `POST /chat/ingest-report/{id}` |
| `backend/api/diagnosis_routes.py` | Modify | Add `BackgroundTasks` ingestion on report save |
| `backend/main.py` | Modify | Register `chat_router` + `rag_graph` in app state |
| `backend/tests/test_rag_embedder.py` | Create | Unit test for embedder |
| `my-app/src/hooks/useChat.ts` | Create | Chat state hook |
| `my-app/src/components/medical/ChatPanel.tsx` | Create | Chat UI component |
| `my-app/src/services/api.ts` | Modify | Add `askChat` method |

---

## PART A — Diagnostic Workflow Consolidation

---

### Task 1: Add checkpointer dependency + config

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/config.py`

`AsyncPostgresSaver` needs a **direct** PostgreSQL connection string — NOT the Supabase REST API URL. Find it in: Supabase Dashboard -> Settings -> Database -> Connection string -> "URI" tab -> Direct connection. Format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

- [ ] **Step 1: Add packages to requirements.txt**

In `backend/requirements.txt`, add after `langgraph`:
```
langgraph-checkpoint-postgres
google-generativeai
```

- [ ] **Step 2: Update config.py**

Replace the entire contents of `backend/config.py`:
```python
import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()
```

- [ ] **Step 3: Add env vars to .env (not committed)**

Add to `.env`:
```
SUPABASE_DB_URL=postgresql://postgres:[your-password]@db.[project-ref].supabase.co:5432/postgres
GEMINI_API_KEY=your-gemini-api-key-from-aistudio.google.com
```

- [ ] **Step 4: Install dependencies**

```bash
cd backend && pip install langgraph-checkpoint-postgres google-generativeai
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/config.py
git commit -m "chore(sp2): add langgraph-checkpoint-postgres + google-generativeai + new config fields"
```

---

### Task 2: Rewrite patient_workflow.py

**Files:**
- Rewrite: `backend/graphs/patient_workflow.py`
- Create: `backend/tests/test_workflow_routing.py`

The current `patient_workflow.py` is dead code (broken adapter imports, never called by routes). Replace it entirely. The two routing functions `_route_after_diagnosis` and `_route_after_followup` replace ALL logic from `WorkflowStateManager.update_workflow_stage_and_determine_next`. Node wrappers `_GenerateQuestionsNode` and `_ProcessResponsesNode` split `FollowUpInteractionNode` into two graph steps without modifying the existing node file.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_workflow_routing.py`:
```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graphs.patient_workflow import _route_after_diagnosis, _route_after_followup


def test_route_diagnosis_low_confidence_goes_to_followup():
    state = {"average_confidence": 0.5, "requires_skin_cancer_screening": False}
    assert _route_after_diagnosis(state) == "generate_followup_questions"


def test_route_diagnosis_skin_cancer_flag_goes_to_followup():
    state = {"average_confidence": 0.9, "requires_skin_cancer_screening": True}
    assert _route_after_diagnosis(state) == "generate_followup_questions"


def test_route_diagnosis_high_confidence_no_screening_goes_to_overall():
    state = {"average_confidence": 0.8, "requires_skin_cancer_screening": False}
    assert _route_after_diagnosis(state) == "overall_analysis"


def test_route_diagnosis_no_confidence_field_goes_to_overall():
    state = {}
    assert _route_after_diagnosis(state) == "overall_analysis"


def test_route_followup_requires_input_loops_back():
    state = {"requires_user_input": True}
    assert _route_after_followup(state) == "generate_followup_questions"


def test_route_followup_done_goes_to_overall():
    state = {"requires_user_input": False}
    assert _route_after_followup(state) == "overall_analysis"


def test_route_followup_no_flag_defaults_to_overall():
    state = {}
    assert _route_after_followup(state) == "overall_analysis"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_workflow_routing.py -v
```
Expected: `ImportError` — `_route_after_diagnosis` does not exist yet

- [ ] **Step 3: Rewrite patient_workflow.py**

Replace the entire file `backend/graphs/patient_workflow.py`:
```python
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledStateGraph
from schemas.medical_schemas import AgentState
from nodes import LLMDiagnosisNode, OverallAnalysisNode, MedicalReportNode
from nodes.follow_up_interaction_node import FollowUpInteractionNode

CONFIDENCE_THRESHOLD = 0.75


def _route_after_diagnosis(state: AgentState) -> str:
    if state.get("requires_skin_cancer_screening", False):
        return "generate_followup_questions"
    if (state.get("average_confidence") or 1.0) < CONFIDENCE_THRESHOLD:
        return "generate_followup_questions"
    return "overall_analysis"


def _route_after_followup(state: AgentState) -> str:
    if state.get("requires_user_input", False):
        return "generate_followup_questions"
    return "overall_analysis"


class _GenerateQuestionsNode:
    def __init__(self, node: FollowUpInteractionNode):
        self._node = node

    async def __call__(self, state: dict) -> dict:
        return await self._node._generate_questions_phase(state)


class _ProcessResponsesNode:
    def __init__(self, node: FollowUpInteractionNode):
        self._node = node

    async def __call__(self, state: dict) -> dict:
        followup_response = state.get("followup_response", {})
        return await self._node._process_responses_phase(state, followup_response)


def compile_patient_workflow(checkpointer) -> CompiledStateGraph:
    followup_node = FollowUpInteractionNode()

    workflow = StateGraph(AgentState)
    workflow.set_entry_point("llm_diagnosis")

    workflow.add_node("llm_diagnosis", LLMDiagnosisNode())
    workflow.add_node("generate_followup_questions", _GenerateQuestionsNode(followup_node))
    workflow.add_node("process_followup_responses", _ProcessResponsesNode(followup_node))
    workflow.add_node("overall_analysis", OverallAnalysisNode())
    workflow.add_node("medical_report", MedicalReportNode())

    workflow.add_conditional_edges(
        "llm_diagnosis",
        _route_after_diagnosis,
        {
            "generate_followup_questions": "generate_followup_questions",
            "overall_analysis": "overall_analysis",
        },
    )
    workflow.add_edge("generate_followup_questions", "process_followup_responses")
    workflow.add_conditional_edges(
        "process_followup_responses",
        _route_after_followup,
        {
            "generate_followup_questions": "generate_followup_questions",
            "overall_analysis": "overall_analysis",
        },
    )
    workflow.add_edge("overall_analysis", "medical_report")
    workflow.add_edge("medical_report", END)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "generate_followup_questions",
            "process_followup_responses",
            "overall_analysis",
            "medical_report",
        ],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_workflow_routing.py -v
```
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/graphs/patient_workflow.py backend/tests/test_workflow_routing.py
git commit -m "feat(sp2): rewrite patient_workflow with LangGraph conditional edges replacing workflow_state_manager"
```

---

### Task 3: Update main.py — init checkpointer + store compiled graph in app.state

**Files:**
- Modify: `backend/main.py`

The compiled graph (with its attached connection pool) lives for the duration of the app lifespan. Routes access it via `request.app.state.patient_graph`.

- [ ] **Step 1: Read current main.py**

Read `backend/main.py` in full before editing.

- [ ] **Step 2: Replace the lifespan function**

The lifespan function should become:
```python
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI Medical Diagnosis API starting...")

    if not settings.LLM_API_KEY:
        print("WARNING: LLM_API_KEY not set - LLM calls will fail at runtime")
    else:
        try:
            from llm.client import llm_client
            await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
            print(f"LLM connectivity confirmed (model: {settings.LLM_MODEL})")
        except Exception as e:
            print(f"WARNING: LLM health ping failed: {e}")

    if not settings.SUPABASE_DB_URL:
        raise RuntimeError("SUPABASE_DB_URL is required for workflow state persistence")

    async with AsyncPostgresSaver.from_conn_string(settings.SUPABASE_DB_URL) as checkpointer:
        await checkpointer.setup()
        from graphs.patient_workflow import compile_patient_workflow
        app.state.patient_graph = compile_patient_workflow(checkpointer)
        print("Patient workflow graph compiled with Supabase checkpointer")
        print("Startup complete!")
        yield

    print("Shutdown complete!")
```

- [ ] **Step 3: Verify server starts**

```bash
cd backend && uvicorn main:app --reload --port 8000
```
Expected: `"Startup complete!"` printed, `GET http://localhost:8000/health` returns `{"status": "healthy"}`

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat(sp2): init AsyncPostgresSaver in app lifespan, store compiled graph in app.state"
```

---

### Task 4: Rewrite diagnosis_routes.py to use graph

**Files:**
- Modify: `backend/api/diagnosis_routes.py`

Each endpoint now calls `graph.ainvoke` or `graph.aupdate_state + ainvoke` instead of calling nodes directly. The `_get_workflow_info` helper replaces `WorkflowStateManager.update_workflow_stage_and_determine_next` — it reads `snapshot.next` from the checkpointer to determine the frontend's next step.

- [ ] **Step 1: Replace diagnosis_routes.py**

```python
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Depends, Request, Response
from typing import Optional
import uuid
from datetime import datetime
import logging
import json

from schemas.medical_schemas import AgentState
from api.auth_routes import require_privacy_policy, get_current_user

diagnosis_router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_workflow_info(graph, config: dict, state: dict) -> dict:
    snapshot = await graph.aget_state(config)
    next_nodes = list(snapshot.next) if snapshot and snapshot.next else []

    if not next_nodes:
        return {
            "workflow_complete": True,
            "next_endpoint": None,
            "needs_user_input": None,
            "next_step_description": "Medical analysis workflow complete",
            "show_next_button": False,
            "medical_report_available": bool(state.get("medical_report")),
        }

    node_map = {
        "generate_followup_questions": ("/patient/followup_questions", "followup_questions", "Follow-up questions needed"),
        "process_followup_responses": ("/patient/followup_questions", "followup_questions", "Answer follow-up questions"),
        "overall_analysis": ("/patient/overall_analysis", None, "Ready for comprehensive analysis"),
        "medical_report": ("/patient/medical_report", None, "Generating medical report"),
    }
    endpoint, user_input, description = node_map.get(next_nodes[0], (None, None, "Unknown next step"))

    return {
        "workflow_complete": False,
        "next_endpoint": endpoint,
        "needs_user_input": user_input,
        "next_step_description": description,
        "show_next_button": True,
        "confidence_score": state.get("average_confidence", 0.0),
    }


@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_textual_analysis(
    request: Request,
    user_symptoms: str = Form(..., description="Patient symptoms"),
    session_id: Optional[str] = Form(None),
):
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        initial_state: AgentState = {
            "session_id": session_id,
            "latest_user_message": user_symptoms,
            "userInput_symptoms": user_symptoms,
            "current_workflow_stage": "initializing",
        }
        result = await graph.ainvoke(initial_state, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/followup_questions", dependencies=[Depends(require_privacy_policy)])
async def run_followup_questions(
    request: Request,
    session_id: str = Form(...),
    followup_responses: Optional[str] = Form(None),
):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        if followup_responses:
            responses = json.loads(followup_responses)
            await graph.aupdate_state(config, {
                "followup_response": responses,
                "requires_user_input": False,
            })
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/overall_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_overall_analysis(request: Request, session_id: str = Form(...)):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/medical_report", dependencies=[Depends(require_privacy_policy)])
async def run_medical_report(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        logger.error(f"Medical report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/export_report")
async def export_report_file(
    request: Request,
    session_id: str = Form(...),
    format: str = Form(...),
    include_details: bool = Form(True),
    report_data: str = Form(...),
):
    try:
        graph = request.app.state.patient_graph
        config = {"configurable": {"thread_id": session_id}}
        snapshot = await graph.aget_state(config)
        session_state = snapshot.values if snapshot and snapshot.values else json.loads(report_data)

        from nodes.medical_report_node import MedicalReportNode
        report_node = MedicalReportNode()
        file_content = await report_node.generate_export_file(
            state=session_state, format=format, include_details=include_details
        )

        if format == "pdf":
            media_type = "application/pdf"
            filename = f"medical-report-{session_id}.pdf"
        elif format == "word":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"medical-report-{session_id}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use pdf or word.")

        return Response(
            content=file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.get("/debug/routes")
async def debug_routes():
    return {"message": "Routes working", "endpoints": [
        "/patient/textual_analysis", "/patient/followup_questions",
        "/patient/overall_analysis", "/patient/medical_report",
        "/patient/export_report", "/health",
    ]}


@diagnosis_router.get("/health")
async def health_check():
    from config import settings
    return {
        "status": "healthy",
        "service": "AI Medical Diagnosis API",
        "version": "2.0.0",
        "llm_model": settings.LLM_MODEL,
        "timestamp": datetime.now().isoformat(),
    }
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp2): rewrite diagnosis_routes to resume LangGraph graph — no more workflow_state_manager or previous_state"
```

---

### Task 5: Delete workflow_state_manager.py

**Files:**
- Delete: `backend/managers/workflow_state_manager.py`

- [ ] **Step 1: Confirm no imports remain**

```bash
grep -r "workflow_state_manager" backend/ --include="*.py"
```
Expected: no output

- [ ] **Step 2: Delete**

PowerShell: `Remove-Item backend/managers/workflow_state_manager.py`

- [ ] **Step 3: Run tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore(sp2): delete workflow_state_manager.py — routing lives in graph conditional edges"
```

---

### Task 6: Update frontend — remove previous_state from API calls

**Files:**
- Modify: `my-app/src/services/api.ts`
- Modify: `my-app/src/hooks/useDiagnosis.ts`

Three `ApiService` methods currently accept `state: AgentState` and send `previous_state` in FormData. Remove both — the backend no longer accepts them.

- [ ] **Step 1: Read api.ts and useDiagnosis.ts before editing**

Read both files in full to locate exact signatures and call sites.

- [ ] **Step 2: Update runFollowupQuestions in api.ts**

Find the method signature:
```typescript
static async runFollowupQuestions(
    sessionId: string,
    state: AgentState,
    responses?: Record<string, string>
```
Change to:
```typescript
static async runFollowupQuestions(
    sessionId: string,
    responses?: Record<string, string>
```
Remove the line: `formData.append('previous_state', JSON.stringify(state));`

- [ ] **Step 3: Update runOverallAnalysis in api.ts**

Change signature from `runOverallAnalysis(sessionId: string, state: AgentState)` to `runOverallAnalysis(sessionId: string)`.
Remove `formData.append('previous_state', JSON.stringify(state));`

- [ ] **Step 4: Update runMedicalReport in api.ts**

Same pattern — remove `state: AgentState` param and `previous_state` FormData append.

- [ ] **Step 5: Update useDiagnosis.ts — submitFollowUp call site**

```typescript
// Before:
const response = await ApiService.runFollowupQuestions(sessionId, result, responses);
// After:
const response = await ApiService.runFollowupQuestions(sessionId, responses);
```

- [ ] **Step 6: Update useDiagnosis.ts — runOverallAnalysis call site**

```typescript
// Before:
const response = await ApiService.runOverallAnalysis(sessionId, result);
// After:
const response = await ApiService.runOverallAnalysis(sessionId);
```

- [ ] **Step 7: Update useDiagnosis.ts — runMedicalReport call sites**

There are two call sites. Both: remove `result` as second argument.

- [ ] **Step 8: TypeScript compile check**

```bash
cd my-app && npx tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 9: End-to-end smoke test**

Start both backend and frontend. Complete a full diagnosis (symptoms -> follow-up questions -> submit answers -> continue -> report). Verify the workflow completes successfully with no console errors about `previous_state`.

- [ ] **Step 10: Commit**

```bash
git add my-app/src/services/api.ts my-app/src/hooks/useDiagnosis.ts
git commit -m "feat(sp2): remove previous_state from frontend — backend uses checkpointer for state"
```

---

## PART B — Agentic RAG Chatbot

---

### Task 7: Supabase pgvector migration

**Files:**
- Create: `backend/migrations/002_rag_pgvector.sql`

- [ ] **Step 1: Run in Supabase Dashboard -> SQL Editor**

```sql
-- Migration 002: pgvector + document_chunks for RAG
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('medical_report', 'uploaded_document')),
    source_id TEXT,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS document_chunks_user_source_idx
    ON document_chunks (user_id, source_type, source_id);

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own chunks" ON document_chunks
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own chunks" ON document_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own chunks" ON document_chunks
    FOR DELETE USING (auth.uid() = user_id);

-- RPC for cosine similarity search
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(768),
    match_user_id UUID,
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID, chunk_text TEXT, source_type TEXT,
    source_id TEXT, chunk_index INT, metadata JSONB, similarity FLOAT
)
LANGUAGE sql STABLE AS $$
    SELECT id, chunk_text, source_type, source_id, chunk_index, metadata,
           1 - (embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE user_id = match_user_id
      AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Verify
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'document_chunks' ORDER BY ordinal_position;
```

- [ ] **Step 2: Save migration file**

Save the above SQL to `backend/migrations/002_rag_pgvector.sql`.

- [ ] **Step 3: Commit**

```bash
git add backend/migrations/002_rag_pgvector.sql
git commit -m "chore(sp2): add pgvector migration — document_chunks table + match_document_chunks RPC"
```

---

### Task 8: Gemini embedder

**Files:**
- Create: `backend/rag/__init__.py`
- Create: `backend/rag/embedder.py`
- Create: `backend/tests/test_rag_embedder.py`

Get your Gemini API key at aistudio.google.com (free tier, ~1500 req/min). Add `GEMINI_API_KEY=...` to `.env`.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_rag_embedder.py`:
```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.asyncio
async def test_embed_text_returns_768_dim():
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    from rag.embedder import embed_text
    vector = await embed_text("chest pain and shortness of breath")
    assert isinstance(vector, list)
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_embed_chunks_returns_list():
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    from rag.embedder import embed_chunks
    vectors = await embed_chunks(["symptom one", "symptom two"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 768


def test_chunk_text_splits_long_text():
    from rag.embedder import chunk_text
    text = " ".join([f"word{i}" for i in range(1200)])
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 500 for c in chunks)
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd backend && python -m pytest tests/test_rag_embedder.py -v
```
Expected: `ImportError` on `rag.embedder`

- [ ] **Step 3: Create rag package**

Create `backend/rag/__init__.py` as an empty file.

- [ ] **Step 4: Create embedder.py**

```python
import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

_MODEL = "models/text-embedding-004"
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


async def embed_text(text: str) -> list[float]:
    result = genai.embed_content(model=_MODEL, content=text)
    return result["embedding"]


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    result = genai.embed_content(model=_MODEL, content=texts)
    embeddings = result["embedding"]
    if isinstance(embeddings[0], float):
        return [embeddings]
    return embeddings


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += chunk_size - overlap
    return chunks
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_rag_embedder.py -v
```
Expected: `3 passed` (first two skip if `GEMINI_API_KEY` not set; third always passes)

- [ ] **Step 6: Commit**

```bash
git add backend/rag/__init__.py backend/rag/embedder.py backend/tests/test_rag_embedder.py
git commit -m "feat(sp2): add Gemini text-embedding-004 embedder + chunk_text utility"
```

---

### Task 9: pgvector retriever

**Files:**
- Create: `backend/rag/retriever.py`

- [ ] **Step 1: Create retriever.py**

```python
import os
import logging
from typing import Any
from supabase import create_client, Client
from rag.embedder import embed_text, embed_chunks, chunk_text

logger = logging.getLogger(__name__)

_TOP_K = 5
_SIMILARITY_THRESHOLD = 0.7


def _get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_API_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_API_KEY required")
    return create_client(url, key)


async def ingest_document(
    user_id: str,
    source_type: str,
    source_id: str,
    text: str,
    metadata: dict | None = None,
) -> int:
    """Chunk, embed, and upsert a document. Returns chunk count inserted."""
    supabase = _get_supabase()
    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = await embed_chunks(chunks)
    rows = [
        {
            "user_id": user_id,
            "source_type": source_type,
            "source_id": source_id,
            "chunk_index": i,
            "chunk_text": chunk,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    supabase.table("document_chunks").delete().eq("user_id", user_id).eq("source_id", source_id).execute()
    supabase.table("document_chunks").insert(rows).execute()
    logger.info(f"Ingested {len(rows)} chunks: user={user_id} source={source_id}")
    return len(rows)


async def retrieve(user_id: str, query: str, top_k: int = _TOP_K) -> list[dict[str, Any]]:
    """Return top-k most similar chunks for a user query."""
    supabase = _get_supabase()
    query_embedding = await embed_text(query)
    result = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_user_id": user_id,
            "match_count": top_k,
            "match_threshold": _SIMILARITY_THRESHOLD,
        },
    ).execute()
    return result.data or []
```

- [ ] **Step 2: Commit**

```bash
git add backend/rag/retriever.py
git commit -m "feat(sp2): add pgvector retriever — ingest_document + retrieve"
```

---

### Task 10: RAG chatbot schema + LangGraph subgraph

**Files:**
- Create: `backend/schemas/chat_schemas.py`
- Create: `backend/graphs/rag_chatbot.py`

- [ ] **Step 1: Create chat schemas**

Create `backend/schemas/chat_schemas.py`:
```python
from typing_extensions import TypedDict
from typing import List, Any


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatState(TypedDict, total=False):
    user_id: str
    query: str
    conversation_history: List[ChatMessage]
    retrieved_chunks: List[Any]
    answer: str
    sources: List[str]
```

- [ ] **Step 2: Create rag_chatbot.py**

Create `backend/graphs/rag_chatbot.py`:
```python
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledStateGraph
from schemas.chat_schemas import ChatState
from rag.retriever import retrieve
from llm.client import llm_client
import logging

logger = logging.getLogger(__name__)


async def _retrieve_node(state: ChatState) -> ChatState:
    chunks = await retrieve(user_id=state["user_id"], query=state["query"])
    state["retrieved_chunks"] = chunks
    return state


async def _synthesize_node(state: ChatState) -> ChatState:
    chunks = state.get("retrieved_chunks", [])
    context = "\n\n".join(
        f"[Source {i+1} - {c.get('source_type', 'unknown')}]\n{c['chunk_text']}"
        for i, c in enumerate(chunks)
    )
    history = state.get("conversation_history", [])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a medical AI assistant helping a patient review their diagnostic history. "
                "Answer ONLY from the context provided. If the context lacks sufficient information, say so. "
                "Never fabricate medical information. Always recommend consulting a healthcare professional.\n\n"
                f"CONTEXT FROM YOUR MEDICAL RECORDS:\n{context if context else 'No relevant records found.'}"
            ),
        },
        *history,
        {"role": "user", "content": state["query"]},
    ]
    answer = await llm_client.complete(messages, max_tokens=500, temperature=0.1)
    state["answer"] = answer
    state["sources"] = [
        f"{c.get('source_type', 'unknown')} - {c.get('source_id', '')}" for c in chunks
    ]
    return state


def compile_rag_chatbot() -> CompiledStateGraph:
    workflow = StateGraph(ChatState)
    workflow.set_entry_point("retrieve")
    workflow.add_node("retrieve", _retrieve_node)
    workflow.add_node("synthesize", _synthesize_node)
    workflow.add_edge("retrieve", "synthesize")
    workflow.add_edge("synthesize", END)
    return workflow.compile()
```

- [ ] **Step 3: Commit**

```bash
git add backend/schemas/chat_schemas.py backend/graphs/rag_chatbot.py
git commit -m "feat(sp2): add RAG chatbot LangGraph subgraph (retrieve -> synthesize)"
```

---

### Task 11: Chat API routes + register in main.py

**Files:**
- Create: `backend/api/chat_routes.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create chat_routes.py**

Create `backend/api/chat_routes.py`:
```python
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import logging

from api.auth_routes import require_privacy_policy, get_current_user
from schemas.chat_schemas import ChatMessage, ChatState
from rag.retriever import ingest_document

chat_router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    query: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


@chat_router.post("/chat/ask", dependencies=[Depends(require_privacy_policy)])
async def ask_chat(request: Request, body: ChatRequest):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    graph = request.app.state.rag_graph
    initial_state: ChatState = {
        "user_id": user["id"],
        "query": body.query,
        "conversation_history": body.conversation_history or [],
    }

    try:
        result = await graph.ainvoke(initial_state)
        return ChatResponse(answer=result["answer"], sources=result.get("sources", []))
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/chat/ingest-report/{report_id}", dependencies=[Depends(require_privacy_policy)])
async def ingest_report(request: Request, report_id: str):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from nodes.medical_report_node import MedicalReportNode
        report_node = MedicalReportNode()
        report = await report_node.get_medical_report_by_id(report_id, user["id"])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        text = report.get("medical_report_content", "") or ""
        count = await ingest_document(
            user_id=user["id"],
            source_type="medical_report",
            source_id=report_id,
            text=text,
            metadata={
                "report_title": report.get("report_title", ""),
                "session_id": report.get("session_id", ""),
            },
        )
        return {"ingested_chunks": count, "report_id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Register in main.py lifespan**

Inside the `async with AsyncPostgresSaver...` block in `backend/main.py`, after `app.state.patient_graph = compile_patient_workflow(checkpointer)`, add:

```python
from graphs.rag_chatbot import compile_rag_chatbot
from api.chat_routes import chat_router
app.state.rag_graph = compile_rag_chatbot()
app.include_router(chat_router)
print("RAG chatbot graph compiled")
```

- [ ] **Step 3: Manual test**

```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What was my last diagnosis?", "conversation_history": []}'
```
Expected: `{"answer": "...", "sources": [...]}`

- [ ] **Step 4: Commit**

```bash
git add backend/api/chat_routes.py backend/main.py
git commit -m "feat(sp2): add chat API routes and register RAG graph in app state"
```

---

### Task 12: Report auto-ingestion via BackgroundTasks

**Files:**
- Modify: `backend/api/diagnosis_routes.py`

After the medical report node completes, schedule ingestion into `document_chunks` as a background task. The user gets their report immediately; embedding happens asynchronously.

- [ ] **Step 1: Read current diagnosis_routes.py**

Read `backend/api/diagnosis_routes.py` in full before editing.

- [ ] **Step 2: Add ingestion helper at top of diagnosis_routes.py**

After the existing imports, add:
```python
async def _ingest_report_background(user_id: str, session_id: str, report_text: str) -> None:
    try:
        from rag.retriever import ingest_document
        await ingest_document(
            user_id=user_id,
            source_type="medical_report",
            source_id=session_id,
            text=report_text,
            metadata={"session_id": session_id},
        )
        logger.info(f"Background ingestion complete: session={session_id}")
    except Exception as e:
        logger.error(f"Background ingestion failed: session={session_id} error={e}")
```

- [ ] **Step 3: Update run_medical_report to fire background ingestion**

Replace the `run_medical_report` try block return statement with:
```python
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)

        user = get_current_user(request)
        report_text = result.get("medical_report", "")
        if user and report_text:
            background_tasks.add_task(
                _ingest_report_background, user["id"], session_id, report_text
            )

        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
```

- [ ] **Step 4: Verify ingestion fires**

Complete a full diagnosis. Then run in Supabase SQL Editor:
```sql
SELECT source_id, chunk_index, LEFT(chunk_text, 80) AS preview
FROM document_chunks ORDER BY created_at DESC LIMIT 5;
```
Expected: rows with the session_id you just used

- [ ] **Step 5: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp2): auto-ingest medical report into pgvector via BackgroundTasks"
```

---

### Task 13: Frontend chat component

**Files:**
- Modify: `my-app/src/services/api.ts`
- Create: `my-app/src/hooks/useChat.ts`
- Create: `my-app/src/components/medical/ChatPanel.tsx`
- Modify: `my-app/src/views/diagnosis.tsx`

- [ ] **Step 1: Read api.ts before editing**

Read `my-app/src/services/api.ts` in full.

- [ ] **Step 2: Add askChat to api.ts**

Inside the `ApiService` class, add:
```typescript
static async askChat(
    query: string,
    conversationHistory: Array<{ role: string; content: string }> = []
): Promise<{ answer: string; sources: string[] }> {
    const response = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ query, conversation_history: conversationHistory }),
    });
    if (response.status === 403) {
        const body = await response.json().catch(() => ({}));
        if (body.detail === 'privacy_policy_required') throw new PrivacyPolicyRequiredError();
    }
    if (!response.ok) throw new Error(`Chat failed: HTTP ${response.status}`);
    return response.json();
}
```

- [ ] **Step 3: Create useChat.ts**

Create `my-app/src/hooks/useChat.ts`:
```typescript
import { useState, useCallback } from 'react';
import { ApiService } from 'services/api';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

interface ChatState {
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
}

export const useChat = () => {
    const [state, setState] = useState<ChatState>({ messages: [], loading: false, error: null });

    const sendMessage = useCallback(async (query: string) => {
        const userMessage: ChatMessage = { role: 'user', content: query };
        setState(prev => ({
            ...prev,
            loading: true,
            error: null,
            messages: [...prev.messages, userMessage],
        }));

        const history = state.messages.map(m => ({ role: m.role, content: m.content }));
        try {
            const { answer, sources } = await ApiService.askChat(query, history);
            setState(prev => ({
                ...prev,
                loading: false,
                messages: [...prev.messages, { role: 'assistant', content: answer, sources }],
            }));
        } catch (error) {
            setState(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : 'Chat failed',
            }));
        }
    }, [state.messages]);

    const clearChat = useCallback(() => {
        setState({ messages: [], loading: false, error: null });
    }, []);

    return {
        messages: state.messages,
        loading: state.loading,
        error: state.error,
        sendMessage,
        clearChat,
    };
};
```

- [ ] **Step 4: Create ChatPanel.tsx**

Create `my-app/src/components/medical/ChatPanel.tsx`:
```tsx
import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { useChat } from 'hooks/useChat';

const Panel = styled.div`
  display: flex;
  flex-direction: column;
  height: 500px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
`;

const Header = styled.div`
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
  font-size: 14px;
`;

const Messages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Bubble = styled.div<{ role: string }>`
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  align-self: ${p => p.role === 'user' ? 'flex-end' : 'flex-start'};
  background: ${p => p.role === 'user' ? '#0070f3' : '#f0f0f0'};
  color: ${p => p.role === 'user' ? '#fff' : '#333'};
`;

const Sources = styled.div`
  font-size: 11px;
  color: #888;
  margin-top: 4px;
`;

const InputRow = styled.div`
  display: flex;
  padding: 12px;
  border-top: 1px solid #e0e0e0;
  gap: 8px;
`;

const ChatInput = styled.input`
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
`;

const SendBtn = styled.button`
  padding: 8px 16px;
  background: #0070f3;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

export const ChatPanel: React.FC = () => {
  const { messages, loading, sendMessage } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');
    await sendMessage(q);
  };

  return (
    <Panel>
      <Header>Medical History Assistant</Header>
      <Messages>
        {messages.length === 0 && (
          <Bubble role="assistant">
            Ask me anything about your past diagnoses and medical reports.
          </Bubble>
        )}
        {messages.map((m, i) => (
          <div key={i}>
            <Bubble role={m.role}>{m.content}</Bubble>
            {m.sources && m.sources.length > 0 && (
              <Sources>Sources: {m.sources.join(' | ')}</Sources>
            )}
          </div>
        ))}
        {loading && <Bubble role="assistant">Searching your records...</Bubble>}
        <div ref={bottomRef} />
      </Messages>
      <InputRow>
        <ChatInput
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your medical history..."
        />
        <SendBtn onClick={handleSend} disabled={loading || !input.trim()}>Send</SendBtn>
      </InputRow>
    </Panel>
  );
};
```

- [ ] **Step 5: Add ChatPanel to diagnosis.tsx**

Read `my-app/src/views/diagnosis.tsx` first, then add:

Import at top:
```typescript
import { ChatPanel } from 'components/medical/ChatPanel';
```

Add inside the returned JSX, after the `</main>` closing tag and before `<footer>`:
```tsx
<section style={{ padding: '0 var(--spacing-md)', maxWidth: '800px', margin: 'var(--spacing-lg) auto 0' }}>
    <ChatPanel />
</section>
```

- [ ] **Step 6: TypeScript compile check**

```bash
cd my-app && npx tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 7: End-to-end test**

Complete a full diagnosis. Wait ~5 seconds for background ingestion. Type "What was my diagnosis?" in the chat panel.
Expected: answer references the completed session's findings.

- [ ] **Step 8: Commit**

```bash
git add my-app/src/hooks/useChat.ts my-app/src/components/medical/ChatPanel.tsx my-app/src/services/api.ts my-app/src/views/diagnosis.tsx
git commit -m "feat(sp2): add RAG chatbot frontend — ChatPanel + useChat hook + askChat API method"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task(s) |
|---|---|
| Delete `workflow_state_manager.py` | Task 5 |
| Routing in LangGraph conditional edges | Task 2 (`_route_after_diagnosis`, `_route_after_followup`) |
| `AsyncPostgresSaver` — scales across workers | Task 3 |
| No `previous_state` in request body | Tasks 4, 6 |
| RAG chatbot retrieves from past diagnostic history | Tasks 9, 10, 11, 12 |
| Gemini `text-embedding-004` (API-first, no local model) | Task 8 |
| Supabase pgvector | Task 7 |
| Report auto-ingestion via `BackgroundTasks` | Task 12 |
| PHI disclaimer UI | Not here — SP3/SP4 scope |
| No duplicate routing logic | Achieved: one file, two functions |

**Placeholder scan:** None — all steps have complete code.

**Type consistency:** `ChatState` defined in Task 10, used in Tasks 11, 13. `AgentState` unchanged. `_get_workflow_info(graph, config, state)` signature identical in Tasks 4 and 12.
