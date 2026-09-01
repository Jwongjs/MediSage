from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from diagnosis.hpo import load_hpo
from diagnosis.merge import merge_profiles
from diagnosis.ranking import rank, open_questions
from schemas.diagnosis_schemas import DiagnosisState

logger = logging.getLogger(__name__)

_hpo = None


def _get_hpo():
    global _hpo
    if _hpo is None:
        _hpo = load_hpo()
        logger.info("HPO index loaded with %d terms", len(_hpo.labels))
    return _hpo


class MergeRankNode:
    """Deterministic. No LLM call, no network."""

    async def __call__(self, state: dict) -> dict:
        profiles = state.get("profiles", {})
        # Embedding fallback is disabled: merge.py embeds every HPO label
        # serially when a symptom misses the exact index (19,836 terms, twice
        # per request). Needs precomputed vectors before it can be enabled.
        # Unmatched symptoms take LOCAL: keys until then.
        result = await merge_profiles(profiles, _get_hpo())

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
        state["open_questions"] = open_questions(
            result.canonical, ranking_matrix, judgements, evaluated
        )
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
