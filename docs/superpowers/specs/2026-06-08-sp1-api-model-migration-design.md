# SP1: API Model Migration Design

**Date:** 2026-06-08
**Status:** Approved
**Scope:** Replace local model stack with provider-abstracted API inference. Remove image analysis and WebSocket subsystems.

---

## Context

MediSage currently runs a 4GB Llama 3.1-8B GGUF model and an EfficientNetB0 skin lesion classifier locally via `llama-cpp-python` and PyTorch. This makes the Docker image ~6GB, requires a CUDA-capable GPU, and prevents horizontal scaling. WebSocket infrastructure exists but is entirely commented out and unused.

This sub-project migrates inference to an OpenAI-compatible API (current: Groq Llama 3.3 70B), removes the image classification feature, and removes the WebSocket dead code. The result is a stateless, GPU-free backend that can be replicated freely.

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM inference | Groq (Llama 3.3 70B) via OpenAI-compatible API | Free dev tier, fastest inference (LPU), ~$0.002/session at paid tier |
| Provider interface | OpenAI Python SDK (`AsyncOpenAI`, `base_url` from env) | vLLM on Modal exposes the same interface — future swap is env-var only |
| Future production target | vLLM on Modal serving Meditron-70B or equivalent medical fine-tune | Full PHI data sovereignty, no BAA required |
| Image classification | Removed entirely | EfficientNet not clinically validated; skin cancer detection without certainty is a liability |
| WebSocket | Removed entirely | Workflow is sequential request/response; loading spinner is sufficient |
| Python / FastAPI | Retained | Async I/O makes it I/O-bound (waiting on API); GIL is not a bottleneck here |

---

## Architecture

### Before

```
main.py startup
  └── model_manager.load_all_models()
        ├── LocalLlamaAdapter (4GB GGUF, CUDA)
        ├── EfficientNetB0 (skin lesion classifier)
        └── SentenceTransformer (embeddings)

Nodes → LocalLlamaAdapter.generate(prompt)
ImageClassificationNode → EfficientNet.predict(image)
websocket_manager.py → ConnectionManager (unused)
```

### After

```
main.py startup
  └── validate env vars + LLM connectivity health ping

backend/llm/client.py
  └── LLMClient (AsyncOpenAI, base_url/model/api_key from env)

Nodes → await llm_client.complete(messages)
ImageClassificationNode → DELETED
websocket_manager.py → DELETED
model_manager.py → DELETED
```

---

## Files Changed

### Deleted entirely

| File | Reason |
|------|--------|
| `backend/managers/model_manager.py` | No local models |
| `backend/managers/websocket_manager.py` | No WebSocket |
| `backend/nodes/image_classification_node.py` | EfficientNet removed |

### New file

**`backend/llm/client.py`**

```python
from openai import AsyncOpenAI
from backend.config import settings

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
        self.model = settings.LLM_MODEL

    async def complete(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

llm_client = LLMClient()
```

### Modified files

**`backend/main.py`**
- Remove: `model_manager` import and `load_all_models()` lifespan block
- Remove: `ConnectionManager` import and `manager = ConnectionManager()` instantiation
- Remove: all commented-out WebSocket endpoint code (lines 86–108)
- Remove: `ImageClassificationNode` from node imports and `initialize_nodes_once()` call
- Simplify lifespan to: validate env vars, run LLM health ping, log available routes

**`backend/api/diagnosis_routes.py`**
- Remove: `/patient/image_analysis` route and all image upload handling
- Remove: `initialize_nodes_once` references to `ImageClassificationNode`
- Update: node imports to exclude image node

**`backend/managers/workflow_state_manager.py`**
- Remove: `image_analysis` stage block (lines 129–151)
- Remove: `image_required` references and `image_upload` needs_user_input paths

**`backend/graphs/patient_workflow.py`**
- Remove: `ImageClassificationNode` from graph nodes
- Remove: edges routing to/from image analysis

**`backend/nodes/__init__.py`**
- Remove: `ImageClassificationNode` export

**All LLM nodes** (`llm_diagnosis_node.py`, `follow_up_interaction_node.py`, `overall_analysis_node.py`, `medical_report_node.py`)
- Replace: `self.local_adapter.generate(prompt)` with `await llm_client.complete(messages)`
- Remove: model adapter constructor injection

**`backend/requirements.txt`**
- Remove: `llama-cpp-python`, `torch`, `torchvision`, `Pillow` (no local inference, no image processing)
- Remove: `sentence-transformers` (currently loaded by model_manager on-demand; SP2 will re-add it when RAG is built)
- Add: `openai>=1.0.0` (OpenAI-compatible SDK used by LLMClient)

---

## Configuration

New environment variables (added to `.env` and `.env.example`):

```env
# LLM Provider (OpenAI-compatible — see docs/FUTURE_LLM_ARCHITECTURE.md for production target)
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
```

Swapping to the self-hosted vLLM/Modal stack requires only changing these three env vars.
See [docs/FUTURE_LLM_ARCHITECTURE.md](../../FUTURE_LLM_ARCHITECTURE.md) for the full production architecture.

Remove from `.env`: all `MODEL_PATH`, `GPU_LAYERS`, `N_CTX`, `EMBEDDING_MODEL` vars.

---

## Privacy Policy Gate

### Database
Add column to Supabase `users` table:
```sql
ALTER TABLE users ADD COLUMN privacy_policy_accepted boolean NOT NULL DEFAULT false;
```

### Backend
FastAPI dependency on all `/patient/*` routes:
```python
async def require_privacy_policy(current_user = Depends(get_current_user)):
    if not current_user.privacy_policy_accepted:
        raise HTTPException(status_code=403, detail="privacy_policy_required")
```

New route: `PATCH /auth/accept-privacy-policy` — sets flag to `true` for current user.

### Frontend
On `403 privacy_policy_required` response from any `/patient/*` call, show a one-time consent modal:

> "Your symptom descriptions will be processed by Groq AI infrastructure to generate medical guidance. By continuing you accept our Privacy Policy. Do not enter personally identifying information in symptom fields."

Two buttons: **Accept & Continue** (calls PATCH, retries request) and **Cancel**.

---

## What This SP Does NOT Change

- `workflow_state_manager.py` routing logic beyond removing image branches — SP2
- LangGraph graph structure and conditional edges — SP2
- Frontend UI/UX — SP4
- Deployment, Docker, security hardening — SP5
- Sentence-transformers embeddings model — removed from requirements in SP1 (its only initializer, `model_manager.py`, is deleted); SP2 re-adds it when building the RAG pipeline

---

## Success Criteria

- [ ] Backend starts without loading any local model files
- [ ] All four LLM nodes return valid responses via Groq API
- [ ] `/patient/image_analysis` route returns 404
- [ ] `docker build` produces an image with no CUDA dependencies, under 500MB
- [ ] Startup logs show LLM connectivity ping, not model loading
- [ ] New user attempting diagnosis without accepting privacy policy receives `403`
- [ ] Accepting privacy policy allows diagnosis to proceed
