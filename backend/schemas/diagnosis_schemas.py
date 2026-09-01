from typing_extensions import TypedDict

# Criterion is the frozen dataclass from diagnosis.merge — the merge stage
# produces real instances and they live in state unchanged. Do NOT redeclare
# it as a TypedDict here: two types with one name, where state holds the
# dataclass, is how attribute access starts failing at runtime.
from diagnosis.merge import Criterion

Stage = str  # started | differential_complete | profiles_complete |
             # evidence_complete | ranked | awaiting_answers | complete

__all__ = ["Criterion", "Judgement", "Summary", "DiagnosisState", "Stage"]


class Judgement(TypedDict):
    status: str          # supported | contradicted | not_mentioned
    evidence: str | None  # verbatim span from patient text
    source: str          # llm | patient_answer


class Summary(TypedDict, total=False):
    severity: str                    # mild|moderate|severe|critical|unknown
    specialist_recommendation: str
    user_explanation: str | None     # from MedlinePlus, omitted if unavailable
    explanation_source: str | None
    explanation_url: str | None


class DiagnosisState(TypedDict, total=False):
    session_id: str
    stage: Stage
    patient_text: str

    candidates: list[str]
    profiles: dict[str, list[dict]]
    grounded: dict[str, bool]

    canonical: list[Criterion]
    matrix: dict[str, dict[str, str]]
    judgements: dict[str, Judgement]

    ranking: list[list[str]]
    not_evaluated: list[str]
    open_questions: list[str]
    answers: dict[str, str]          # criterion key -> yes | no | unsure

    summary: Summary | None
    steps: list[dict]
