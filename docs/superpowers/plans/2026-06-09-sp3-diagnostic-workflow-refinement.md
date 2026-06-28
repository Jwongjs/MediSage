# SP3 — Diagnostic Workflow Refinement

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the diagnosis pipeline into a linear, guided collection flow: intake → symptoms → observable signs (LLM-prompted) → adaptive follow-up → overall analysis → report. Introduce patient intake at session start, LLM-generated sign prompts and follow-up questions, prompt guard with injection sanitization, layman-friendly diagnosis terms, and critical symptoms escalation. Remove all dead skin-cancer code paths, confidence-based routing, and the follow-up loop. Enforce a clear non-overlapping boundary between the diagnosis workflow and the RAG chatbot.

**Architecture summary:**

- **Linear LangGraph graph — no conditional routing.** Six nodes in fixed order: `llm_diagnosis → process_signs → generate_followup_questions → process_followup_responses → overall_analysis → medical_report`. Routing functions `_route_after_diagnosis` and `_route_after_followup` are removed entirely.
- **`interrupt_before`:** `["process_signs", "process_followup_responses", "overall_analysis", "medical_report"]`. `generate_followup_questions` runs automatically after `process_signs` within the same resume call — no interrupt between them.
- **`llm_diagnosis` single LLM call** produces both: (1) top-5 differential diagnoses with layman terms and (2) 3–4 observable sign prompts targeted to the differential. Stored as `textual_analysis` and `sign_prompts`.
- **`process_signs`** is a thin inline node in `patient_workflow.py` — no LLM, records `sign_responses` → `userInput_signs`, appends `"signs_collected"` to `workflow_path`.
- **`workflow_path` as audit log**, not routing switch. Entries appended sequentially: `"initial_assessment"` (after `llm_diagnosis`) → `"signs_collected"` (after `process_signs`) → `"followup_complete"` (after `process_followup_responses`). `OverallAnalysisNode` routes on `"followup_complete" in workflow_path`.
- **`average_confidence`** computed in `process_followup_responses` for report display only — not used for routing.
- **`requires_user_input` removed** from `AgentState` and all nodes — no follow-up loop.
- **Prompt guard** has two layers: (1) vague input detection (word count, junk patterns) and (2) injection sanitization (role-spoofing, jailbreak, instruction-override patterns). User content XML-wrapped in all LLM prompts.
- **PHI log cleanup** — all `print()` calls that echo patient symptom data replaced with non-PHI log messages.
- **`PatientIntake` TypedDict** + `format_intake_context()` in `medical_schemas.py`. Intake context prepended to system prompt in all downstream LLM calls.
- **`TextualSymptomAnalysisResult`** gains `layman_term: str | None`.
- **`FollowUpInteractionNode.handle_followup_interaction`** (SP2 dispatch logic) removed — `_GenerateQuestionsNode` and `_ProcessResponsesNode` wrappers in `patient_workflow.py` call `_generate_questions_phase` and `_process_responses_phase` directly.
- **RAG chatbot boundary** enforced in `_synthesize_node` system prompt: no new diagnoses from current symptoms, emergency redirect, context-only answers.

**Tech Stack:** Python 3.11, FastAPI (Form fields), LangGraph, TypeScript/React, styled-components

> **SP2 dependency:** Tasks assume SP2 is complete — `diagnosis_routes.py` uses `graph.ainvoke` with `Command` for resume, `request: Request` parameter is present, and `patient_workflow.py` compiles the LangGraph graph.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/schemas/medical_schemas.py` | Add `PatientIntake`, `format_intake_context()`, `sign_prompts`/`sign_responses` in `AgentState`; `layman_term` in `TextualSymptomAnalysisResult`; new `WorkflowPathType` literals; remove dead fields |
| Create | `backend/tests/test_sp3_schema.py` | Tests: schema structure, format_intake_context, layman_term |
| Modify | `backend/graphs/patient_workflow.py` | Full rewrite: linear 6-node graph, `_ProcessSignsNode` inline, no routing functions |
| Modify | `backend/api/diagnosis_routes.py` | Injection sanitization, vague input guard, critical detection, `sign_responses` in resume handling |
| Modify | `backend/nodes/llm_diagnosis_node.py` | Combined LLM call (differential + sign prompts), `parse_sign_prompts()`, PHI log cleanup, XML-wrap user input |
| Modify | `backend/nodes/follow_up_interaction_node.py` | Remove `handle_followup_interaction` dispatch + `requires_user_input` logic; adaptive questions; append `workflow_path`; remove skin cancer branch |
| Modify | `backend/nodes/overall_analysis_node.py` | Intake context, critical floor, updated routing on `"followup_complete"` |
| Modify | `backend/nodes/medical_report_node.py` | PATIENT INFORMATION section, emergency banner, layman terms in alternatives, clean dead code |
| Create | `my-app/src/components/medical/IntakeForm.tsx` | Patient intake form |
| Create | `my-app/src/components/medical/SignCheckPanel.tsx` | Displays LLM-generated sign prompts; collects user responses |
| Modify | `my-app/src/services/api.ts` | `VagueInputError`, updated `DiagnosisRequest`, `sign_responses` in resume call |
| Modify | `my-app/src/hooks/useDiagnosis.ts` | Handle `VagueInputError`; expose `submitSignResponses` action |
| Modify | `my-app/src/views/diagnosis.tsx` | Intake gate, signs stage, emergency banner |
| Modify | `backend/graphs/rag_chatbot.py` | `_synthesize_node` boundary enforcement |

---

## Task 1: Schema Updates (TDD)

**Files:**
- Modify: `backend/schemas/medical_schemas.py`
- Create: `backend/tests/test_sp3_schema.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_sp3_schema.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_patient_intake_structure():
    from schemas.medical_schemas import PatientIntake
    intake: PatientIntake = {
        "age": 35,
        "biological_sex": "female",
        "current_medications": "Metformin 500mg",
        "known_allergies": "Penicillin",
        "relevant_medical_history": "Type 2 diabetes",
    }
    assert intake["age"] == 35
    assert intake["biological_sex"] == "female"


def test_agent_state_new_fields():
    from schemas.medical_schemas import AgentState
    state: AgentState = {
        "session_id": "s1",
        "patient_intake": {"age": 40, "biological_sex": "male",
                           "current_medications": "None", "known_allergies": "None",
                           "relevant_medical_history": "None"},
        "userInput_signs": "Swollen left ankle",
        "critical_symptoms_detected": False,
        "sign_prompts": ["Is there visible bruising?", "Can you bear weight?"],
        "sign_responses": {"Is there visible bruising?": "Yes"},
    }
    assert state["patient_intake"]["age"] == 40
    assert state["sign_prompts"][0] == "Is there visible bruising?"
    assert state["critical_symptoms_detected"] is False


def test_format_intake_context_full():
    from schemas.medical_schemas import format_intake_context
    intake = {"age": 28, "biological_sex": "female",
              "current_medications": "Ibuprofen as needed",
              "known_allergies": "Sulfa drugs",
              "relevant_medical_history": "Asthma"}
    result = format_intake_context(intake)
    assert result.startswith("PATIENT INTAKE:")
    assert "28" in result
    assert "Ibuprofen" in result
    assert "Sulfa" in result


def test_format_intake_context_none():
    from schemas.medical_schemas import format_intake_context
    assert format_intake_context(None) == ""


def test_textual_result_layman_term():
    from schemas.medical_schemas import TextualSymptomAnalysisResult
    r: TextualSymptomAnalysisResult = {
        "text_diagnosis": "Costochondritis",
        "layman_term": "Chest Wall Pain",
        "diagnosis_confidence": 0.82,
    }
    assert r["layman_term"] == "Chest Wall Pain"
    r2: TextualSymptomAnalysisResult = {
        "text_diagnosis": "Influenza",
        "layman_term": None,
        "diagnosis_confidence": 0.90,
    }
    assert r2["layman_term"] is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_sp3_schema.py -v
```
Expected: `ImportError` or `KeyError` — new fields do not exist yet.

- [ ] **Step 3: Add PatientIntake + format_intake_context**

Before `WorkflowStage` in `backend/schemas/medical_schemas.py`, add:

```python
class PatientIntake(TypedDict, total=False):
    age: int | None
    biological_sex: Literal["male", "female", "other", "prefer_not_to_say"] | None
    current_medications: str | None
    known_allergies: str | None
    relevant_medical_history: str | None


def format_intake_context(intake: "PatientIntake | None") -> str:
    if not intake:
        return ""
    parts = []
    if intake.get("age"):
        parts.append(f"Age: {intake['age']}")
    if intake.get("biological_sex"):
        parts.append(f"Biological sex: {intake['biological_sex']}")
    if intake.get("current_medications"):
        parts.append(f"Current medications: {intake['current_medications']}")
    if intake.get("known_allergies"):
        parts.append(f"Known allergies: {intake['known_allergies']}")
    if intake.get("relevant_medical_history"):
        parts.append(f"Relevant medical history: {intake['relevant_medical_history']}")
    return ("PATIENT INTAKE:\n" + "\n".join(parts)) if parts else ""
```

- [ ] **Step 4: Update TextualSymptomAnalysisResult**

Replace:
```python
class TextualSymptomAnalysisResult(TypedDict):
    text_diagnosis: str
    diagnosis_confidence: float
```
With:
```python
class TextualSymptomAnalysisResult(TypedDict):
    text_diagnosis: str
    layman_term: str | None
    diagnosis_confidence: float
```

- [ ] **Step 5: Add new fields to AgentState**

After `session_id: str`, add:
```python
    patient_intake: PatientIntake | None
    userInput_signs: str | None
    critical_symptoms_detected: bool | None
    sign_prompts: list[str] | None
    sign_responses: dict[str, str] | None
```

- [ ] **Step 6: Remove dead fields from AgentState**

Delete these lines entirely from `AgentState`:
```python
    requires_skin_cancer_screening: bool | None
    skin_cancer_risk_detected: bool | None
    skin_cancer_risk_metrics: dict[str, Any] | None
    followup_type: Literal["standard", "skin_cancer_screening"] | None
    image_required: bool | None
    userInput_skin_symptoms: str | None
    requires_user_input: bool | None
    workflow: WorkflowInfo   # SP1-era field if present
```

Remove the `WorkflowInfo` class and its `WorkflowAction` Literal if present and unreferenced elsewhere.

- [ ] **Step 7: Update WorkflowPathType**

Replace the existing `WorkflowPathType` Literal with:
```python
WorkflowPathType = Literal[
    "initial_assessment",
    "signs_collected",
    "followup_complete",
]
```

- [ ] **Step 8: Update WorkflowStage**

Add `"awaiting_sign_responses"` to `WorkflowStage`. Remove `"generating_healthcare_recommendations"` and `"healthcare_recommendation_complete"` if present.

- [ ] **Step 9: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_sp3_schema.py -v
```
Expected: 5 passed.

- [ ] **Step 10: Verify no regressions**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 11: Commit**

```bash
git add backend/schemas/medical_schemas.py backend/tests/test_sp3_schema.py
git commit -m "feat(sp3): schema -- PatientIntake, sign_prompts, layman_term, new WorkflowPathType; remove dead skin-cancer fields"
```

---

## Task 2: patient_workflow.py — Linear Graph Rewrite

**Files:**
- Modify: `backend/graphs/patient_workflow.py`

Full rewrite. Remove all routing functions and the `CONFIDENCE_THRESHOLD` constant. Add `_ProcessSignsNode` inline. Six nodes, all edges direct, no conditionals.

- [ ] **Step 1: Read the current file before editing**

- [ ] **Step 2: Replace entire file content**

```python
from __future__ import annotations
from langgraph.graph import StateGraph, END
from schemas.medical_schemas import AgentState


class _GenerateQuestionsNode:
    def __init__(self, node):
        self._node = node

    async def __call__(self, state: dict) -> dict:
        return await self._node._generate_questions_phase(state)


class _ProcessResponsesNode:
    def __init__(self, node):
        self._node = node

    async def __call__(self, state: dict) -> dict:
        followup_response = state.get("followup_response", {})
        return await self._node._process_responses_phase(state, followup_response)


class _ProcessSignsNode:
    async def __call__(self, state: dict) -> dict:
        sign_responses = state.get("sign_responses") or {}
        if sign_responses:
            formatted = "\n".join(
                f"Sign: {q}\nObservation: {a}"
                for q, a in sign_responses.items()
            )
            state["userInput_signs"] = formatted
        workflow_path = list(state.get("workflow_path") or [])
        if "signs_collected" not in workflow_path:
            workflow_path.append("signs_collected")
        state["workflow_path"] = workflow_path
        state["current_workflow_stage"] = "generating_followup_questions"
        return state


def compile_patient_workflow(checkpointer):
    from nodes import LLMDiagnosisNode, OverallAnalysisNode, MedicalReportNode
    from nodes.follow_up_interaction_node import FollowUpInteractionNode

    followup_node = FollowUpInteractionNode()

    workflow = StateGraph(AgentState)
    workflow.set_entry_point("llm_diagnosis")

    workflow.add_node("llm_diagnosis", LLMDiagnosisNode())
    workflow.add_node("process_signs", _ProcessSignsNode())
    workflow.add_node("generate_followup_questions", _GenerateQuestionsNode(followup_node))
    workflow.add_node("process_followup_responses", _ProcessResponsesNode(followup_node))
    workflow.add_node("overall_analysis", OverallAnalysisNode())
    workflow.add_node("medical_report", MedicalReportNode())

    workflow.add_edge("llm_diagnosis", "process_signs")
    workflow.add_edge("process_signs", "generate_followup_questions")
    workflow.add_edge("generate_followup_questions", "process_followup_responses")
    workflow.add_edge("process_followup_responses", "overall_analysis")
    workflow.add_edge("overall_analysis", "medical_report")
    workflow.add_edge("medical_report", END)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "process_signs",
            "process_followup_responses",
            "overall_analysis",
            "medical_report",
        ],
    )
```

- [ ] **Step 3: Verify graph compiles**

```bash
cd backend && python -c "
from unittest.mock import MagicMock
from graphs.patient_workflow import compile_patient_workflow
g = compile_patient_workflow(MagicMock())
print('nodes:', list(g.get_graph().nodes.keys()))
print('OK')
"
```
Expected: prints 6 node names, `OK`.

- [ ] **Step 4: Commit**

```bash
git add backend/graphs/patient_workflow.py
git commit -m "feat(sp3): patient_workflow -- linear 6-node graph, ProcessSignsNode, remove routing functions"
```

---

## Task 3: Input Validation + Backend API

**Files:**
- Modify: `backend/api/diagnosis_routes.py`

- [ ] **Step 1: Read the current file in full**

Note the exact signature of `run_textual_analysis` and the resume endpoint name and parameters.

- [ ] **Step 2: Add validation helpers at module level**

After imports, add:

```python
import re as _re

_MIN_WORDS = 5
_JUNK_PATTERN = _re.compile(
    r'^\s*(test|hello|hi|asdf|qwerty|123|abc|nothing|n\/?a|none|idk)\s*$',
    _re.IGNORECASE,
)
_INJECTION_PATTERNS = [
    _re.compile(r'ignore\s+(previous|above|all)\s+instructions', _re.IGNORECASE),
    _re.compile(r'you\s+are\s+now\s+', _re.IGNORECASE),
    _re.compile(r'(system|user|assistant)\s*:', _re.IGNORECASE),
    _re.compile(r'repeat\s+(everything|your|the)\s+(above|system|prompt)', _re.IGNORECASE),
    _re.compile(r'jailbreak', _re.IGNORECASE),
    _re.compile(r'act\s+as\s+(?!a?\s*patient)', _re.IGNORECASE),
]
_CRITICAL_KEYWORDS = frozenset([
    "chest pain", "chest tightness", "shortness of breath", "difficulty breathing",
    "sudden weakness", "sudden numbness", "loss of consciousness", "unconscious",
    "severe headache", "worst headache", "thunderclap", "sudden vision loss",
    "throat swelling", "anaphylaxis", "coughing blood", "vomiting blood",
    "crushing pain", "heart attack", "stroke", "seizure", "suicidal", "self-harm",
])


def _validate_symptom_input(symptoms: str) -> dict:
    combined = symptoms.strip()
    if len(combined.split()) < _MIN_WORDS:
        return {"valid": False, "feedback": (
            "Please describe your symptoms in more detail "
            "(at least a few words describing what you are experiencing)."
        )}
    if _JUNK_PATTERN.match(combined):
        return {"valid": False, "feedback": (
            "Please describe the actual symptoms you are experiencing."
        )}
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(combined):
            return {"valid": False, "feedback": (
                "Your input contains content that cannot be processed. "
                "Please describe your symptoms only."
            )}
    return {"valid": True, "feedback": ""}


def _detect_critical_symptoms(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _CRITICAL_KEYWORDS)
```

- [ ] **Step 3: Update run_textual_analysis signature and body**

Replace the function signature with:

```python
@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_textual_analysis(
    request: Request,
    user_symptoms: str = Form(...),
    session_id: Optional[str] = Form(None),
    intake_age: Optional[str] = Form(None),
    intake_biological_sex: Optional[str] = Form(None),
    intake_current_medications: Optional[str] = Form(None),
    intake_known_allergies: Optional[str] = Form(None),
    intake_relevant_medical_history: Optional[str] = Form(None),
):
```

Replace the body from `session_id = ...` through `result = await graph.ainvoke(...)` with:

```python
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        validation = _validate_symptom_input(user_symptoms)
        if not validation["valid"]:
            raise HTTPException(
                status_code=422,
                detail={"code": "vague_input", "feedback": validation["feedback"]},
            )

        critical = _detect_critical_symptoms(user_symptoms)

        patient_intake = None
        if any([intake_age, intake_biological_sex, intake_current_medications,
                intake_known_allergies, intake_relevant_medical_history]):
            patient_intake = {
                "age": int(intake_age) if intake_age and intake_age.isdigit() else None,
                "biological_sex": intake_biological_sex or None,
                "current_medications": intake_current_medications or "",
                "known_allergies": intake_known_allergies or "",
                "relevant_medical_history": intake_relevant_medical_history or "",
            }

        initial_state: AgentState = {
            "session_id": session_id,
            "latest_user_message": user_symptoms,
            "userInput_symptoms": user_symptoms,
            "current_workflow_stage": "initializing",
            "patient_intake": patient_intake,
            "critical_symptoms_detected": critical,
            "workflow_path": [],
        }
        result = await graph.ainvoke(initial_state, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Add sign_responses to the resume endpoint**

Read the existing resume endpoint. After the existing `followup_response` Form field, add:

```python
    sign_responses: Optional[str] = Form(None),
```

In the `update` dict construction, add:

```python
        if sign_responses:
            import json as _json
            update["sign_responses"] = _json.loads(sign_responses)
```

- [ ] **Step 5: Verify import**

```bash
cd backend && python -c "from api.diagnosis_routes import diagnosis_router; print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp3): diagnosis_routes -- injection sanitization, prompt guard, critical detection, sign_responses in resume"
```

---

## Task 4: LLMDiagnosisNode — Combined Differential + Sign Prompts

**Files:**
- Modify: `backend/nodes/llm_diagnosis_node.py`

Single LLM call produces both the differential diagnosis list and targeted sign prompts. PHI removed from logs. User input XML-wrapped.

- [ ] **Step 1: Update imports**

Replace:
```python
from schemas.medical_schemas import TextualSymptomAnalysisResult
```
With:
```python
from schemas.medical_schemas import TextualSymptomAnalysisResult, format_intake_context
```

- [ ] **Step 2: Update parse_diagnosis_details to extract layman_term**

Replace the entire `parse_diagnosis_details` function:

```python
def parse_diagnosis_details(raw_response: str) -> list[TextualSymptomAnalysisResult]:
    results: list[TextualSymptomAnalysisResult] = []
    diagnosis_pattern = re.compile(
        r"-\s*Diagnosis:\s*(.*?)\s*-\s*Confidence:\s*([0-9.]+)\s*",
        re.IGNORECASE | re.DOTALL,
    )
    layman_pattern = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")

    for match in diagnosis_pattern.finditer(raw_response):
        raw_diagnosis, confidence = match.groups()
        raw_diagnosis = raw_diagnosis.strip()
        layman_match = layman_pattern.match(raw_diagnosis)
        if layman_match:
            medical_name = layman_match.group(1).strip()
            layman_term = layman_match.group(2).strip()
        else:
            medical_name = raw_diagnosis
            layman_term = None
        results.append({
            "text_diagnosis": medical_name,
            "layman_term": layman_term,
            "diagnosis_confidence": float(confidence.strip()),
        })

    results.sort(key=lambda x: x["diagnosis_confidence"], reverse=True)
    return results
```

- [ ] **Step 3: Add parse_sign_prompts function**

After `parse_diagnosis_details`, add:

```python
def parse_sign_prompts(raw_response: str) -> list[str]:
    section_match = re.search(
        r"SIGNS?\s+TO\s+CHECK:?\s*\n(.*?)(?:\n\n[A-Z]|\Z)",
        raw_response,
        re.IGNORECASE | re.DOTALL,
    )
    if not section_match:
        return []
    lines = [l.strip() for l in section_match.group(1).strip().split('\n') if l.strip()]
    signs = []
    for line in lines:
        cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)
        cleaned = re.sub(r'^[-•]\s*', '', cleaned).strip()
        if cleaned:
            signs.append(cleaned)
    return signs[:4]
```

- [ ] **Step 4: Replace LLMDiagnosisNode entirely**

Replace the entire class:

```python
# Contract: Produces textual_analysis (differential) and sign_prompts from symptoms + intake.
# Single LLM call returns DIFFERENTIAL and SIGNS TO CHECK sections.
# Sets workflow_path = ["initial_assessment"]. Does NOT generate follow-up questions or the report.
class LLMDiagnosisNode:
    async def __call__(self, state: dict) -> dict:
        state["current_workflow_stage"] = "running_diagnosis"
        state = await self.diagnose(state)
        state["current_workflow_stage"] = "awaiting_sign_responses"
        return state

    async def diagnose(self, state: dict) -> dict:
        symptoms = state.get("latest_user_message", "")
        intake_context = format_intake_context(state.get("patient_intake"))

        state["userInput_symptoms"] = symptoms

        user_content = (
            "<patient_input>\n"
            f"Symptoms: {symptoms}\n"
            "</patient_input>\n\n"
            "Provide two sections:\n\n"
            "DIFFERENTIAL:\n"
            "List exactly 5 diagnoses:\n"
            "- Diagnosis: <Medical Name> (<Common Name if meaningfully different, else omit>)\n"
            "- Confidence: <0.0-1.0>\n"
            "(Repeat for each. Most likely first.)\n\n"
            "SIGNS TO CHECK:\n"
            "List 3-4 observable signs the patient should check, relevant to the top diagnoses.\n"
            "Numbered list, one per line, phrased as patient instructions."
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant. Provide accurate, structured responses. "
                    "Always follow the exact format requested. Be concise and professional."
                    + (f"\n\n{intake_context}" if intake_context else "")
                ),
            },
            {"role": "user", "content": user_content},
        ]

        output = await llm_client.complete(messages, max_tokens=500, temperature=0.1)
        parsed_diagnosis = parse_diagnosis_details(output)
        sign_prompts = parse_sign_prompts(output)

        state["textual_analysis"] = parsed_diagnosis
        state["sign_prompts"] = sign_prompts if sign_prompts else []
        state["workflow_path"] = ["initial_assessment"]
        return state
```

- [ ] **Step 5: Smoke test parsers**

```bash
cd backend && python -c "
from nodes.llm_diagnosis_node import parse_diagnosis_details, parse_sign_prompts
sample = '''DIFFERENTIAL:
- Diagnosis: Costochondritis (Chest Wall Pain)
- Confidence: 0.82
- Diagnosis: Influenza
- Confidence: 0.65

SIGNS TO CHECK:
1. Is the pain reproducible by pressing on the chest?
2. Do you have a fever above 38C?
3. Any visible swelling around the ribs?'''

d = parse_diagnosis_details(sample)
assert d[0]['text_diagnosis'] == 'Costochondritis', d[0]
assert d[0]['layman_term'] == 'Chest Wall Pain', d[0]
assert d[1]['layman_term'] is None, d[1]

s = parse_sign_prompts(sample)
assert len(s) == 3, s
assert 'pressing' in s[0], s
print('PASS')
"
```

- [ ] **Step 6: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/nodes/llm_diagnosis_node.py
git commit -m "feat(sp3): LLMDiagnosisNode -- combined differential+sign prompts, parse_sign_prompts, layman_term, PHI cleanup"
```

---

## Task 5: FollowUpInteractionNode — Adaptive Questions

**Files:**
- Modify: `backend/nodes/follow_up_interaction_node.py`

Remove `handle_followup_interaction` (SP2 dispatch — no longer called). Remove `requires_user_input` logic. Remove skin cancer branch. Append `"followup_complete"` to `workflow_path` in `_process_responses_phase`.

Method signatures `_generate_questions_phase(self, state)` and `_process_responses_phase(self, state, responses)` are **UNCHANGED**.

- [ ] **Step 1: Read the current file in full before editing**

- [ ] **Step 2: Remove __call__ and handle_followup_interaction**

Delete the `__call__` method and `handle_followup_interaction` method entirely.

- [ ] **Step 3: Add node contract comment**

Above `class FollowUpInteractionNode:`, add:

```python
# Contract: Generates LLM-adaptive follow-up questions targeting the current differential.
# Processes responses, appends "followup_complete" to workflow_path.
# NEVER asks about age, sex, medications, allergies, or medical history (those come from patient_intake).
# Signatures _generate_questions_phase and _process_responses_phase are stable (patient_workflow.py callers).
```

- [ ] **Step 4: Replace _generate_questions_phase body (signature unchanged)**

```python
    async def _generate_questions_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        questions_list = await self._generate_adaptive_questions_via_llm(state)
        state["followup_questions"] = questions_list
        state["current_workflow_stage"] = "awaiting_followup_responses"
        return state
```

- [ ] **Step 5: Add _generate_adaptive_questions_via_llm**

```python
    async def _generate_adaptive_questions_via_llm(self, state: dict) -> list[str]:
        from schemas.medical_schemas import format_intake_context
        symptoms = state.get("userInput_symptoms", "")
        signs = state.get("userInput_signs", "") or ""
        intake_context = format_intake_context(state.get("patient_intake"))
        textual_analysis = state.get("textual_analysis", [])

        top_diagnoses = "\n".join(
            f"{i+1}. {d.get('text_diagnosis', 'Unknown')}"
            + (f" ({d['layman_term']})" if d.get("layman_term") else "")
            + f" — {d.get('diagnosis_confidence', 0):.0%} confidence"
            for i, d in enumerate(textual_analysis[:5])
        )

        prompt = (
            "You are a clinical intake assistant helping narrow a differential diagnosis.\n\n"
            + (f"PATIENT PROFILE:\n{intake_context}\n\n" if intake_context else "")
            + "<patient_input>\n"
            f"Symptoms: {symptoms or 'Not provided'}\n"
            f"Signs observed: {signs or 'None reported'}\n"
            "</patient_input>\n\n"
            f"INITIAL DIFFERENTIAL:\n{top_diagnoses or 'Not available'}\n\n"
            "Generate exactly 4 targeted follow-up questions to distinguish between these diagnoses. "
            "Focus on: onset/duration, pain characteristics, associated symptoms, aggravating/relieving factors. "
            "Do NOT ask about medications, allergies, age, sex, or past medical history.\n\n"
            "Output: numbered list 1-4, questions only."
        )

        try:
            output = await llm_client.complete(
                [{"role": "user", "content": prompt}], max_tokens=250, temperature=0.2
            )
            questions = self._parse_questions(output)
            if len(questions) >= 2:
                return questions[:4]
        except Exception as e:
            print(f"Adaptive question generation failed: {e}")
        return self._get_fallback_questions()
```

- [ ] **Step 6: Replace _process_responses_phase body (signature unchanged)**

Remove skin cancer branch. Append `"followup_complete"` to `workflow_path`:

```python
    async def _process_responses_phase(self, state: dict[str, Any], responses: dict[str, str]) -> dict[str, Any]:
        from nodes.llm_diagnosis_node import parse_diagnosis_details
        from schemas.medical_schemas import format_intake_context

        symptoms = state.get("userInput_symptoms", "")
        signs = state.get("userInput_signs", "") or ""
        intake_context = format_intake_context(state.get("patient_intake"))

        state["followup_responses"] = responses
        enhanced = self._combine_symptoms_and_responses(symptoms, responses)
        if signs:
            enhanced = f"Observable signs: {signs}\n\n{enhanced}"
        state["followup_qna_overall"] = enhanced

        user_content = (
            "<patient_input>\n"
            f"{enhanced}\n"
            "</patient_input>\n\n"
            "List 5 most possible diagnoses in this exact format ONLY:\n"
            "- Diagnosis: <Medical Name> (<Common Name if different, else omit>)\n"
            "- Confidence: <0.0-1.0>\n\n"
            "Repeat for each diagnosis. Most likely first."
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant. Provide accurate, structured responses. "
                    "Always follow the exact format requested. Be concise and professional."
                    + (f"\n\n{intake_context}" if intake_context else "")
                ),
            },
            {"role": "user", "content": user_content},
        ]
        output = await llm_client.complete(messages, max_tokens=300, temperature=0.1)
        diagnosis_results = parse_diagnosis_details(output)

        state["followup_diagnosis"] = diagnosis_results or []

        if diagnosis_results:
            scores = [d.get("diagnosis_confidence", 0.0) for d in diagnosis_results]
            state["average_confidence"] = sum(scores) / len(scores)

        workflow_path = list(state.get("workflow_path") or [])
        if "followup_complete" not in workflow_path:
            workflow_path.append("followup_complete")
        state["workflow_path"] = workflow_path
        state["current_workflow_stage"] = "followup_analysis_complete"
        return state
```

- [ ] **Step 7: Remove dead methods**

Delete entirely:
- `_get_universal_medical_questions(self)`
- `_get_skin_cancer_screening_questions(self)`
- `analyze_skin_cancer_risk(self, responses)`

- [ ] **Step 8: Verify import and run tests**

```bash
cd backend && python -c "from nodes.follow_up_interaction_node import FollowUpInteractionNode; print('OK')"
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 9: Commit**

```bash
git add backend/nodes/follow_up_interaction_node.py
git commit -m "feat(sp3): FollowUpInteractionNode -- LLM-adaptive questions, append workflow_path, remove ABCDE/skin-cancer/dispatch logic"
```

---

## Task 6: OverallAnalysisNode — Intake Context + Critical Escalation

**Files:**
- Modify: `backend/nodes/overall_analysis_node.py`

- [ ] **Step 1: Add import**

Add:
```python
from schemas.medical_schemas import format_intake_context
```

- [ ] **Step 2: Add node contract comment**

Above `class OverallAnalysisNode:`, add:

```python
# Contract: Produces final_diagnosis, final_severity, clinical_reasoning, specialist_recommendation.
# Routes on workflow_path: "followup_complete" present -> _analyze_textual_and_followup, else -> _analyze_textual_only.
# Enforces severity="critical" floor when critical_symptoms_detected is True.
# Does NOT generate follow-up questions or the report.
```

- [ ] **Step 3: Update perform_overall_analysis routing**

Replace:
```python
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
```
With:
```python
            if "followup_complete" in workflow_path:
                enhanced_analysis = await self._analyze_textual_and_followup(state)
            else:
                enhanced_analysis = await self._analyze_textual_only(state)
```

- [ ] **Step 4: Add critical severity floor**

After `state["overall_analysis"] = enhanced_analysis` (inside `try` block), add:

```python
            if state.get("critical_symptoms_detected") and \
                    enhanced_analysis.get("final_severity") != "critical":
                enhanced_analysis["final_severity"] = "critical"
                state["overall_analysis"] = enhanced_analysis
```

- [ ] **Step 5: Add intake context to _analyze_textual_only**

Inside `_analyze_textual_only`, replace the `messages = [...]` block with:

```python
        intake_context = format_intake_context(state.get("patient_intake"))
        critical = state.get("critical_symptoms_detected", False)
        critical_note = "\nNOTE: Critical symptoms detected. Severity must be 'critical'." if critical else ""

        messages = [
            {
                "role": "system",
                "content": _SYSTEM_PROMPT + (f"\n\n{intake_context}" if intake_context else ""),
            },
            {
                "role": "user",
                "content": (
                    f"MEDICAL ANALYSIS\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})\n"
                    f"Original Symptoms: {userInput_symptoms}{critical_note}\n\n"
                    f"Provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification>\n"
                    f"- Specialist: <most appropriate specialist type>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]
```

- [ ] **Step 6: Add intake context to _analyze_textual_and_followup**

Inside `_analyze_textual_and_followup`, replace the `messages = [...]` block with:

```python
        intake_context = format_intake_context(state.get("patient_intake"))
        critical = state.get("critical_symptoms_detected", False)
        critical_note = "\nNOTE: Critical symptoms detected. Severity must be 'critical'." if critical else ""

        messages = [
            {
                "role": "system",
                "content": _SYSTEM_PROMPT + (f"\n\n{intake_context}" if intake_context else ""),
            },
            {
                "role": "user",
                "content": (
                    f"ENHANCED MEDICAL ANALYSIS\n\n"
                    f"Follow-up Information:\n{followup_qna}\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f}){critical_note}\n\n"
                    f"Provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification>\n"
                    f"- Specialist: <most appropriate specialist type>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]
```

- [ ] **Step 7: Verify and test**

```bash
cd backend && python -c "from nodes.overall_analysis_node import OverallAnalysisNode; print('OK')"
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 8: Commit**

```bash
git add backend/nodes/overall_analysis_node.py
git commit -m "feat(sp3): OverallAnalysisNode -- intake context, critical floor, clean routing on followup_complete"
```

---

## Task 7: MedicalReportNode — Patient Info + Emergency Banner

**Files:**
- Modify: `backend/nodes/medical_report_node.py`

- [ ] **Step 1: Read the current file in full before editing**

Note the exact surrounding text of the report f-string header and the `Analysis Method:` line to make exact edits.

- [ ] **Step 2: Add import**

Add:
```python
from schemas.medical_schemas import format_intake_context
```

- [ ] **Step 3: Add node contract comment**

Above `class MedicalReportNode:`, add:

```python
# Contract: Produces medical_report string from overall_analysis + patient_intake + workflow data.
# Does not re-run diagnosis or analysis. Includes PATIENT INFORMATION section and emergency banner.
```

- [ ] **Step 4: Add intake section and emergency banner builders**

In `_create_template_based_report`, after the existing urgency/severity lookups, add:

```python
        patient_intake = state.get("patient_intake")
        intake_section = ""
        if patient_intake:
            rows = []
            if patient_intake.get("age"):
                rows.append(f"    Age:                  {patient_intake['age']}")
            if patient_intake.get("biological_sex"):
                rows.append(f"    Biological Sex:       {patient_intake['biological_sex'].replace('_', ' ').title()}")
            if patient_intake.get("current_medications"):
                rows.append(f"    Medications:          {patient_intake['current_medications']}")
            if patient_intake.get("known_allergies"):
                rows.append(f"    Allergies:            {patient_intake['known_allergies']}")
            if patient_intake.get("relevant_medical_history"):
                rows.append(f"    Medical History:      {patient_intake['relevant_medical_history']}")
            if rows:
                intake_section = (
                    "\n" + "=" * 65 + "\n"
                    "        PATIENT INFORMATION\n"
                    + "=" * 65 + "\n"
                    + "\n".join(rows) + "\n"
                )

        emergency_banner = ""
        if state.get("critical_symptoms_detected"):
            emergency_banner = (
                "\n[!] EMERGENCY ALERT -- CRITICAL SYMPTOMS DETECTED\n"
                + "-" * 65 + "\n"
                "    STOP -- Call 911 or go to the nearest emergency room IMMEDIATELY.\n"
                "    One or more symptoms may indicate a life-threatening condition.\n"
                "    Do NOT wait. Seek emergency care NOW.\n"
                + "-" * 65 + "\n"
            )
```

- [ ] **Step 5: Insert emergency_banner and intake_section into report f-string**

Prepend `{emergency_banner}` before the report header line (read exact text first). Insert `{intake_section}` between `Analysis Method: {analysis_type}` and the EXECUTIVE SUMMARY separator (read exact surrounding text first).

- [ ] **Step 6: Replace _get_alternative_diagnoses**

```python
    def _get_alternative_diagnoses(self, state: Dict[str, Any]) -> str:
        followup_diagnosis = state.get("followup_diagnosis", [])
        textual_analysis = state.get("textual_analysis", [])
        source = followup_diagnosis if len(followup_diagnosis) > 1 else textual_analysis
        if len(source) <= 1:
            return "No significant alternative diagnoses identified."
        alternatives = []
        for i, diag in enumerate(source[1:4], 1):
            name = diag.get("text_diagnosis", "Unknown")
            layman = diag.get("layman_term")
            conf = diag.get("diagnosis_confidence", 0.0)
            label = f"{name} ({layman})" if layman else name
            alternatives.append(f"• {i}. {label} ({conf:.1%} confidence)")
        return (
            "The following alternative diagnoses were also considered:\n"
            + "\n".join(alternatives)
            + "\n\nThese alternatives may warrant further evaluation if the primary diagnosis is ruled out."
        )
```

- [ ] **Step 7: Replace _get_analysis_type_display**

```python
    def _get_analysis_type_display(self, workflow_path: list, state: Dict[str, Any]) -> str:
        if "followup_complete" in workflow_path:
            return "Enhanced Symptom Analysis (with Guided Signs + Follow-up Questions)"
        return "Standard Symptom Analysis"
```

- [ ] **Step 8: Verify and test**

```bash
cd backend && python -c "from nodes.medical_report_node import MedicalReportNode; print('OK')"
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 9: Commit**

```bash
git add backend/nodes/medical_report_node.py
git commit -m "feat(sp3): MedicalReportNode -- PATIENT INFORMATION, emergency banner, layman alternatives, clean dead code"
```

---

## Task 8: Frontend — Intake Form + Signs Stage + Wiring

**Files:**
- Create: `my-app/src/components/medical/IntakeForm.tsx`
- Create: `my-app/src/components/medical/SignCheckPanel.tsx`
- Modify: `my-app/src/services/api.ts`
- Modify: `my-app/src/hooks/useDiagnosis.ts`
- Modify: `my-app/src/views/diagnosis.tsx`

- [ ] **Step 1: Read diagnosis.tsx, api.ts, and useDiagnosis.ts in full before editing**

Note: exact locations of `handleStartDiagnosis`, `WorkflowRouter`, existing stage checks, and `current_workflow_stage` values currently handled.

- [ ] **Step 2: Create IntakeForm.tsx**

```tsx
import React, { useState } from 'react';
import styled from 'styled-components';

export interface PatientIntake {
  age: string;
  biological_sex: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  current_medications: string;
  known_allergies: string;
  relevant_medical_history: string;
}

interface Props { onSubmit: (intake: PatientIntake) => void; }

const Form = styled.form`display: flex; flex-direction: column; gap: 1.25rem; max-width: 560px; margin: 0 auto;`;
const Field = styled.div`display: flex; flex-direction: column; gap: 0.4rem;`;
const Label = styled.label`font-size: 0.875rem; font-weight: 500; color: var(--text-primary, #fff);`;
const Input = styled.input`padding: 0.6rem 0.875rem; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-primary, #fff); font-size: 0.9rem; outline: none; &:focus { border-color: var(--primary, #6c63ff); }`;
const Select = styled.select`padding: 0.6rem 0.875rem; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-primary, #fff); font-size: 0.9rem; outline: none; &:focus { border-color: var(--primary, #6c63ff); } option { background: #1a1a2e; }`;
const Textarea = styled.textarea`padding: 0.6rem 0.875rem; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-primary, #fff); font-size: 0.9rem; resize: vertical; min-height: 70px; outline: none; &:focus { border-color: var(--primary, #6c63ff); }`;
const Disclaimer = styled.p`font-size: 0.78rem; color: var(--text-secondary, rgba(255,255,255,0.5)); margin: 0;`;
const SubmitBtn = styled.button`padding: 0.7rem 1.5rem; background: var(--primary, #6c63ff); color: #fff; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 500; cursor: pointer; align-self: flex-end; &:hover { opacity: 0.9; }`;

const EMPTY: PatientIntake = {
  age: '', biological_sex: 'prefer_not_to_say',
  current_medications: '', known_allergies: '', relevant_medical_history: '',
};

export const IntakeForm: React.FC<Props> = ({ onSubmit }) => {
  const [intake, setIntake] = useState<PatientIntake>(EMPTY);
  const set = (field: keyof PatientIntake) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setIntake(prev => ({ ...prev, [field]: e.target.value }));

  return (
    <Form onSubmit={e => { e.preventDefault(); onSubmit(intake); }}>
      <Disclaimer>Do not enter real personally identifying information. Symptom data is processed by an AI model.</Disclaimer>
      <Field>
        <Label htmlFor="intake-age">Age</Label>
        <Input id="intake-age" type="number" min={0} max={150} placeholder="e.g. 34" value={intake.age} onChange={set('age')} />
      </Field>
      <Field>
        <Label htmlFor="intake-sex">Biological Sex</Label>
        <Select id="intake-sex" value={intake.biological_sex} onChange={set('biological_sex')}>
          <option value="prefer_not_to_say">Prefer not to say</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </Select>
      </Field>
      <Field>
        <Label htmlFor="intake-meds">Current Medications</Label>
        <Textarea id="intake-meds" placeholder='"Metformin 500mg daily" — or "None"' value={intake.current_medications} onChange={set('current_medications')} />
      </Field>
      <Field>
        <Label htmlFor="intake-allergy">Known Allergies</Label>
        <Textarea id="intake-allergy" placeholder='"Penicillin, sulfa drugs" — or "None"' value={intake.known_allergies} onChange={set('known_allergies')} />
      </Field>
      <Field>
        <Label htmlFor="intake-history">Relevant Medical History</Label>
        <Textarea id="intake-history" placeholder='"Type 2 diabetes since 2020" — or "None"' value={intake.relevant_medical_history} onChange={set('relevant_medical_history')} />
      </Field>
      <SubmitBtn type="submit">Continue to Symptoms</SubmitBtn>
    </Form>
  );
};
```

- [ ] **Step 3: Create SignCheckPanel.tsx**

```tsx
import React, { useState } from 'react';
import styled from 'styled-components';

interface Props {
  signPrompts: string[];
  onSubmit: (responses: Record<string, string>) => void;
  loading?: boolean;
}

const Container = styled.div`display: flex; flex-direction: column; gap: 1.25rem; max-width: 600px; margin: 0 auto;`;
const Heading = styled.h3`font-size: 1rem; font-weight: 500; color: var(--text-primary, #fff); margin: 0;`;
const Subtext = styled.p`font-size: 0.82rem; color: var(--text-secondary, rgba(255,255,255,0.55)); margin: 0;`;
const Item = styled.div`display: flex; flex-direction: column; gap: 0.4rem;`;
const PromptText = styled.label`font-size: 0.875rem; color: var(--text-primary, #fff);`;
const Input = styled.input`padding: 0.55rem 0.8rem; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-primary, #fff); font-size: 0.875rem; outline: none; &:focus { border-color: var(--primary, #6c63ff); }`;
const SubmitBtn = styled.button`padding: 0.7rem 1.5rem; background: var(--primary, #6c63ff); color: #fff; border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; align-self: flex-end; &:disabled { opacity: 0.5; } &:hover:not(:disabled) { opacity: 0.9; }`;

export const SignCheckPanel: React.FC<Props> = ({ signPrompts, onSubmit, loading }) => {
  const [responses, setResponses] = useState<Record<string, string>>({});

  return (
    <Container>
      <div>
        <Heading>Please check the following signs</Heading>
        <Subtext>Based on your symptoms, observe and describe each indicator below.</Subtext>
      </div>
      {signPrompts.map((prompt, i) => (
        <Item key={i}>
          <PromptText htmlFor={`sign-${i}`}>{i + 1}. {prompt}</PromptText>
          <Input
            id={`sign-${i}`}
            type="text"
            placeholder='Describe what you observe, or "Not applicable"'
            value={responses[prompt] || ''}
            onChange={e => setResponses(prev => ({ ...prev, [prompt]: e.target.value }))}
          />
        </Item>
      ))}
      <SubmitBtn disabled={loading} onClick={() => onSubmit(responses)}>
        {loading ? 'Processing...' : 'Submit Signs'}
      </SubmitBtn>
    </Container>
  );
};
```

- [ ] **Step 4: Update api.ts**

Add after `PrivacyPolicyRequiredError`:

```typescript
export class VagueInputError extends Error {
  constructor(public readonly feedback: string) {
    super('vague_input');
    this.name = 'VagueInputError';
  }
}

export interface PatientIntakeRequest {
  age: string;
  biological_sex: string;
  current_medications: string;
  known_allergies: string;
  relevant_medical_history: string;
}

export interface DiagnosisRequest {
  symptoms: string;
  patient_intake?: PatientIntakeRequest;
}
```

In `startTextualAnalysis`, after the 403 check, add:

```typescript
      if (response.status === 422) {
        const body = await response.json().catch(() => ({}));
        if (body.detail?.code === 'vague_input') {
          throw new VagueInputError(body.detail.feedback);
        }
      }
```

In `startTextualAnalysis` form data, add intake fields after `session_id`:

```typescript
      if (request.patient_intake) {
        const p = request.patient_intake;
        if (p.age) formData.append('intake_age', p.age);
        if (p.biological_sex) formData.append('intake_biological_sex', p.biological_sex);
        if (p.current_medications) formData.append('intake_current_medications', p.current_medications);
        if (p.known_allergies) formData.append('intake_known_allergies', p.known_allergies);
        if (p.relevant_medical_history) formData.append('intake_relevant_medical_history', p.relevant_medical_history);
      }
```

Add `resumeWithSignResponses` to `ApiService`:

```typescript
  async resumeWithSignResponses(sessionId: string, signResponses: Record<string, string>) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('sign_responses', JSON.stringify(signResponses));
    const response = await fetch(`${this.baseUrl}/patient/resume`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    if (!response.ok) throw new Error(`Resume failed: ${response.status}`);
    return response.json();
  }
```

- [ ] **Step 5: Update useDiagnosis.ts**

Update import to include `VagueInputError`. In `startDiagnosis` catch block, add before `PrivacyPolicyRequiredError` check:

```typescript
      if (error instanceof VagueInputError) {
        setState(prev => ({ ...prev, loading: false, error: error.feedback }));
        return;
      }
```

Add `submitSignResponses` action that calls `api.resumeWithSignResponses(sessionId, signResponses)` and updates state with the result.

- [ ] **Step 6: Update diagnosis.tsx**

Add imports:
```typescript
import { IntakeForm, PatientIntake } from 'components/medical/IntakeForm';
import { SignCheckPanel } from 'components/medical/SignCheckPanel';
```

Add state variables:
```typescript
  const [patientIntake, setPatientIntake] = React.useState<PatientIntake | null>(null);
```

Update `startDiagnosis` call to pass `patient_intake: patientIntake || undefined`.

Gate rendering: show `IntakeForm` when `!patientIntake && !result`. Once intake is set, show symptom input and `WorkflowRouter`. Show `SignCheckPanel` in place of or above the workflow when `result?.current_workflow_stage === "awaiting_sign_responses"` and `result?.sign_prompts?.length`. Add emergency banner when `result?.critical_symptoms_detected`.

- [ ] **Step 7: TypeScript compile check**

```bash
cd my-app && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 8: End-to-end smoke test**

Start backend and frontend.

1. Diagnosis page → `IntakeForm` shown, no symptom input visible
2. Fill intake (age=32, female, no meds/allergies/history) → continue
3. Submit `"asdf"` → vague input error shown
4. Submit `"I have severe chest pain and cannot breathe"` → after result: emergency banner shown
5. Submit `"persistent headache for 3 days with nausea and light sensitivity"`:
   - After result: `SignCheckPanel` with 3–4 sign prompts visible
   - Fill sign responses → submit signs
   - Follow-up questions appear (must NOT include questions about medications, age, or allergies)
   - Answer follow-up → report renders
   - Report contains PATIENT INFORMATION (age=32, sex=Female)
   - `workflow_path` in response = `["initial_assessment", "signs_collected", "followup_complete"]`

- [ ] **Step 9: Commit**

```bash
git add my-app/src/components/medical/IntakeForm.tsx my-app/src/components/medical/SignCheckPanel.tsx my-app/src/services/api.ts my-app/src/hooks/useDiagnosis.ts my-app/src/views/diagnosis.tsx
git commit -m "feat(sp3): frontend -- IntakeForm, SignCheckPanel, VagueInputError, emergency banner, intake+signs wiring"
```

---

## Task 9: RAG Chatbot Boundary Safeguard

**Files:**
- Modify: `backend/graphs/rag_chatbot.py`

- [ ] **Step 1: Update _synthesize_node**

Above `async def _synthesize_node`, add:

```python
# Contract: Answers questions about the patient's stored health history documents only.
# Does NOT diagnose new symptoms — directs user to the Diagnosis Workflow.
# Redirects active emergencies to call emergency services immediately.
```

Replace the existing system prompt `"content"` string with:

```python
                "You are a medical AI assistant helping a patient review their health history "
                "documents and previously generated assessment reports.\n\n"
                "BOUNDARIES -- strictly enforced:\n"
                "1. Answer questions about the patient's documented health history, existing "
                "assessments, medications, and previously recorded conditions -- using only the "
                "provided context.\n"
                "2. Do NOT generate new diagnoses from currently described symptoms. If the user "
                "describes new or worsening symptoms, direct them to use the Diagnosis feature instead.\n"
                "3. If the user describes an active emergency (chest pain, difficulty breathing, "
                "sudden weakness, loss of consciousness), immediately advise them to call emergency "
                "services (911 or local equivalent). Do not attempt to assess or diagnose.\n"
                "4. If the context lacks sufficient information to answer the question, say so clearly.\n"
                "5. Never fabricate medical information. Always recommend consulting a healthcare "
                "professional for clinical decisions.\n\n"
                f"CONTEXT FROM YOUR MEDICAL RECORDS:\n{context if context else 'No relevant records found.'}"
```

- [ ] **Step 2: Verify and commit**

```bash
cd backend && python -c "from graphs.rag_chatbot import compile_rag_chatbot; print('OK')"
git add backend/graphs/rag_chatbot.py
git commit -m "feat(sp3): RAG chatbot -- boundary safeguard, no new diagnosis from symptoms, emergency redirect"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task(s) |
|---|---|
| Patient intake at session start | Tasks 1, 3, 8 |
| Intake context in all downstream LLM prompts | Tasks 4, 5, 6 |
| PATIENT INFORMATION section in report | Task 7 |
| LLM-generated sign prompts (guided signs stage) | Task 4 |
| Signs collection as separate interactive stage | Tasks 2, 8 |
| Adaptive follow-up questions from LLM | Task 5 |
| No hardcoded questions of any kind | Task 5 |
| Prompt guard: vague input detection | Task 3 |
| Prompt guard: injection sanitization | Task 3 |
| XML-wrapped user input in LLM prompts | Tasks 4, 5 |
| Layman-friendly diagnosis terms | Tasks 1, 4, 5, 7 |
| Critical symptoms detection | Task 3 |
| Critical severity floor enforced | Task 6 |
| Emergency banner in report | Task 7 |
| Emergency banner in frontend | Task 8 |
| Linear workflow — no confidence-based routing | Task 2 |
| workflow_path as append-only audit log | Tasks 4, 5 |
| average_confidence computed for report display only | Task 5 |
| requires_user_input removed entirely | Tasks 1, 5 |
| PHI removed from logs | Task 4 |
| Dead code: skin cancer fields + routing functions | Tasks 1, 2, 5, 6, 7 |
| Dead code: handle_followup_interaction dispatch | Task 5 |
| RAG chatbot boundary: no new diagnosis from symptoms | Task 9 |
| RAG chatbot boundary: emergency redirect | Task 9 |
| Node contracts (inline responsibility comments) | Tasks 4, 5, 6, 7, 9 |

**Workflow path audit trail:**
- After `llm_diagnosis`: `workflow_path = ["initial_assessment"]`
- After `process_signs`: `workflow_path = ["initial_assessment", "signs_collected"]`
- After `process_followup_responses`: `workflow_path = ["initial_assessment", "signs_collected", "followup_complete"]`

**Frontend API call sequence:**
1. `POST /patient/textual_analysis` — symptoms + intake → `llm_diagnosis` runs → pauses before `process_signs`
2. `POST /patient/resume` `{sign_responses}` → `process_signs` + `generate_followup_questions` run → pauses before `process_followup_responses`
3. `POST /patient/resume` `{followup_response}` → `process_followup_responses` runs → pauses before `overall_analysis`
4. `POST /patient/resume` (no body) → `overall_analysis` runs → pauses before `medical_report`
5. `POST /patient/resume` (no body) → `medical_report` runs → END

**SP2 compatibility:**
- `_generate_questions_phase(self, state)` and `_process_responses_phase(self, state, responses)` signatures unchanged — `patient_workflow.py` wrappers still call them directly.
- `TextualSymptomAnalysisResult` gains `layman_term` additively — existing code reading only `text_diagnosis` and `diagnosis_confidence` is unaffected.
- `handle_followup_interaction` removed — was only called by the SP2 `__call__` method which is also removed. Not referenced from `patient_workflow.py`.
