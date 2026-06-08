# Future LLM Architecture — Self-Hosted Medical Inference

This document describes the production target for MediSage's LLM inference layer.
The current implementation (Groq) is a placeholder designed to swap to this architecture
with env var changes only.

---

## Why Self-Hosted

The Groq (cloud API) setup used in development sends text symptom data to a third-party
infrastructure provider. For a production healthcare system with full PHI compliance,
inference must run on controlled infrastructure — no BAA required, no data leaving your
servers.

---

## Target Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Inference server | **vLLM** | Industry standard for open-source LLM serving. OpenAI-compatible REST API. Continuous batching for high throughput. |
| Hosting | **Modal** | Serverless GPU. Auto-scales to zero (pay per request). Handles cold starts, GPU provisioning, and HTTPS endpoint automatically. |
| Primary model | **Meditron-70B** | Fine-tuned on PubMed abstracts and clinical guidelines. Strong medical reasoning. |
| Alternative model | **OpenBioLLM-Llama3-70B** | Fine-tuned on PubMed + MIMIC clinical notes. Good alternative if Meditron performance is insufficient. |
| Fallback hosting | **RunPod** | Cheaper for steady high-load deployments. Less developer-friendly than Modal but lower hourly cost on dedicated pods. |

---

## Why vLLM + Modal

vLLM exposes an **OpenAI-compatible REST API** — the same interface Groq uses. This means
the `LLMClient` in `backend/llm/client.py` requires zero code changes. The swap is purely
configuration:

```env
# Current (Groq — development/portfolio demo)
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...

# Future (vLLM on Modal — self-hosted production)
LLM_BASE_URL=https://your-medisage-inference.modal.run/v1
LLM_MODEL=meditron-70b
LLM_API_KEY=your-internal-key
```

Modal deploys vLLM as a persistent app with a stable HTTPS endpoint. You push a Modal
deployment script once; the endpoint URL stays fixed. GPU instances spin up on demand
and scale to zero when idle.

---

## Migration Path

1. Fine-tune or validate Meditron-70B on MediSage's prompt format
2. Write a Modal deployment script that serves the model via vLLM
3. Deploy to Modal, get the endpoint URL
4. Update three env vars in production secrets (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`)
5. No code changes required

---

## Cost Estimate (Modal + vLLM)

- A100 80GB on Modal: ~$0.000164/second (~$0.59/hr)
- A 70B model at ~20 tokens/second handles ~1 request at a time
- At 100 concurrent daily users with 5-minute sessions: ~$2–5/day
- Scale-to-zero means idle periods cost nothing
