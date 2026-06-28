"""Integration tests through the compiled LangGraph patient workflow.

These exist because StateGraph(AgentState) silently drops input keys that are
not declared in the AgentState schema — node-level unit tests with plain dicts
cannot catch that class of bug.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langgraph.checkpoint.memory import MemorySaver

from graphs.patient_workflow import compile_patient_workflow

SYMPTOMS = "persistent headache on the right side with nausea and light sensitivity"

LLM_OUTPUT_LOW_CONFIDENCE = (
    "- Diagnosis: Migraine\n- Confidence: 0.8\n"
    "- Diagnosis: Tension headache\n- Confidence: 0.6\n"
)

LLM_OUTPUT_HIGH_CONFIDENCE = (
    "- Diagnosis: Migraine\n- Confidence: 0.9\n"
    "- Diagnosis: Tension headache\n- Confidence: 0.85\n"
)


def _initial_state(session_id: str) -> dict:
    # Mirrors the state built in diagnosis_routes.run_textual_analysis
    return {
        "session_id": session_id,
        "latest_user_message": SYMPTOMS,
        "userInput_symptoms": SYMPTOMS,
        "current_workflow_stage": "initializing",
    }


async def _invoke_diagnosis(llm_output: str, session_id: str):
    graph = compile_patient_workflow(MemorySaver())
    config = {"configurable": {"thread_id": session_id}}
    with patch("nodes.llm_diagnosis_node.llm_client") as mock_client:
        mock_client.complete = AsyncMock(return_value=llm_output)
        result = await graph.ainvoke(_initial_state(session_id), config)
        return graph, config, result, mock_client


@pytest.mark.asyncio
async def test_symptoms_reach_llm_through_compiled_graph():
    graph, config, result, mock_client = await _invoke_diagnosis(
        LLM_OUTPUT_LOW_CONFIDENCE, "test-session-1"
    )

    prompt = mock_client.complete.call_args.args[0][1]["content"]
    assert SYMPTOMS in prompt, "LLM was queried without the submitted symptoms"
    assert result["userInput_symptoms"] == SYMPTOMS
    assert result["textual_analysis"] == [
        {"text_diagnosis": "Migraine", "diagnosis_confidence": 0.8},
        {"text_diagnosis": "Tension headache", "diagnosis_confidence": 0.6},
    ]


@pytest.mark.asyncio
async def test_low_confidence_diagnosis_routes_to_followup():
    graph, config, result, _ = await _invoke_diagnosis(
        LLM_OUTPUT_LOW_CONFIDENCE, "test-session-2"
    )

    assert result["average_confidence"] == pytest.approx(0.7)
    snapshot = await graph.aget_state(config)
    assert list(snapshot.next) == ["generate_followup_questions"]


@pytest.mark.asyncio
async def test_high_confidence_diagnosis_routes_to_overall_analysis():
    graph, config, result, _ = await _invoke_diagnosis(
        LLM_OUTPUT_HIGH_CONFIDENCE, "test-session-3"
    )

    assert result["average_confidence"] == pytest.approx(0.875)
    snapshot = await graph.aget_state(config)
    assert list(snapshot.next) == ["overall_analysis"]
