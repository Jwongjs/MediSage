import sys, os
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.evidence_node import reconcile, chunk_criteria, EvidenceNode, CHUNK_SIZE
from diagnosis.merge import Criterion

TEXT = "I have had stomach pain since yesterday and a slight fever."
CRITS = [
    Criterion("HP:0002027", "Abdominal pain", "symptom"),
    Criterion("HP:0001945", "Fever", "symptom"),
]


def test_reconcile_keeps_valid_supported_judgement():
    raw = {"HP:0002027": {"status": "supported", "evidence": "stomach pain"}}
    out = reconcile(raw, CRITS, TEXT)
    assert out["HP:0002027"]["status"] == "supported"
    assert out["HP:0002027"]["evidence"] == "stomach pain"


def test_reconcile_defaults_omitted_key_to_not_mentioned():
    out = reconcile({}, CRITS, TEXT)
    assert out["HP:0001945"]["status"] == "not_mentioned"


def test_reconcile_discards_keys_that_were_not_requested():
    raw = {"HP:9999999": {"status": "supported", "evidence": "stomach pain"}}
    assert "HP:9999999" not in reconcile(raw, CRITS, TEXT)


def test_reconcile_downgrades_non_verbatim_evidence():
    raw = {"HP:0002027": {"status": "supported", "evidence": "patient reports belly ache"}}
    out = reconcile(raw, CRITS, TEXT)
    assert out["HP:0002027"]["status"] == "not_mentioned"
    assert out["HP:0002027"]["evidence"] is None


def test_reconcile_verbatim_check_ignores_case():
    raw = {"HP:0002027": {"status": "supported", "evidence": "Stomach Pain"}}
    assert reconcile(raw, CRITS, TEXT)["HP:0002027"]["status"] == "supported"


def test_reconcile_downgrades_supported_with_no_evidence():
    raw = {"HP:0002027": {"status": "supported", "evidence": None}}
    assert reconcile(raw, CRITS, TEXT)["HP:0002027"]["status"] == "not_mentioned"


def test_reconcile_rejects_unknown_status():
    raw = {"HP:0002027": {"status": "probably", "evidence": "stomach pain"}}
    assert reconcile(raw, CRITS, TEXT)["HP:0002027"]["status"] == "not_mentioned"


def test_reconcile_clears_evidence_on_not_mentioned():
    raw = {"HP:0002027": {"status": "not_mentioned", "evidence": "stomach pain"}}
    assert reconcile(raw, CRITS, TEXT)["HP:0002027"]["evidence"] is None


def test_reconcile_stamps_llm_as_source():
    out = reconcile({}, CRITS, TEXT)
    assert out["HP:0002027"]["source"] == "llm"


def test_chunking_splits_above_the_threshold():
    many = [Criterion(f"k{i}", f"c{i}", "symptom") for i in range(CHUNK_SIZE + 5)]
    chunks = chunk_criteria(many)
    assert len(chunks) == 2
    assert sum(len(c) for c in chunks) == CHUNK_SIZE + 5


def test_chunks_are_disjoint():
    many = [Criterion(f"k{i}", f"c{i}", "symptom") for i in range(CHUNK_SIZE + 5)]
    chunks = chunk_criteria(many)
    keys = [c.key for chunk in chunks for c in chunk]
    assert len(keys) == len(set(keys))


def test_no_chunking_at_or_below_threshold():
    exact = [Criterion(f"k{i}", f"c{i}", "symptom") for i in range(CHUNK_SIZE)]
    assert len(chunk_criteria(exact)) == 1


async def test_node_preserves_existing_patient_answers():
    existing = {"HP:0001945": {"status": "supported", "evidence": "yes", "source": "patient_answer"}}
    payload = '{"HP:0002027": {"status": "supported", "evidence": "stomach pain"}}'
    with patch("nodes.evidence_node.llm_client") as client:
        client.complete = AsyncMock(return_value=payload)
        state = await EvidenceNode()({
            "patient_text": TEXT, "canonical": CRITS, "judgements": existing,
        })
    assert state["judgements"]["HP:0001945"]["source"] == "patient_answer"
    assert state["judgements"]["HP:0002027"]["status"] == "supported"


def test_reconcile_tolerates_whitespace_differences_in_the_quote():
    # A textarea gives line breaks and double spaces; the model quotes with
    # single spaces. That must still count as verbatim.
    text = "I have pain in my lower\nback  that radiates down my leg."
    crits = [Criterion("k", "Back pain", "symptom")]
    raw = {"k": {"status": "supported", "evidence": "pain in my lower back that radiates"}}
    out = reconcile(raw, crits, text)
    assert out["k"]["status"] == "supported"
    assert out["k"]["evidence"] == "pain in my lower\nback  that radiates"


def test_reconcile_stores_the_patient_words_not_the_model_casing():
    text = "i have stomach pain"
    crits = [Criterion("k", "Abdominal pain", "symptom")]
    raw = {"k": {"status": "supported", "evidence": "Stomach Pain"}}
    assert reconcile(raw, crits, text)["k"]["evidence"] == "stomach pain"


async def test_node_drops_patient_answers_for_criteria_no_longer_canonical():
    stale = {"HP:9999999": {"status": "supported", "evidence": "yes", "source": "patient_answer"}}
    payload = '{"HP:0002027": {"status": "supported", "evidence": "stomach pain"}}'
    with patch("nodes.evidence_node.llm_client") as client:
        client.complete = AsyncMock(return_value=payload)
        state = await EvidenceNode()({
            "patient_text": TEXT, "canonical": CRITS, "judgements": stale,
        })
    assert "HP:9999999" not in state["judgements"]
    assert set(state["judgements"]) == {c.key for c in CRITS}


async def test_prompt_uses_plain_label_when_present():
    crits = [Criterion("HP:0002027", "Abdominal pain", "symptom", plain_label="belly pain")]
    captured = []

    async def capture(messages, **kw):
        captured.append(messages)
        return "{}"

    with patch("nodes.evidence_node.llm_client") as client:
        client.complete = AsyncMock(side_effect=capture)
        await EvidenceNode()({"patient_text": TEXT, "canonical": crits})

    prompt = captured[0][1]["content"]
    assert "belly pain" in prompt
    assert "Abdominal pain" not in prompt


async def test_prompt_falls_back_to_clinical_label_without_a_plain_label():
    async def capture(messages, **kw):
        captured.append(messages)
        return "{}"

    captured = []
    with patch("nodes.evidence_node.llm_client") as client:
        client.complete = AsyncMock(side_effect=capture)
        await EvidenceNode()({"patient_text": TEXT, "canonical": CRITS})

    assert "Abdominal pain" in captured[0][1]["content"]


async def test_node_makes_no_llm_call_when_there_are_no_criteria():
    with patch("nodes.evidence_node.llm_client") as client:
        client.complete = AsyncMock(return_value="{}")
        state = await EvidenceNode()({"patient_text": TEXT, "canonical": []})
    assert client.complete.await_count == 0
    assert state["judgements"] == {}
