# SP1: API Model Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the local GGUF/EfficientNet stack with a provider-abstracted Groq API client, remove all WebSocket and image analysis dead code, and add a privacy policy gate on all `/patient/*` routes.

**Architecture:** A new `backend/llm/client.py` singleton wraps `AsyncOpenAI` with `base_url`/`model`/`api_key` from env vars. All four LLM nodes drop their `LocalModelAdapter` constructor injection and call `await llm_client.complete(messages)` directly with inlined prompts. Three files are deleted entirely (`model_manager.py`, `websocket_manager.py`, `image_classification_node.py`). A `privacy_policy_accepted` column on `user_profiles` gates all `/patient/*` routes via a FastAPI dependency.

**Tech Stack:** Python 3.11, FastAPI, `openai>=1.0.0` (AsyncOpenAI for Groq), LangGraph, Supabase PostgreSQL, React 18 + TypeScript, styled-components, pytest + pytest-asyncio.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `backend/config.py` | Settings singleton: LLM_BASE_URL, LLM_MODEL, LLM_API_KEY |
| Create | `backend/llm/__init__.py` | Package marker |
| Create | `backend/llm/client.py` | LLMClient class + `llm_client` singleton |
| Create | `backend/tests/__init__.py` | Package marker |
| Create | `backend/tests/test_llm_client.py` | Unit tests for LLMClient |
| Create | `backend/migrations/001_privacy_policy.sql` | Supabase migration |
| Create | `my-app/src/components/medical/PrivacyPolicyModal.tsx` | Consent modal |
| Modify | `backend/requirements.txt` | Drop local deps, add openai |
| Modify | `backend/nodes/llm_diagnosis_node.py` | Drop adapter, inline prompt |
| Modify | `backend/nodes/follow_up_interaction_node.py` | Drop adapter, inline prompt, fix high-risk path |
| Modify | `backend/nodes/overall_analysis_node.py` | Drop adapter, inline prompts, remove image instance |
| Modify | `backend/nodes/medical_report_node.py` | Drop adapter, inline prompt, update footer |
| Modify | `backend/nodes/__init__.py` | Remove ImageClassificationNode export |
| Modify | `backend/schemas/medical_schemas.py` | Remove image fields/stages/path types |
| Modify | `backend/managers/workflow_state_manager.py` | Remove image_analysis stage block |
| Modify | `backend/api/diagnosis_routes.py` | Drop dead code, add privacy dependency |
| Modify | `backend/api/auth_routes.py` | Drop model_manager, add privacy gate fn + endpoint |
| Modify | `backend/main.py` | Drop model loading, add LLM health ping |
| Modify | `my-app/src/hooks/useDiagnosis.ts` | Handle PrivacyPolicyRequiredError |
| Modify | `my-app/src/services/api.ts` | Throw PrivacyPolicyRequiredError on 403, add acceptPrivacyPolicy() |
| Delete | `backend/managers/model_manager.py` | Local model orchestration — gone |
| Delete | `backend/managers/websocket_manager.py` | ConnectionManager — gone |
| Delete | `backend/nodes/image_classification_node.py` | EfficientNet node — gone |

---

## Task 0: Initialize Git

**Files:** (none — git only)

- [ ] **Step 1: Initialize the repo**

```bash
cd c:/Users/user/Desktop/MediSage
git init
git add .
git commit -m "chore: initial commit — pre-SP1 baseline"
```

Expected: `[main (root-commit) xxxxxxx] chore: initial commit — pre-SP1 baseline`

---

## Task 1: Requirements + Config + Environment

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/.env.example`

- [ ] **Step 1: Rewrite requirements.txt**

Replace the entire file with:

```
fastapi
uvicorn
python-dotenv
requests
aiofiles
langchain
langgraph
pydantic
supabase
PyJWT
openai>=1.0.0
reportlab==4.0.4
python-docx==1.1.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx
```

Removed: `llama-cpp-python[cublas]`, `torch`, `torchvision`, `sentence-transformers`, `pillow`, `transformers`, `scikit-learn`, `scipy`, `numpy<2.0`, `google-maps-services`, `asyncio` (stdlib — not a pip package)

- [ ] **Step 2: Create backend/config.py**

```python
import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

settings = Settings()
```

- [ ] **Step 3: Create backend/.env.example**

```env
# LLM Provider — OpenAI-compatible
# See docs/FUTURE_LLM_ARCHITECTURE.md to swap to self-hosted vLLM on Modal
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_your_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-anon-key

# JWT
JWT_SECRET=your-jwt-secret
```

- [ ] **Step 4: Update backend/.env with new variables**

Open `backend/.env`. Remove any lines containing:
`MODEL_PATH`, `GPU_LAYERS`, `N_CTX`, `EMBEDDING_MODEL`, `EFFICIENTNET_MODEL_PATH`

Add these three lines (get your key from console.groq.com):
```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_your_actual_key_here
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/config.py backend/.env.example
git commit -m "chore(sp1): clean requirements, add config.py and env template"
```

---

## Task 2: LLMClient (TDD)

**Files:**
- Create: `backend/llm/__init__.py`
- Create: `backend/llm/client.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_llm_client.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/__init__.py` as an empty file.

Create `backend/tests/test_llm_client.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_complete_returns_content(monkeypatch):
    """LLMClient.complete() returns the content string from the first response choice."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "- Diagnosis: Common Cold\n- Confidence: 0.85"

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        MockOpenAI.return_value = mock_instance

        from llm.client import LLMClient
        client = LLMClient()
        result = await client.complete([{"role": "user", "content": "I have a headache"}])

    assert result == "- Diagnosis: Common Cold\n- Confidence: 0.85"


@pytest.mark.asyncio
async def test_complete_forwards_kwargs(monkeypatch):
    """LLMClient.complete() passes max_tokens and temperature through to the API."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "ok"

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        create_spy = AsyncMock(return_value=mock_response)
        mock_instance.chat.completions.create = create_spy
        MockOpenAI.return_value = mock_instance

        from llm.client import LLMClient
        client = LLMClient()
        await client.complete(
            [{"role": "user", "content": "test"}],
            max_tokens=200,
            temperature=0.3
        )

    create_spy.assert_called_once()
    call_kwargs = create_spy.call_args[1]
    assert call_kwargs["max_tokens"] == 200
    assert call_kwargs["temperature"] == 0.3
```

- [ ] **Step 2: Run tests — confirm they fail (module not found)**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -m pytest tests/test_llm_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'llm'`

- [ ] **Step 3: Create backend/llm/__init__.py (empty)**

Create an empty file at `backend/llm/__init__.py`.

- [ ] **Step 4: Create backend/llm/client.py**

```python
import os
from openai import AsyncOpenAI


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.getenv("LLM_API_KEY", ""),
        )
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    async def complete(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


llm_client = LLMClient()
```

- [ ] **Step 5: Run tests — confirm they pass**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -m pytest tests/test_llm_client.py -v
```

Expected:
```
PASSED tests/test_llm_client.py::test_complete_returns_content
PASSED tests/test_llm_client.py::test_complete_forwards_kwargs
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend/llm/ backend/tests/
git commit -m "feat(sp1): add LLMClient with provider-abstracted AsyncOpenAI"
```

---

## Task 3: Update LLMDiagnosisNode

**Files:**
- Modify: `backend/nodes/llm_diagnosis_node.py`

The adapter's `generate_diagnosis()` computed confidence scores via a separate blackbox algorithm. With Groq we ask the model directly for confidence values in [0.0-1.0]. The `parse_diagnosis_details` regex already handles `- Diagnosis: X\n- Confidence: Y` format — no parser change needed.

- [ ] **Step 1: Replace the entire file**

```python
from typing import TypedDict
import re
from schemas.medical_schemas import TextualSymptomAnalysisResult
from llm.client import llm_client


def parse_diagnosis_details(raw_response: str) -> list[TextualSymptomAnalysisResult]:
    results: list[TextualSymptomAnalysisResult] = []

    diagnosis_pattern = re.compile(
        r"-\s*Diagnosis:\s*(.*?)\s*"
        r"-\s*Confidence:\s*([0-9.]+)\s*",
        re.IGNORECASE | re.DOTALL
    )

    for match in diagnosis_pattern.finditer(raw_response):
        diagnosis, confidence = match.groups()
        result: TextualSymptomAnalysisResult = {
            "text_diagnosis": diagnosis.strip(),
            "diagnosis_confidence": float(confidence.strip()),
        }
        results.append(result)

    results.sort(key=lambda x: x["diagnosis_confidence"], reverse=True)
    return results


class LLMDiagnosisNode:
    async def __call__(self, state: dict) -> dict:
        state["current_workflow_stage"] = "textual_analysis"
        print("🩺 LLM DIAGNOSIS NODE CALLED!")
        print(f"    Input: {state.get('latest_user_message', 'NO MESSAGE')}")

        state = await self.diagnose(state)

        workflow_path = []
        workflow_path.append("textual_only")
        state["workflow_path"] = workflow_path

        print(f"✅ LLM Diagnosis complete — found {len(state.get('textual_analysis', []))} diagnoses")
        return state

    async def diagnose(self, state: dict) -> dict:
        text = state.get("latest_user_message", "")

        skin_cancer_keywords = [
            'mole', 'lesion', 'growth', 'bump', 'spot', 'rash', 'patch', 'scab',
            'discoloration', 'freckle', 'birthmark', 'wart', 'cyst', 'lump',
            'melanoma', 'cancer', 'tumor', 'nevus', 'seborrheic', 'keratosis'
        ]
        general_skin_keywords = [
            'skin', 'dermatitis', 'eczema', 'psoriasis', 'acne', 'hives',
            'rosacea', 'fungal', 'bacterial', 'viral', 'infection'
        ]

        has_skin_cancer_indicators = any(kw in text.lower() for kw in skin_cancer_keywords)
        has_general_skin_symptoms = any(kw in text.lower() for kw in general_skin_keywords)

        if has_skin_cancer_indicators or has_general_skin_symptoms:
            state["userInput_skin_symptoms"] = text
            state["requires_skin_cancer_screening"] = True
            state["textual_analysis"] = [
                {"text_diagnosis": "Possible Skin Cancer Condition (Further Evaluation Required)", "diagnosis_confidence": None}
            ]
            state["average_confidence"] = 0.0
            return state

        state["userInput_symptoms"] = text
        state["requires_skin_cancer_screening"] = False

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant. Provide accurate, structured responses. "
                    "Always follow the exact format requested. Be concise and professional."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Symptoms: {text}\n"
                    "List 5 most possible diagnoses in this exact format ONLY:\n"
                    "- Diagnosis: <name>\n"
                    "- Confidence: <0.0-1.0>\n\n"
                    "Repeat for each diagnosis. List from most likely to least likely."
                ),
            },
        ]

        output = await llm_client.complete(messages, max_tokens=300, temperature=0.1)
        parsed_diagnosis = parse_diagnosis_details(output)

        state["textual_analysis"] = parsed_diagnosis
        state["image_required"] = False
        return state
```

- [ ] **Step 2: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from nodes.llm_diagnosis_node import LLMDiagnosisNode, parse_diagnosis_details; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/nodes/llm_diagnosis_node.py
git commit -m "feat(sp1): LLMDiagnosisNode — replace LocalModelAdapter with llm_client"
```

---

## Task 4: Update FollowUpInteractionNode

**Files:**
- Modify: `backend/nodes/follow_up_interaction_node.py`

Two changes: (1) replace `self.adapter.generate_diagnosis()` in the standard follow-up path with `llm_client.complete()`; (2) change the high-ABCDE-risk branch from `image_required=True` (routing to the deleted image endpoint) to `image_required=False` (routes to overall_analysis). Also remove the dead `from ray import state` import at line 1.

- [ ] **Step 1: Replace the import block and class constructor**

Old (lines 1-11):
```python
from ray import state
from adapters.local_model_adapter4 import LocalModelAdapter
from typing import Dict, Any, List
import re

#followup_response contain both qna pairs, the parsing is used to combine initial user input and structured qna 
#for context later (followup_qna_overall)

class FollowUpInteractionNode:
    def __init__(self, adapter: LocalModelAdapter):
        self.adapter = adapter
```

New:
```python
from typing import Dict, Any, List
import re
from llm.client import llm_client


class FollowUpInteractionNode:
    pass  # no adapter — llm_client is module-level singleton
```

- [ ] **Step 2: Replace the adapter call in the standard follow-up path**

Find (around line 151 in the original after removing the header):
```python
            print(f"🔄 Generating standard follow-up diagnosis with enhanced symptoms...")
            output = await self.adapter.generate_diagnosis(enhanced_symptoms)
```

Replace with:
```python
            print(f"🔄 Generating standard follow-up diagnosis with enhanced symptoms...")
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an AI medical assistant. Provide accurate, structured responses. "
                        "Always follow the exact format requested. Be concise and professional."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Symptoms: {enhanced_symptoms}\n"
                        "List 5 most possible diagnoses in this exact format ONLY:\n"
                        "- Diagnosis: <name>\n"
                        "- Confidence: <0.0-1.0>\n\n"
                        "Repeat for each diagnosis. List from most likely to least likely."
                    ),
                },
            ]
            output = await llm_client.complete(messages, max_tokens=300, temperature=0.1)
```

- [ ] **Step 3: Fix the high-ABCDE-risk branch**

Find:
```python
            if needs_image_analysis: ## skin cancer screening only
                print("🔍 SKIN CANCER RISK DETECTED - proceeding to image analysis")
                state["image_required"] = True
                state["skin_cancer_risk_detected"] = True
                state["current_workflow_stage"] = "awaiting_image_upload"
                
                enhanced_diagnosis = [
                    {"text_diagnosis": "Skin Cancer Risk Detected - Image Analysis Required", "diagnosis_confidence": None}
                ]
                state["followup_diagnosis"] = enhanced_diagnosis
                
                return state
```

Replace with:
```python
            if needs_image_analysis:  # high ABCDE risk — route directly to overall analysis
                print("🔍 HIGH ABCDE RISK DETECTED — routing to overall analysis")
                state["image_required"] = False
                state["skin_cancer_risk_detected"] = True
                state["current_workflow_stage"] = "followup_analysis_complete"
                state["requires_user_input"] = False

                state["followup_diagnosis"] = [
                    {"text_diagnosis": "High-risk skin lesion features detected (ABCDE criteria)", "diagnosis_confidence": 0.0}
                ]

                workflow_path = state.get("workflow_path", [])
                if "skin_cancer_high_risk" not in workflow_path:
                    workflow_path.append("skin_cancer_high_risk")
                state["workflow_path"] = workflow_path

                return state
```

- [ ] **Step 4: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from nodes.follow_up_interaction_node import FollowUpInteractionNode; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/nodes/follow_up_interaction_node.py
git commit -m "feat(sp1): FollowUpInteractionNode — replace adapter, fix high-risk skin path"
```

---

## Task 5: Update OverallAnalysisNode

**Files:**
- Modify: `backend/nodes/overall_analysis_node.py`

Remove `_analyze_textual_and_image` and `_parse_llm_skin_synthesis` entirely. Replace both adapter calls with `llm_client.complete()` using the same prompt text from the old adapter. Add `"skin_cancer_high_risk"` to the followup path check.

- [ ] **Step 1: Replace the entire file**

```python
from typing import Dict, Any, List
import re
from llm.client import llm_client

_SYSTEM_PROMPT = (
    "You are an AI medical assistant. Provide accurate, structured responses. "
    "Always follow the exact format requested. Be concise and professional."
)


class OverallAnalysisNode:
    async def __call__(self, state):
        print("OVERALL ANALYSIS NODE CALLED!")
        state["current_workflow_stage"] = "performing_overall_analysis"
        state = await self.perform_overall_analysis(state)
        state["current_workflow_stage"] = "overall_analysis_complete"
        return state

    async def perform_overall_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            workflow_path = state.get("workflow_path", [])
            print(f"WORKFLOW PATH: {workflow_path}")

            if workflow_path == ["textual_only"]:
                enhanced_analysis = await self._analyze_textual_only(state)
            elif (
                "followup_only" in workflow_path
                or "skin_to_standard_followup" in workflow_path
                or "skin_cancer_high_risk" in workflow_path
            ):
                enhanced_analysis = await self._analyze_textual_and_followup(state)
            else:
                enhanced_analysis = await self._analyze_fallback(state)

            state["overall_analysis"] = enhanced_analysis
            print(f"✅ Overall analysis complete: {enhanced_analysis.get('final_diagnosis', 'Unknown')}")
            return state

        except Exception as e:
            print(f"❌ Overall analysis error: {e}")
            state["overall_analysis"] = self._fallback_analysis(state)
            return state

    async def _analyze_textual_only(self, state: Dict[str, Any]) -> Dict[str, Any]:
        userInput_symptoms = state.get("userInput_symptoms", "")
        textual_analysis = state.get("textual_analysis", [])

        if not textual_analysis:
            raise ValueError("No textual analysis available")

        primary_diagnosis = textual_analysis[0]
        diagnosis = primary_diagnosis.get("text_diagnosis", "Unknown")
        confidence = primary_diagnosis.get("diagnosis_confidence", 0.0) or 0.0

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"MEDICAL ANALYSIS\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})\n"
                    f"Original Symptoms: {userInput_symptoms}\n\n"
                    f"Based on the confirmed diagnosis above, provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification based on user's original symptom "
                    f"({userInput_symptoms}) & confirmed diagnosis ({diagnosis})>\n"
                    f"- Specialist: <choose MOST appropriate specialist type (separate with \" / \" if more than one)>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]

        assessment_text = await llm_client.complete(messages, max_tokens=400, temperature=0.3)
        return self._parse_enhanced_analysis(assessment_text, primary_diagnosis)

    async def _analyze_textual_and_followup(self, state: Dict[str, Any]) -> Dict[str, Any]:
        followup_qna = state.get("followup_qna_overall", "")
        followup_diagnosis = state.get("followup_diagnosis", [])

        if not followup_diagnosis:
            raise ValueError("No follow-up diagnosis available")

        enhanced_diagnosis = followup_diagnosis[0]
        diagnosis = enhanced_diagnosis.get("text_diagnosis", "Unknown")
        confidence = enhanced_diagnosis.get("diagnosis_confidence", 0.0) or 0.0

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"ENHANCED MEDICAL ANALYSIS\n\n"
                    f"Follow-up Information:\n{followup_qna}\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})\n\n"
                    f"Based on the confirmed diagnosis above, provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification based on user's follow-up "
                    f"information & confirmed diagnosis stated above>\n"
                    f"- Specialist: <choose MOST appropriate specialist type (separate with \" / \" if more than one)>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]

        assessment_text = await llm_client.complete(messages, max_tokens=400, temperature=0.3)
        return self._parse_enhanced_analysis(assessment_text, enhanced_diagnosis)

    async def _analyze_fallback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        textual_analysis = state.get("textual_analysis", [])
        primary = textual_analysis[0] if textual_analysis else {
            "text_diagnosis": "Unknown", "diagnosis_confidence": 0.0
        }
        return {
            "final_diagnosis": primary.get("text_diagnosis", "Unknown"),
            "final_confidence": primary.get("diagnosis_confidence", 0.0) or 0.0,
            "final_severity": "moderate",
            "user_explanation": "Analysis completed based on available symptom data.",
            "clinical_reasoning": "Systematic symptom analysis performed.",
            "specialist_recommendation": "general_practitioner",
        }

    def _parse_enhanced_analysis(self, assessment_text: str, primary_diagnosis: dict) -> Dict[str, Any]:
        severity_match = re.search(r"-\s*Severity:\s*(.+)", assessment_text, re.IGNORECASE)
        explanation_match = re.search(
            r"-\s*User Explanation:\s*(.+?)(?:\n-|\Z)", assessment_text, re.IGNORECASE | re.DOTALL
        )
        reasoning_match = re.search(
            r"-\s*Clinical Reasoning:\s*(.+?)(?:\n-|\Z)", assessment_text, re.IGNORECASE | re.DOTALL
        )
        specialist_match = re.search(r"-\s*Specialist:\s*(.+)", assessment_text, re.IGNORECASE)

        severity = severity_match.group(1).strip() if severity_match else "moderate"
        user_explanation = explanation_match.group(1).strip() if explanation_match else "Analysis completed."
        clinical_reasoning = reasoning_match.group(1).strip() if reasoning_match else "Systematic analysis performed."
        specialist = specialist_match.group(1).strip() if specialist_match else "general_practitioner"

        if severity.lower() not in {"mild", "moderate", "severe", "critical"}:
            severity = "moderate"

        return {
            "final_diagnosis": primary_diagnosis.get("text_diagnosis", "Unknown"),
            "final_confidence": primary_diagnosis.get("diagnosis_confidence", 0.0) or 0.0,
            "final_severity": severity.lower(),
            "user_explanation": user_explanation,
            "clinical_reasoning": clinical_reasoning,
            "specialist_recommendation": specialist,
        }

    def _fallback_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        textual_analysis = state.get("textual_analysis", [])
        primary = textual_analysis[0] if textual_analysis else {}
        return {
            "final_diagnosis": primary.get("text_diagnosis", "Analysis incomplete"),
            "final_confidence": 0.0,
            "final_severity": "moderate",
            "user_explanation": "Unable to complete full analysis.",
            "clinical_reasoning": "Analysis encountered an error.",
            "specialist_recommendation": "general_practitioner",
        }
```

- [ ] **Step 2: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from nodes.overall_analysis_node import OverallAnalysisNode; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/nodes/overall_analysis_node.py
git commit -m "feat(sp1): OverallAnalysisNode — replace adapter, remove image instance"
```

---

## Task 6: Update MedicalReportNode

**Files:**
- Modify: `backend/nodes/medical_report_node.py`

Remove `adapter` from constructor (keep `supabase_client`). Replace `self.adapter.generate_text_guidance()` with `llm_client.complete()`. Update the report footer from "Llama 3.1 8B UltraMedical" to "Groq Llama 3.3 70B".

- [ ] **Step 1: Replace the import block and constructor**

Old (lines 1-30):
```python
from adapters.local_model_adapter4 import LocalModelAdapter
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import re
import logging

# PDF/Word imports 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from io import BytesIO

# Database imports
from supabase import Client
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class MedicalReportNode:
    def __init__(self, adapter: LocalModelAdapter, supabase_client: Optional[Client] = None):
        self.adapter = adapter
        
        # Initialize Supabase client for database operations
        if supabase_client:
            self.supabase = supabase_client
```

New:
```python
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import re
import logging
import os
from dotenv import load_dotenv

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from io import BytesIO
from supabase import Client

from llm.client import llm_client

load_dotenv()
logger = logging.getLogger(__name__)


class MedicalReportNode:
    def __init__(self, supabase_client: Optional[Client] = None):
        if supabase_client:
            self.supabase = supabase_client
```

- [ ] **Step 2: Replace the adapter call in `_generate_followup_guidance`**

Find:
```python
        followup_guidance = await self.adapter.generate_text_guidance(followup_prompt, 200, 0.2)
```

Replace with:
```python
        followup_guidance = await llm_client.complete(
            [{"role": "user", "content": followup_prompt}],
            max_tokens=200,
            temperature=0.2,
        )
```

- [ ] **Step 3: Update the report footer text**

Run this to find occurrences:
```bash
grep -n "Llama 3.1\|UltraMedical\|8-bit\|GGUF" c:/Users/user/Desktop/MediSage/backend/nodes/medical_report_node.py
```

For each match, replace the model attribution string with:
```
Groq Llama 3.3 70B
```

- [ ] **Step 4: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from nodes.medical_report_node import MedicalReportNode; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/nodes/medical_report_node.py
git commit -m "feat(sp1): MedicalReportNode — remove adapter injection, update footer"
```

---

## Task 7: Delete Dead Files + Update nodes/__init__.py

**Files:**
- Delete: `backend/managers/model_manager.py`
- Delete: `backend/managers/websocket_manager.py`
- Delete: `backend/nodes/image_classification_node.py`
- Modify: `backend/nodes/__init__.py`

- [ ] **Step 1: Delete the three dead files**

```bash
rm "c:/Users/user/Desktop/MediSage/backend/managers/model_manager.py"
rm "c:/Users/user/Desktop/MediSage/backend/managers/websocket_manager.py"
rm "c:/Users/user/Desktop/MediSage/backend/nodes/image_classification_node.py"
```

- [ ] **Step 2: Replace nodes/__init__.py**

```python
from .llm_diagnosis_node import LLMDiagnosisNode
from .follow_up_interaction_node import FollowUpInteractionNode
from .overall_analysis_node import OverallAnalysisNode
from .medical_report_node import MedicalReportNode


__all__ = [
    "LLMDiagnosisNode",
    "FollowUpInteractionNode",
    "OverallAnalysisNode",
    "MedicalReportNode",
]
```

- [ ] **Step 3: Verify nodes package imports cleanly**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from nodes import LLMDiagnosisNode, FollowUpInteractionNode, OverallAnalysisNode, MedicalReportNode; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add -u
git add backend/nodes/__init__.py
git commit -m "chore(sp1): delete model_manager, websocket_manager, image_classification_node"
```

---

## Task 8: Update Schemas + WorkflowStateManager

**Files:**
- Modify: `backend/schemas/medical_schemas.py`
- Modify: `backend/managers/workflow_state_manager.py`

- [ ] **Step 1: Remove image stages from WorkflowStage**

In `medical_schemas.py`, remove these three lines from the `WorkflowStage` Literal:
```python
    "awaiting_image_upload",
    "analyzing_image",
    "image_analysis_complete",
```

- [ ] **Step 2: Replace WorkflowPathType**

Old:
```python
WorkflowPathType = Literal[
    "textual_only",
    "textual_to_image",
    "textual_to_skin_screening",
    "skin_to_image_analysis",
    "textual_to_followup",
    "followup_only",
    "skin_to_standard_followup"
]
```

New:
```python
WorkflowPathType = Literal[
    "textual_only",
    "textual_to_skin_screening",
    "textual_to_followup",
    "followup_only",
    "skin_to_standard_followup",
    "skin_cancer_high_risk",
]
```

- [ ] **Step 3: Remove image_upload from WorkflowInfo**

Old:
```python
    needs_user_input: Literal["followup_questions", "image_upload"] | None
```

New:
```python
    needs_user_input: Literal["followup_questions"] | None
```

- [ ] **Step 4: Remove image fields from AgentState**

Delete the `image_required: bool` line and the entire `#STAGE 2` block:
```python
    image_required: bool
    ...
    #STAGE 2: Skin LesionImage Analysis (Optional)
    userInput_skin_symptoms: str | None
    skin_cancer_screening_responses: str | None
    image_input: str | None
    skin_lesion_analysis: SkinLesionImageAnalysisResult | None
```

Also delete the `SkinLesionImageAnalysisResult` TypedDict definition (it's now unreferenced):
```python
class SkinLesionImageAnalysisResult(TypedDict):
    image_diagnosis: str | None
    confidence_score: Union[dict[str, float]] | None
```

- [ ] **Step 5: Remove image_analysis stage block from workflow_state_manager.py**

Delete the entire `elif completed_node == "image_analysis":` block (approximately lines 128-151):
```python
        #STAGE 3: Image Analysis Complete
        elif completed_node == "image_analysis":
            ...
            return {
                "current_stage": "image_analysis_complete",
                ...
            }
```

- [ ] **Step 6: Remove image_required check in followup_interaction case**

In workflow_state_manager.py's `followup_interaction` handling, find this block:
```python
            if state.get("image_required", False):
                next_endpoint = "/patient/image_analysis"
                needs_user_input = "image_upload"
                next_step_description = "Medical image upload required for enhanced diagnosis"
                
                state["workflow_path"] = ["textual_to_skin_screening", "skin_to_image_analysis"]
            else: 
            ## standard follow-up only
                logger.info("🔄 Standard follow-up analysis complete - no image required")
                next_endpoint = "/patient/overall_analysis"
                needs_user_input = None
                next_step_description = "Ready for comprehensive analysis with follow-up data"
```

Replace with just the else body (always route to overall_analysis):
```python
            logger.info("🔄 Follow-up analysis complete — proceeding to overall analysis")
            next_endpoint = "/patient/overall_analysis"
            needs_user_input = None
            next_step_description = "Ready for comprehensive analysis with follow-up data"
```

- [ ] **Step 7: Verify schemas and state manager import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from schemas.medical_schemas import AgentState, WorkflowStage, WorkflowPathType; print('OK')"
python -c "from managers.workflow_state_manager import workflow_state_manager; print('OK')"
```

Expected: `OK` for both.

- [ ] **Step 8: Commit**

```bash
git add backend/schemas/medical_schemas.py backend/managers/workflow_state_manager.py
git commit -m "chore(sp1): remove image-related fields from schemas and state manager"
```

---

## Task 9: Rewrite diagnosis_routes.py

**Files:**
- Modify: `backend/api/diagnosis_routes.py`

Remove: all WebSocket send calls, `image_analysis` route, `initialize_nodes_once`, `ensure_nodes_initialized`, `get_image_classification_node`, `diagnose_patient_realtime`, `run_workflow_with_updates`, `execute_workflow_with_monitoring`, `get_session_status`, `terminate_session`, `list_active_connections`.

Add: `require_privacy_policy` dependency on all `/patient/*` routes. Nodes instantiated directly at module level (no lazy loading needed).

- [ ] **Step 1: Replace the entire file**

```python
from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi.responses import Response
from typing import Optional, Dict
import uuid
from datetime import datetime
import logging
import json

from nodes import LLMDiagnosisNode, FollowUpInteractionNode, OverallAnalysisNode, MedicalReportNode
from schemas.medical_schemas import AgentState
from managers.workflow_state_manager import workflow_state_manager
from api.auth_routes import require_privacy_policy

diagnosis_router = APIRouter()
logger = logging.getLogger(__name__)

# Stateless nodes — no adapters, safe to instantiate at module level
llm_diagnosis_node = LLMDiagnosisNode()
followup_interaction_node = FollowUpInteractionNode()
overall_analysis_node = OverallAnalysisNode()
medical_report_node = MedicalReportNode()

# In-memory session store (keyed by session_id)
session_states: Dict[str, AgentState] = {}


def get_or_create_session_state(session_id: str, initial_state: Optional[AgentState] = None) -> AgentState:
    if session_id not in session_states:
        session_states[session_id] = initial_state or AgentState(
            session_id=session_id,
            latest_user_message="",
        )
    return session_states[session_id]


def update_session_state(session_id: str, updated_state: AgentState) -> None:
    session_states[session_id] = updated_state


# NODE 1: Textual Analysis
@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_textual_analysis(
    user_symptoms: str = Form(..., description="Patient symptoms"),
    session_id: Optional[str] = Form(None),
):
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:8]}"

    try:
        state = get_or_create_session_state(session_id, AgentState(
            session_id=session_id,
            latest_user_message=user_symptoms,
            userInput_symptoms=user_symptoms,
            current_workflow_stage="initializing",
        ))

        result = await llm_diagnosis_node(state)

        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "textual_analysis"
        )
        update_session_state(session_id, result)

        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NODE 2: Follow-up Questions
@diagnosis_router.post("/patient/followup_questions", dependencies=[Depends(require_privacy_policy)])
async def run_followup_questions(
    session_id: str = Form(...),
    previous_state: str = Form(...),
    followup_responses: Optional[str] = Form(None),
):
    try:
        state = json.loads(previous_state)

        if not followup_responses:
            state["requires_user_input"] = True
        else:
            state["followup_response"] = json.loads(followup_responses)
            state["requires_user_input"] = False

        result = await followup_interaction_node(state)

        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "followup_interaction"
        )
        update_session_state(session_id, result)

        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NODE 3: Overall Analysis
@diagnosis_router.post("/patient/overall_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_overall_analysis(
    session_id: str = Form(...),
    previous_state: str = Form(...),
):
    try:
        state = json.loads(previous_state)

        result = await overall_analysis_node(state)

        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "overall_analysis"
        )
        update_session_state(session_id, result)

        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NODE Final: Medical Report
@diagnosis_router.post("/patient/medical_report", dependencies=[Depends(require_privacy_policy)])
async def run_medical_report(
    session_id: str = Form(...),
    previous_state: str = Form(...),
):
    try:
        state = json.loads(previous_state)

        result = await medical_report_node(state)

        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "generate_report"
        )
        update_session_state(session_id, result)

        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }

    except Exception as e:
        logger.error(f"Medical report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export PDF/Word
@diagnosis_router.post("/patient/export_report")
async def export_report_file(
    session_id: str = Form(...),
    format: str = Form(...),
    include_details: bool = Form(True),
    report_data: str = Form(...),
):
    try:
        data = json.loads(report_data)
        session_state = session_states.get(session_id) or data

        file_content = await medical_report_node.generate_export_file(
            state=session_state,
            format=format,
            include_details=include_details,
        )

        if format == "pdf":
            media_type = "application/pdf"
            filename = f"medical-report-{session_id}.pdf"
        elif format == "word":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"medical-report-{session_id}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'word'.")

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
    return {
        "message": "Routes are working!",
        "available_endpoints": [
            "/patient/textual_analysis",
            "/patient/followup_questions",
            "/patient/overall_analysis",
            "/patient/medical_report",
            "/patient/export_report",
            "/health",
        ],
    }


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

- [ ] **Step 2: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from api.diagnosis_routes import diagnosis_router; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp1): diagnosis_routes — remove WebSocket/image/model-manager, add privacy gate"
```

---

## Task 10: Update auth_routes.py

**Files:**
- Modify: `backend/api/auth_routes.py`

Remove: `from managers.model_manager import model_manager` (line 12) and `get_medical_report_node()` lazy-loader (lines 43-53).  
Add: direct `report_node = MedicalReportNode(supabase)` instantiation, `require_privacy_policy` dependency, `PATCH /accept-privacy-policy` endpoint.

- [ ] **Step 1: Remove model_manager import**

Delete line 12:
```python
from managers.model_manager import model_manager
```

- [ ] **Step 2: Replace the lazy-loader with direct instantiation**

Delete:
```python
medical_report_node = None

def get_medical_report_node():
    """Get or create medical report node with loaded adapter"""
    global medical_report_node
    if medical_report_node is None:
        adapter = model_manager.get_local_adapter()
        if adapter is None:
            raise HTTPException(status_code=503, detail="Models not loaded yet")
        medical_report_node = MedicalReportNode(adapter, supabase)
    return medical_report_node
```

Replace with:
```python
report_node = MedicalReportNode(supabase)
```

- [ ] **Step 3: Update all call sites**

Replace every `node = get_medical_report_node()` + `await node.METHOD(...)` pattern with `await report_node.METHOD(...)` directly. There are 5 routes: `get_user_medical_reports`, `get_medical_report`, `save_medical_report`, `delete_medical_report`, `update_report_title`.

Example — old:
```python
    try:
        node = get_medical_report_node()
        reports = await node.get_user_medical_reports(
            user["id"], limit, offset
        )
```

New:
```python
    try:
        reports = await report_node.get_user_medical_reports(
            user["id"], limit, offset
        )
```

Apply this pattern to all 5 routes.

- [ ] **Step 4: Add require_privacy_policy function and accept endpoint**

After the `get_current_user` function (after the closing `return None` line), add:

```python
async def require_privacy_policy(request: Request):
    """FastAPI dependency: 401 if unauthenticated, 403 if privacy policy not accepted."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        result = supabase.table("user_profiles") \
            .select("privacy_policy_accepted") \
            .eq("id", user["id"]) \
            .single() \
            .execute()

        if not result.data or not result.data.get("privacy_policy_accepted"):
            raise HTTPException(status_code=403, detail="privacy_policy_required")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="privacy_policy_required")


@router.patch("/accept-privacy-policy")
async def accept_privacy_policy(request: Request):
    """Mark the current user's privacy_policy_accepted flag as true."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        supabase.table("user_profiles") \
            .update({"privacy_policy_accepted": True}) \
            .eq("id", user["id"]) \
            .execute()
        return {"message": "Privacy policy accepted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 5: Verify import**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from api.auth_routes import router, require_privacy_policy; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/api/auth_routes.py
git commit -m "feat(sp1): auth_routes — remove model_manager, add privacy policy gate"
```

---

## Task 11: Update main.py

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Replace the entire file**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

from api.diagnosis_routes import diagnosis_router
from api.auth_routes import router as auth_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AI Medical Diagnosis API starting...")

    from config import settings
    if not settings.LLM_API_KEY:
        print("⚠️  LLM_API_KEY not set — LLM calls will fail at runtime")
    else:
        try:
            from llm.client import llm_client
            await llm_client.complete(
                [{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            print(f"✅ LLM connectivity confirmed (model: {settings.LLM_MODEL})")
        except Exception as e:
            print(f"⚠️  LLM health ping failed: {e}")

    print("✅ Startup complete!")

    yield

    print("🛑 Shutting down API...")
    print("✅ Shutdown complete!")


app = FastAPI(
    title="AI Medical Diagnosis Assistant",
    description="Medical AI system with LangGraph workflow",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(diagnosis_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "AI Medical Diagnosis API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "textual_analysis": "/patient/textual_analysis",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: Verify main.py imports and app constructs**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -c "from main import app; print('OK')"
```

Expected: `OK` — no model loading, no CUDA references, no errors.

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat(sp1): main.py — remove model loading, add LLM health ping"
```

---

## Task 12: Supabase Migration

**Files:**
- Create: `backend/migrations/001_privacy_policy.sql`

- [ ] **Step 1: Create the migration file**

```sql
-- Migration: Add privacy_policy_accepted to user_profiles
-- Run in Supabase Dashboard → SQL Editor

ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS privacy_policy_accepted boolean NOT NULL DEFAULT false;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles' AND column_name = 'privacy_policy_accepted';
```

- [ ] **Step 2: Run in Supabase Dashboard**

Go to your Supabase project → SQL Editor → paste the SQL → Run.

Expected: The verification SELECT returns one row showing `privacy_policy_accepted | boolean | false`.

- [ ] **Step 3: Commit**

```bash
git add backend/migrations/001_privacy_policy.sql
git commit -m "chore(sp1): add privacy_policy_accepted migration"
```

---

## Task 13: Frontend — Privacy Policy Gate

**Files:**
- Create: `my-app/src/components/medical/PrivacyPolicyModal.tsx`
- Modify: `my-app/src/services/api.ts`
- Modify: `my-app/src/hooks/useDiagnosis.ts`

Flow: API call → 403 `privacy_policy_required` → `PrivacyPolicyRequiredError` thrown in api.ts → `useDiagnosis` catches it, sets `privacyPolicyPending` → modal renders → user clicks Accept → `PATCH /auth/accept-privacy-policy` → retry original function.

- [ ] **Step 1: Add PrivacyPolicyRequiredError and acceptPrivacyPolicy to api.ts**

At the top of `my-app/src/services/api.ts`, before the `ApiService` class, add:

```typescript
export class PrivacyPolicyRequiredError extends Error {
  constructor() {
    super('privacy_policy_required');
    this.name = 'PrivacyPolicyRequiredError';
  }
}
```

Inside the `ApiService` class, add this static method:

```typescript
  static async acceptPrivacyPolicy(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/accept-privacy-policy`, {
      method: 'PATCH',
      credentials: 'include',
    });
    if (!response.ok) {
      throw new Error(`Failed to accept privacy policy: HTTP ${response.status}`);
    }
  }
```

In `startTextualAnalysis`, `runFollowupQuestions`, `runOverallAnalysis`, and `runMedicalReport`, insert this check **before** the existing `if (!response.ok)` block:

```typescript
      if (response.status === 403) {
        const body = await response.json().catch(() => ({}));
        if (body.detail === 'privacy_policy_required') {
          throw new PrivacyPolicyRequiredError();
        }
      }
```

Remove the `runImageAnalysis` static method entirely — the `/patient/image_analysis` endpoint no longer exists.

- [ ] **Step 2: Update useDiagnosis.ts**

Change the import line:
```typescript
import { ApiService, DiagnosisRequest, PrivacyPolicyRequiredError } from 'services/api';
```

Add `privacyPolicyPending` to `DiagnosisState`:
```typescript
interface DiagnosisState {
  loading: boolean;
  result: AgentState | null;
  error: string | null;
  sessionId: string | null;
  currentStage: string | null;
  workflowInfo: any | null;
  privacyPolicyPending: (() => Promise<void>) | null;
}
```

Add `privacyPolicyPending: null` to the initial state object.

In `startDiagnosis`, replace the catch block:
```typescript
    } catch (error) {
      if (error instanceof PrivacyPolicyRequiredError) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await startDiagnosis(request);
          },
        }));
        return;
      }
      const errorMessage = error instanceof Error ? error.message : 'Diagnosis failed';
      setState(prev => ({ ...prev, loading: false, error: errorMessage }));
      throw error;
    }
```

Apply the same `PrivacyPolicyRequiredError` catch pattern (with the appropriate retry call) to `submitFollowUp` and any other hook method that calls a `/patient/*` endpoint.

Add these two callbacks inside the hook (before the `return`):
```typescript
  const handlePrivacyAccepted = useCallback(async () => {
    await ApiService.acceptPrivacyPolicy();
    if (state.privacyPolicyPending) {
      await state.privacyPolicyPending();
    }
  }, [state.privacyPolicyPending]);

  const dismissPrivacyModal = useCallback(() => {
    setState(prev => ({ ...prev, privacyPolicyPending: null }));
  }, []);
```

Add to the hook's return object:
```typescript
    showPrivacyModal: !!state.privacyPolicyPending,
    handlePrivacyAccepted,
    dismissPrivacyModal,
```

Remove `getImageRequired` and `submitImageAnalysis` from the return — image flow no longer exists.

- [ ] **Step 3: Create PrivacyPolicyModal.tsx**

```typescript
import React from 'react';
import styled from 'styled-components';

interface PrivacyPolicyModalProps {
  onAccept: () => Promise<void>;
  onCancel: () => void;
}

const Overlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const Modal = styled.div`
  background: var(--background, #1a1a2e);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  max-width: 480px;
  width: 90%;
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary, #ffffff);
`;

const Body = styled.p`
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
  margin-bottom: 1.5rem;
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
`;

const CancelButton = styled.button`
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
  cursor: pointer;
  font-size: 0.9rem;
  &:hover { background: rgba(255, 255, 255, 0.05); }
`;

const AcceptButton = styled.button`
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  background: var(--primary, #6c63ff);
  color: #ffffff;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  &:hover { opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

export const PrivacyPolicyModal: React.FC<PrivacyPolicyModalProps> = ({ onAccept, onCancel }) => {
  const [accepting, setAccepting] = React.useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await onAccept();
    } finally {
      setAccepting(false);
    }
  };

  return (
    <Overlay>
      <Modal>
        <Title>Data Privacy Notice</Title>
        <Body>
          Your symptom descriptions will be processed by Groq AI infrastructure to generate
          medical guidance. This service is for informational purposes only and does not
          replace professional medical advice.
          <br /><br />
          Do not enter personally identifying information (name, ID numbers, contact details)
          in symptom fields. By continuing you accept our Privacy Policy.
        </Body>
        <ButtonRow>
          <CancelButton onClick={onCancel}>Cancel</CancelButton>
          <AcceptButton onClick={handleAccept} disabled={accepting}>
            {accepting ? 'Saving...' : 'Accept & Continue'}
          </AcceptButton>
        </ButtonRow>
      </Modal>
    </Overlay>
  );
};
```

- [ ] **Step 4: Wire the modal into the diagnosis workflow**

Find the page/container that calls `useDiagnosis()`. Check `my-app/src/pages/diagnosis/DiagnosisFormPage.tsx` and `AnalysisProgressPage.tsx` — whichever file uses the hook and renders the diagnosis UI.

Import the modal:
```typescript
import { PrivacyPolicyModal } from 'components/medical/PrivacyPolicyModal';
```

Destructure from the hook:
```typescript
const { showPrivacyModal, handlePrivacyAccepted, dismissPrivacyModal, ...rest } = useDiagnosis();
```

Add to JSX (inside the return, at the top level):
```typescript
{showPrivacyModal && (
  <PrivacyPolicyModal
    onAccept={handlePrivacyAccepted}
    onCancel={dismissPrivacyModal}
  />
)}
```

- [ ] **Step 5: Commit**

```bash
git add my-app/src/components/medical/PrivacyPolicyModal.tsx
git add my-app/src/services/api.ts
git add my-app/src/hooks/useDiagnosis.ts
git commit -m "feat(sp1): privacy policy modal, api.ts 403 handling, useDiagnosis integration"
```

---

## Task 14: Verify Success Criteria

- [ ] **Step 1: Run all backend tests**

```bash
cd c:/Users/user/Desktop/MediSage/backend
python -m pytest tests/ -v
```

Expected: `2 passed`

- [ ] **Step 2: Start backend and verify startup log**

```bash
cd c:/Users/user/Desktop/MediSage/backend
uvicorn main:app --reload
```

Expected startup output (no model loading):
```
🚀 AI Medical Diagnosis API starting...
✅ LLM connectivity confirmed (model: llama-3.3-70b-versatile)
✅ Startup complete!
```

- [ ] **Step 3: Confirm image_analysis is gone**

```bash
curl http://localhost:8000/patient/image_analysis
```

Expected: 404 Not Found

- [ ] **Step 4: Confirm privacy policy gate**

```bash
# Unauthenticated → 401
curl -X POST http://localhost:8000/patient/textual_analysis -F "user_symptoms=headache"
```

Expected: `{"detail": "Not authenticated"}`

- [ ] **Step 5: Verify end-to-end in the browser**

Start the frontend (`npm start` in `my-app/`). Log in, submit symptoms. The privacy policy modal should appear. Accept it. The diagnosis should proceed with a loading spinner and return results. Check browser console for no WebSocket or model-loading errors.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat(sp1): complete — API model migration, privacy gate, local stack removed"
```

---

## Spec Coverage Checklist

| Spec requirement | Task covering it |
|-----------------|-----------------|
| Remove llama-cpp-python, torch, torchvision, pillow | Task 1 |
| Add openai>=1.0.0 | Task 1 |
| backend/config.py with LLM env vars | Task 1 |
| backend/llm/client.py — LLMClient singleton | Task 2 |
| LLM_BASE_URL/MODEL/API_KEY from env (swap via env vars only) | Task 2 |
| Delete model_manager.py | Task 7 |
| Delete websocket_manager.py | Task 7 |
| Delete image_classification_node.py | Task 7 |
| All 4 LLM nodes use llm_client.complete() | Tasks 3–6 |
| /patient/image_analysis removed (404) | Task 9 |
| All WebSocket send calls removed | Task 9 |
| main.py: no model loading, LLM health ping | Task 11 |
| Supabase migration: privacy_policy_accepted column | Task 12 |
| require_privacy_policy FastAPI dependency | Task 10 |
| PATCH /auth/accept-privacy-policy endpoint | Task 10 |
| 403 privacy_policy_required on /patient/* | Tasks 9, 10 |
| Frontend PrivacyPolicyModal | Task 13 |
| High ABCDE risk routes to overall_analysis (not image) | Tasks 4, 5, 8 |
| sentence-transformers removed (re-added in SP2 for RAG) | Task 1 |
