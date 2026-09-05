from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from diagnosis.merge import merge_profiles
from diagnosis.ranking import rank
from schemas.diagnosis_schemas import DiagnosisState

logger = logging.getLogger(__name__)


class MergeRankNode:
    """Deterministic. No LLM call, no network."""

    async def __call__(self, state: dict) -> dict:
        profiles = state.get("profiles", {})
        result = await merge_profiles(profiles)

        judgements = state.get("judgements", {}) or {}
        candidates = state.get("candidates", [])

        # A candidate with no criteria was never evaluated. Ranking it would
        # PROMOTE it: an empty tally is (0,)*8, which beats a candidate whose
        # criteria are merely unconfirmed.
        evaluated = [d for d in candidates if result.matrix.get(d)]
        not_evaluated = [d for d in candidates if not result.matrix.get(d)]
        ranking_matrix = {d: result.matrix[d] for d in evaluated}

        state["canonical"] = result.canonical
        state["matrix"] = result.matrix
        state["ranking"] = rank(ranking_matrix, judgements)
        state["not_evaluated"] = not_evaluated
        state["stage"] = "ranked"
        return state


def compile_diagnosis_workflow(checkpointer):
    from nodes.differential_node import DifferentialNode
    from nodes.profile_node import ProfileNode
    from nodes.evidence_node import EvidenceNode
    from nodes.summary_node import SummaryNode

    workflow = StateGraph(DiagnosisState)
    workflow.set_entry_point("differential")

    workflow.add_node("differential", DifferentialNode())
    workflow.add_node("profiles", ProfileNode())
    workflow.add_node("merge_rank_pre", MergeRankNode())
    workflow.add_node("evidence", EvidenceNode())
    workflow.add_node("merge_rank", MergeRankNode())
    workflow.add_node("summary", SummaryNode())

    # Linear. The only branch is the user deciding to answer questions,
    # which happens outside the graph between invocations.
    workflow.add_edge("differential", "profiles")
    workflow.add_edge("profiles", "merge_rank_pre")
    workflow.add_edge("merge_rank_pre", "evidence")
    workflow.add_edge("evidence", "merge_rank")
    workflow.add_edge("merge_rank", "summary")
    workflow.add_edge("summary", END)

    return workflow.compile(checkpointer=checkpointer, interrupt_before=["summary"])