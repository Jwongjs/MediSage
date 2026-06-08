# SP3 — Diagnostic Workflow Refinement

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a structured patient intake step at the start of every session, eliminate all overlap between intake fields and follow-up questions, and give each workflow node a documented, non-overlapping responsibility.

**Architecture:** `PatientIntake` (age, biological sex, current medications, known allergies, relevant medical history) is a new TypedDict added to `AgentState` and `medical_schemas.py`. The frontend collects intake data before the symptoms input and submits both together to `/patient/textual_analysis`. All downstream nodes receive intake via state. One follow-up question that directly duplicates intake — "Are you currently taking any medications, supplements, or have any known allergies?" — is removed. Each node gets an inline contract comment. The medical report gains a `PATIENT INFORMATION` section.

**Tech Stack:** Python 3.11, FastAPI (Form fields), LangGraph, TypeScript/React, styled-components

> **SP2 dependency:** Task 2 assumes SP2 is complete — specifically that `diagnosis_routes.py` uses `graph.ainvoke` and the `Request` parameter is present. If SP2 is still in progress, complete SP2 Task 4 first before executing SP3 Task 2.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/schemas/medical_schemas.py` | Add `PatientIntake` TypedDict, `patient_intake` to `AgentState`, `format_intake_context()` helper |
| Create | `backend/tests/test_intake_passthrough.py` | Tests: schema structure, no overlap in questions, intake in LLM prompt, intake in report |
| Modify | `backend/api/diagnosis_routes.py` | Accept 5 intake Form fields in `run_textual_analysis`; build `patient_intake` dict |
| Modify | `backend/nodes/llm_diagnosis_node.py` | Intake context in diagnosis prompt; node contract comment |
| Modify | `backend/nodes/follow_up_interaction_node.py` | Remove overlap question; node contract comment |
| Modify | `backend/nodes/overall_analysis_node.py` | Intake context in analysis prompts; node contract comment |
| Modify | `backend/nodes/medical_report_node.py` | `PATIENT INFORMATION` section in report; node contract comment |
| Create | `my-app/src/components/medical/IntakeForm.tsx` | Patient intake form component |
| Modify | `my-app/src/services/api.ts` | Add `PatientIntakeRequest` interface; send intake fields in FormData |
| Modify | `my-app/src/views/diagnosis.tsx` | Show `IntakeForm` step before `WorkflowRouter`; pass intake through `handleStartDiagnosis` |

---

## Task 1: PatientIntake schema (TDD)

**Files:**
- Modify: `backend/schemas/medical_schemas.py`
- Create: `backend/tests/test_intake_passthrough.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_intake_passthrough.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_patient_intake_typeddict_structure():
    from schemas.medical_schemas import PatientIntake
    intake: PatientIntake = {
        "age": 35,
        "biological_sex": "female",
        "current_medications": "Metformin 500mg",
        "known_allergies": "Penicillin",
        "relevant_medical_history": "Type 2 diabetes, diagnosed 2020",
    }
    assert intake["age"] == 35
    assert intake["biological_sex"] == "female"


def test_agent_state_accepts_patient_intake():
    from schemas.medical_schemas import AgentState
    state: AgentState = {
        "session_id": "test-session",
        "patient_intake": {
            "age": 40,
            "biological_sex": "male",
            "current_medications": "None",
            "known_allergies": "None",
            "relevant_medical_history": "None",
        }
    }
    assert state["patient_intake"]["age"] == 40


def test_format_intake_context_returns_string():
    from schemas.medical_schemas import format_intake_context
    intake = {
        "age": 28,
        "biological_sex": "female",
        "current_medications": "Ibuprofen as needed",
        "known_allergies": "Sulfa drugs",
        "relevant_medical_history": "Asthma",
    }
    result = format_intake_context(intake)
    assert "28" in result
    assert "female" in result
    assert "Ibuprofen" in result
    assert "Sulfa" in result
    assert "Asthma" in result


def test_format_intake_context_none_returns_empty():
    from schemas.medical_schemas import format_intake_context
    assert format_intake_context(None) == ""
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py -v
```
Expected: `ImportError` — `PatientIntake` and `format_intake_context` do not exist yet

- [ ] **Step 3: Add PatientIntake + format_intake_context to medical_schemas.py**

After the existing imports at the top of `backend/schemas/medical_schemas.py`, add before the `WorkflowStage` literal:

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
    return "PATIENT INTAKE:\n" + "\n".join(parts) if parts else ""
```

- [ ] **Step 4: Add patient_intake field to AgentState**

In the `AgentState` TypedDict, add this line directly after `session_id: str`:

```python
    patient_intake: PatientIntake | None
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py -v
```
Expected: `4 passed`

- [ ] **Step 6: Verify existing tests still pass**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all prior tests still pass (no regressions)

- [ ] **Step 7: Commit**

```bash
git add backend/schemas/medical_schemas.py backend/tests/test_intake_passthrough.py
git commit -m "feat(sp3): add PatientIntake schema, format_intake_context helper, patient_intake in AgentState"
```

---

## Task 2: Backend — intake fields in textual_analysis endpoint

**Files:**
- Modify: `backend/api/diagnosis_routes.py`

This assumes SP2 Task 4 is complete: `run_textual_analysis` accepts `request: Request`, calls `graph.ainvoke(initial_state, config)`, and imports `AgentState`.

- [ ] **Step 1: Update run_textual_analysis signature**

Find the `run_textual_analysis` function in `backend/api/diagnosis_routes.py`. Add 5 optional intake Form parameters after `session_id`:

```python
@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_textual_analysis(
    request: Request,
    user_symptoms: str = Form(..., description="Patient symptoms"),
    session_id: Optional[str] = Form(None),
    intake_age: Optional[str] = Form(None),
    intake_biological_sex: Optional[str] = Form(None),
    intake_current_medications: Optional[str] = Form(None),
    intake_known_allergies: Optional[str] = Form(None),
    intake_relevant_medical_history: Optional[str] = Form(None),
):
```

- [ ] **Step 2: Build patient_intake dict inside the try block**

Replace the `initial_state` construction inside the try block with:

```python
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        patient_intake = None
        if intake_age or intake_biological_sex:
            patient_intake = {
                "age": int(intake_age) if intake_age else None,
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
        }
        result = await graph.ainvoke(initial_state, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Verify import**

```bash
cd backend && python -c "from api.diagnosis_routes import diagnosis_router; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/api/diagnosis_routes.py
git commit -m "feat(sp3): accept patient intake Form fields in textual_analysis endpoint"
```

---

## Task 3: LLMDiagnosisNode — intake context + node contract

**Files:**
- Modify: `backend/nodes/llm_diagnosis_node.py`
- Modify: `backend/tests/test_intake_passthrough.py`

- [ ] **Step 1: Add format_intake_context import**

In `backend/nodes/llm_diagnosis_node.py`, change the schema import:

Old:
```python
from schemas.medical_schemas import TextualSymptomAnalysisResult
```

New:
```python
from schemas.medical_schemas import TextualSymptomAnalysisResult, format_intake_context
```

- [ ] **Step 2: Add node contract comment above the class**

```python
# Contract: Produces textual_analysis list + workflow_path from raw symptoms + patient_intake context.
# Does NOT generate follow-up questions, interpret prior diagnoses, or produce the final report.
class LLMDiagnosisNode:
```

- [ ] **Step 3: Include intake context in diagnose() system prompt**

In the `diagnose` method, find the `messages = [...]` block in the non-skin branch. Replace it:

```python
        intake_context = format_intake_context(state.get("patient_intake"))

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant. Provide accurate, structured responses. "
                    "Always follow the exact format requested. Be concise and professional."
                    + (f"\n\n{intake_context}" if intake_context else "")
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
```

- [ ] **Step 4: Write test verifying intake appears in LLM prompt**

Append to `backend/tests/test_intake_passthrough.py`:

```python
import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_llm_diagnosis_node_includes_intake_in_system_prompt():
    captured_messages = []

    async def mock_complete(messages, **kwargs):
        captured_messages.extend(messages)
        return "- Diagnosis: Flu\n- Confidence: 0.85"

    with patch("nodes.llm_diagnosis_node.llm_client") as mock_client:
        mock_client.complete = mock_complete
        from nodes.llm_diagnosis_node import LLMDiagnosisNode
        node = LLMDiagnosisNode()
        state = {
            "latest_user_message": "I have a headache",
            "patient_intake": {
                "age": 30,
                "biological_sex": "male",
                "current_medications": "None",
                "known_allergies": "Penicillin",
                "relevant_medical_history": "None",
            },
        }
        await node.diagnose(state)

    system_prompt = captured_messages[0]["content"]
    assert "30" in system_prompt
    assert "male" in system_prompt
    assert "Penicillin" in system_prompt
```

- [ ] **Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py -v
```
Expected: all tests pass (5 passed)

- [ ] **Step 6: Verify import**

```bash
cd backend && python -c "from nodes.llm_diagnosis_node import LLMDiagnosisNode; print('OK')"
```
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add backend/nodes/llm_diagnosis_node.py backend/tests/test_intake_passthrough.py
git commit -m "feat(sp3): LLMDiagnosisNode — intake context in diagnosis prompt, node contract"
```

---

## Task 4: FollowUpInteractionNode — remove overlap + node contract

**Files:**
- Modify: `backend/nodes/follow_up_interaction_node.py`
- Modify: `backend/tests/test_intake_passthrough.py`

The current `_get_universal_medical_questions()` question 5 — "Are you currently taking any medications, supplements, or have any known allergies?" — directly overlaps with `current_medications` and `known_allergies` in `PatientIntake`. Remove it.

- [ ] **Step 1: Write failing overlap test**

Append to `backend/tests/test_intake_passthrough.py`:

```python
def test_followup_questions_do_not_overlap_with_intake():
    from nodes.follow_up_interaction_node import FollowUpInteractionNode
    node = FollowUpInteractionNode()
    questions = node._get_universal_medical_questions()
    combined = " ".join(questions).lower()
    assert "medication" not in combined, "Follow-up overlaps intake: medications"
    assert "allerg" not in combined, "Follow-up overlaps intake: allergies"
    for q in questions:
        assert "medical history" not in q.lower(), f"Follow-up overlaps intake history: {q}"
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py::test_followup_questions_do_not_overlap_with_intake -v
```
Expected: `FAILED` — "medication" found in the questions

- [ ] **Step 3: Add node contract comment above the class**

```python
# Contract: Generates follow-up questions about the CURRENT EPISODE only (timeline, progression,
# pain level, additional symptoms). Processes responses and produces followup_diagnosis.
# NEVER asks about age, biological sex, current medications, known allergies, or general medical
# history — these are captured in patient_intake before the session starts.
class FollowUpInteractionNode:
```

- [ ] **Step 4: Replace _get_universal_medical_questions**

```python
    def _get_universal_medical_questions(self) -> list[str]:
        # Medications, allergies, and medical history are covered by patient intake — do not duplicate.
        return [
            "How long have you been experiencing these symptoms? (hours, days, weeks, months)",
            "Have your symptoms gotten worse, better, or stayed the same since they started?",
            "On a scale of 0–10, what is your current pain level? (0 = no pain, 10 = worst pain imaginable)",
            "Do you have any other symptoms that you haven't mentioned yet?",
        ]
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py -v
```
Expected: all tests pass (6 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/nodes/follow_up_interaction_node.py backend/tests/test_intake_passthrough.py
git commit -m "feat(sp3): FollowUpInteractionNode — remove medication/allergy overlap question, add node contract"
```

---

## Task 5: OverallAnalysisNode — intake context + node contract

**Files:**
- Modify: `backend/nodes/overall_analysis_node.py`

- [ ] **Step 1: Add format_intake_context import**

In `backend/nodes/overall_analysis_node.py`, change the imports:

Old:
```python
from typing import Dict, Any, List
import re
from llm.client import llm_client
```

New:
```python
from typing import Dict, Any, List
import re
from llm.client import llm_client
from schemas.medical_schemas import format_intake_context
```

- [ ] **Step 2: Add node contract comment above the class**

```python
# Contract: Produces final_diagnosis, final_severity, clinical_reasoning, and
# specialist_recommendation from textual_analysis or followup_diagnosis + patient_intake.
# Does NOT generate follow-up questions or the full medical report text.
class OverallAnalysisNode:
```

- [ ] **Step 3: Include intake context in _analyze_textual_only**

In `_analyze_textual_only`, find `messages = [...]`. Replace it:

```python
        intake_context = format_intake_context(state.get("patient_intake"))
        system_with_intake = _SYSTEM_PROMPT + (f"\n\n{intake_context}" if intake_context else "")

        messages = [
            {"role": "system", "content": system_with_intake},
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
```

- [ ] **Step 4: Include intake context in _analyze_textual_and_followup**

In `_analyze_textual_and_followup`, find `messages = [...]`. Replace it:

```python
        intake_context = format_intake_context(state.get("patient_intake"))
        system_with_intake = _SYSTEM_PROMPT + (f"\n\n{intake_context}" if intake_context else "")

        messages = [
            {"role": "system", "content": system_with_intake},
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
```

- [ ] **Step 5: Verify import**

```bash
cd backend && python -c "from nodes.overall_analysis_node import OverallAnalysisNode; print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/nodes/overall_analysis_node.py
git commit -m "feat(sp3): OverallAnalysisNode — intake context in analysis prompts, node contract"
```

---

## Task 6: MedicalReportNode — Patient Information section + node contract

**Files:**
- Modify: `backend/nodes/medical_report_node.py`
- Modify: `backend/tests/test_intake_passthrough.py`

- [ ] **Step 1: Add format_intake_context import**

In `backend/nodes/medical_report_node.py`, add to the imports:

```python
from schemas.medical_schemas import format_intake_context
```

- [ ] **Step 2: Add node contract comment above the class**

```python
# Contract: Produces medical_report string from overall_analysis + patient_intake + workflow data.
# Does not re-run diagnosis or analysis. Does not access external data sources or databases
# (except Supabase for saving via separate methods).
class MedicalReportNode:
```

- [ ] **Step 3: Add intake section in _create_template_based_report**

In `_create_template_based_report`, after `workflow_path = state.get("workflow_path", [])`, add:

```python
        patient_intake = state.get("patient_intake")
        intake_section = ""
        if patient_intake:
            rows = []
            if patient_intake.get("age"):
                rows.append(f"    Age:                     {patient_intake['age']}")
            if patient_intake.get("biological_sex"):
                rows.append(f"    Biological Sex:          {patient_intake['biological_sex'].replace('_', ' ').title()}")
            if patient_intake.get("current_medications"):
                rows.append(f"    Current Medications:     {patient_intake['current_medications']}")
            if patient_intake.get("known_allergies"):
                rows.append(f"    Known Allergies:         {patient_intake['known_allergies']}")
            if patient_intake.get("relevant_medical_history"):
                rows.append(f"    Relevant History:        {patient_intake['relevant_medical_history']}")
            if rows:
                intake_section = (
                    "\n═══════════════════════════════════════════════════════════════════\n"
                    "        PATIENT INFORMATION\n"
                    "═══════════════════════════════════════════════════════════════════\n"
                    + "\n".join(rows) + "\n"
                )
```

Then in the `report = f"""..."""` string, insert `{intake_section}` between the header block and `EXECUTIVE SUMMARY`. Find:

```python
    Analysis Method: {analysis_type}

═══════════════════════════════════════════════════════════════════
        EXECUTIVE SUMMARY
```

Replace with:

```python
    Analysis Method: {analysis_type}
{intake_section}
═══════════════════════════════════════════════════════════════════
        EXECUTIVE SUMMARY
```

- [ ] **Step 4: Write test verifying intake appears in report**

Append to `backend/tests/test_intake_passthrough.py`:

```python
@pytest.mark.asyncio
async def test_medical_report_includes_patient_information_section():
    from nodes.medical_report_node import MedicalReportNode
    from unittest.mock import AsyncMock, patch

    node = MedicalReportNode()
    state = {
        "session_id": "test-session",
        "patient_intake": {
            "age": 45,
            "biological_sex": "female",
            "current_medications": "Lisinopril 10mg",
            "known_allergies": "Penicillin",
            "relevant_medical_history": "Hypertension",
        },
        "overall_analysis": {
            "final_diagnosis": "Hypertension",
            "final_confidence": 0.88,
            "final_severity": "moderate",
            "specialist_recommendation": "cardiologist",
            "user_explanation": "High blood pressure condition.",
            "clinical_reasoning": "Consistent with reported history.",
        },
        "workflow_path": ["textual_only"],
    }

    with patch.object(
        node, "_generate_followup_guidance", new_callable=AsyncMock
    ) as mock_guidance:
        mock_guidance.return_value = {"followup_guidance": "Follow up in 2 weeks."}
        result_state = await node.generate_medical_report_content(state)

    report = result_state["medical_report"]
    assert "PATIENT INFORMATION" in report
    assert "45" in report
    assert "Female" in report
    assert "Lisinopril" in report
    assert "Penicillin" in report
    assert "Hypertension" in report
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && python -m pytest tests/test_intake_passthrough.py -v
```
Expected: all tests pass (7 passed)

- [ ] **Step 6: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/nodes/medical_report_node.py backend/tests/test_intake_passthrough.py
git commit -m "feat(sp3): MedicalReportNode — PATIENT INFORMATION section in report, node contract"
```

---

## Task 7: Frontend — IntakeForm component

**Files:**
- Create: `my-app/src/components/medical/IntakeForm.tsx`

- [ ] **Step 1: Create IntakeForm.tsx**

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

interface IntakeFormProps {
  onSubmit: (intake: PatientIntake) => void;
}

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 560px;
  margin: 0 auto;
`;

const Field = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
`;

const Label = styled.label`
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary, #fff);
`;

const Input = styled.input`
  padding: 0.6rem 0.875rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #fff);
  font-size: 0.9rem;
  outline: none;
  &:focus { border-color: var(--primary, #6c63ff); }
`;

const Select = styled.select`
  padding: 0.6rem 0.875rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #fff);
  font-size: 0.9rem;
  outline: none;
  &:focus { border-color: var(--primary, #6c63ff); }
  option { background: #1a1a2e; }
`;

const Textarea = styled.textarea`
  padding: 0.6rem 0.875rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #fff);
  font-size: 0.9rem;
  resize: vertical;
  min-height: 70px;
  outline: none;
  &:focus { border-color: var(--primary, #6c63ff); }
`;

const Disclaimer = styled.p`
  font-size: 0.78rem;
  color: var(--text-secondary, rgba(255, 255, 255, 0.5));
  margin: 0;
`;

const SubmitBtn = styled.button`
  padding: 0.7rem 1.5rem;
  background: var(--primary, #6c63ff);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  align-self: flex-end;
  &:hover { opacity: 0.9; }
`;

const EMPTY: PatientIntake = {
  age: '',
  biological_sex: 'prefer_not_to_say',
  current_medications: '',
  known_allergies: '',
  relevant_medical_history: '',
};

export const IntakeForm: React.FC<IntakeFormProps> = ({ onSubmit }) => {
  const [intake, setIntake] = useState<PatientIntake>(EMPTY);

  const set =
    (field: keyof PatientIntake) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setIntake(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(intake);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Disclaimer>
        Do not enter real personally identifying information. Symptom data is processed by Groq AI.
      </Disclaimer>

      <Field>
        <Label htmlFor="intake-age">Age</Label>
        <Input
          id="intake-age"
          type="number"
          min={0}
          max={150}
          placeholder="e.g. 34"
          value={intake.age}
          onChange={set('age')}
        />
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
        <Textarea
          id="intake-meds"
          placeholder='"Metformin 500mg daily" — or "None"'
          value={intake.current_medications}
          onChange={set('current_medications')}
        />
      </Field>

      <Field>
        <Label htmlFor="intake-allergy">Known Allergies</Label>
        <Textarea
          id="intake-allergy"
          placeholder='"Penicillin, sulfa drugs" — or "None"'
          value={intake.known_allergies}
          onChange={set('known_allergies')}
        />
      </Field>

      <Field>
        <Label htmlFor="intake-history">Relevant Medical History</Label>
        <Textarea
          id="intake-history"
          placeholder='"Type 2 diabetes since 2020" — or "None"'
          value={intake.relevant_medical_history}
          onChange={set('relevant_medical_history')}
        />
      </Field>

      <SubmitBtn type="submit">Continue to Symptoms</SubmitBtn>
    </Form>
  );
};
```

- [ ] **Step 2: TypeScript compile check**

```bash
cd my-app && npx tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add my-app/src/components/medical/IntakeForm.tsx
git commit -m "feat(sp3): add IntakeForm component"
```

---

## Task 8: Frontend — wire intake into diagnosis flow

**Files:**
- Modify: `my-app/src/services/api.ts`
- Modify: `my-app/src/views/diagnosis.tsx`

- [ ] **Step 1: Update DiagnosisRequest in api.ts**

Find the `DiagnosisRequest` interface at the top of `my-app/src/services/api.ts`. Replace it:

Old:
```typescript
export interface DiagnosisRequest {
  symptoms: string;
  image?: File;
  location?: { lat: number; lng: number };
}
```

New:
```typescript
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

- [ ] **Step 2: Send intake fields in startTextualAnalysis**

In `startTextualAnalysis`, after the line `formData.append('session_id', sessionId);`, add:

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

- [ ] **Step 3: Read diagnosis.tsx before editing**

Read `my-app/src/views/diagnosis.tsx` in full to locate where `WorkflowRouter` is rendered and where `handleStartDiagnosis` is defined.

- [ ] **Step 4: Add import and intake state to diagnosis.tsx**

Add import at the top of `my-app/src/views/diagnosis.tsx`:
```typescript
import { IntakeForm, PatientIntake } from 'components/medical/IntakeForm';
```

Inside `DiagnosisFunction`, after the `useDiagnosis()` destructure, add:
```typescript
  const [patientIntake, setPatientIntake] = React.useState<PatientIntake | null>(null);
```

- [ ] **Step 5: Update handleStartDiagnosis to pass intake**

Find `handleStartDiagnosis`. Replace its `startDiagnosis` call:

Old:
```typescript
    await startDiagnosis({
      symptoms
    });
```

New:
```typescript
    await startDiagnosis({
      symptoms,
      patient_intake: patientIntake || undefined,
    });
```

- [ ] **Step 6: Gate WorkflowRouter behind intake completion**

In the JSX, add the intake form and gate the `WorkflowRouter`. Find the existing `<WorkflowRouter .../>` render. Wrap it as follows (fill in the existing props):

```tsx
{!patientIntake && !result && (
  <section style={{ padding: '2rem var(--spacing-md)', maxWidth: '600px', margin: '0 auto' }}>
    <h2 style={{ marginBottom: '1.5rem', color: 'var(--text-primary, #fff)', fontSize: '1.25rem' }}>
      Before we start — patient information
    </h2>
    <IntakeForm onSubmit={(intake) => setPatientIntake(intake)} />
  </section>
)}

{patientIntake && (
  <WorkflowRouter {/* existing props unchanged */} />
)}
```

Move the existing `<WorkflowRouter .../>` (with all its existing props) inside the `{patientIntake && (...)}` block and remove the old unconditional render.

- [ ] **Step 7: TypeScript compile check**

```bash
cd my-app && npx tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 8: End-to-end smoke test**

Start backend (`uvicorn main:app --reload --port 8000`) and frontend (`npm start` in `my-app/`). Complete a full diagnosis:

1. Navigate to diagnosis page — intake form appears first; no symptom input or WorkflowRouter visible
2. Fill in: Age=30, Biological Sex=Female, Medications=None, Allergies=None, History=None
3. Click "Continue to Symptoms" — symptom input appears
4. Submit symptoms: "I have a persistent headache for 3 days"
5. Check backend logs — `patient_intake` must be non-null in the initial state log
6. Complete full workflow: follow-up questions → submit → continue → report generation
7. Verify follow-up questions do NOT include any question about medications or allergies
8. Verify generated medical report contains a `PATIENT INFORMATION` section showing age=30, sex=Female

- [ ] **Step 9: Commit**

```bash
git add my-app/src/services/api.ts my-app/src/views/diagnosis.tsx
git commit -m "feat(sp3): wire IntakeForm into diagnosis flow — api.ts + diagnosis.tsx"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task(s) |
|---|---|
| Patient intake form: age, biological sex, medications, allergies, history | Tasks 7, 8 |
| Intake stored in `AgentState` and passed to all downstream nodes | Tasks 1, 2 |
| LLM diagnosis uses intake context | Task 3 |
| Overall analysis uses intake context | Task 5 |
| Medical report surfaces intake data | Task 6 |
| Zero overlap: follow-up questions never re-ask intake fields | Task 4 |
| Written boundary: inline node contract comment per node | Tasks 3, 4, 5, 6 |

**Placeholder scan:** No TBDs, TODOs, or "similar to Task N" references. All steps include complete code.

**Type consistency:**
- `PatientIntake` Python TypedDict: defined in Task 1 (`medical_schemas.py`), referenced in Tasks 2, 3, 5, 6
- `format_intake_context(intake)`: defined in Task 1, called in Tasks 3, 5, 6 — same signature throughout
- `PatientIntakeRequest` TypeScript interface: defined in Task 8 (`api.ts`), used in `DiagnosisRequest`
- `PatientIntake` TypeScript interface: exported from Task 7 (`IntakeForm.tsx`), imported in Task 8 (`diagnosis.tsx`)
- `IntakeForm` component: exported from Task 7, imported and used in Task 8

**SP2 dependency note:** Task 2 modifies `run_textual_analysis` assuming SP2 Task 4 is complete (function takes `request: Request`, uses `graph.ainvoke`). The intake Form parameters are purely additive and work in either the SP1 or SP2 version of the file — the only difference is where `initial_state` is constructed.
