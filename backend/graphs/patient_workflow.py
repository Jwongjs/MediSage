from __future__ import annotations
from langgraph.graph import StateGraph, END
from schemas.medical_schemas import AgentState

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


def compile_patient_workflow(checkpointer):
    from nodes import LLMDiagnosisNode, OverallAnalysisNode, MedicalReportNode
    from nodes.follow_up_interaction_node import FollowUpInteractionNode

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
