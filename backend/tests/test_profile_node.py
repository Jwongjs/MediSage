import sys, os
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.profile_node import parse_profile, ProfileNode, clear_cache
from knowledge.interface import Passage

VALID = """[
  {"id": 1, "description": "Right lower quadrant pain", "plain_label": "pain in lower right belly", "importance": "strong", "kind": "symptom"},
  {"id": 2, "description": "Leukocytosis", "plain_label": "high white blood cell count", "importance": "moderate", "kind": "lab"}
]"""


def setup_function():
    clear_cache()


def test_parse_reads_description_importance_and_kind():
    crits = parse_profile(VALID)
    assert crits[0] == {
        "text": "Right lower quadrant pain",
        "plain_label": "pain in lower right belly",
        "importance": "strong",
        "kind": "symptom",
    }


def test_parse_defaults_missing_plain_label_to_empty_string():
    raw = '[{"description": "X", "importance": "weak"}]'
    assert parse_profile(raw)[0]["plain_label"] == ""


def test_parse_tolerates_fenced_json():
    crits = parse_profile("```json\n" + VALID + "\n```")
    assert len(crits) == 1


def test_parse_defaults_invalid_importance_to_moderate():
    raw = '[{"description": "X", "importance": "critical", "kind": "symptom"}]'
    assert parse_profile(raw)[0]["importance"] == "moderate"


def test_parse_defaults_missing_kind_to_symptom():
    assert parse_profile('[{"description": "X", "importance": "weak"}]')[0]["kind"] == "symptom"


def test_parse_drops_kinds_the_patient_cannot_answer_for():
    # lab/imaging/demographic criteria can only ever come back not_mentioned --
    # nothing in this flow lets a patient report a test result, their age or
    # their sex -- and an unaddressed strong/moderate criterion counts against
    # the condition in the ranking. Dropping them here keeps them out of the
    # matrix entirely rather than hiding them at display time.
    raw = """[
      {"description": "Fever", "importance": "strong", "kind": "symptom"},
      {"description": "Recent travel", "importance": "moderate", "kind": "history"},
      {"description": "Leukocytosis", "importance": "strong", "kind": "lab"},
      {"description": "Free air under the diaphragm", "importance": "strong", "kind": "imaging"},
      {"description": "More common in men", "importance": "weak", "kind": "demographic"}
    ]"""
    assert [c["text"] for c in parse_profile(raw)] == ["Fever", "Recent travel"]


def test_parse_keeps_an_unrecognised_kind_as_a_symptom():
    # The filter rejects kinds it recognises as unanswerable, not garbage: an
    # unknown kind still falls back to "symptom" rather than being dropped.
    raw = '[{"description": "X", "importance": "weak", "kind": "vibes"}]'
    assert parse_profile(raw)[0]["kind"] == "symptom"


def test_parse_drops_exclusion_criteria():
    # A negated criterion can never be supported: Node C requires a verbatim
    # quote and an absence is unquotable, so it parks at not_mentioned and
    # penalises the condition. It also renders as a double negative under the
    # "Do you have these?" checkbox.
    raw = """[
      {"description": "Bilateral pressing head pain", "importance": "strong",
       "kind": "symptom", "polarity": "present"},
      {"description": "Absence of nausea or vomiting", "importance": "strong",
       "kind": "symptom", "polarity": "absent"},
      {"description": "Not attributed to another disorder", "importance": "strong",
       "kind": "history", "polarity": "absent"}
    ]"""
    assert [c["text"] for c in parse_profile(raw)] == ["Bilateral pressing head pain"]


def test_parse_treats_a_missing_polarity_as_present():
    raw = '[{"description": "Fever", "importance": "strong", "kind": "symptom"}]'
    assert [c["text"] for c in parse_profile(raw)] == ["Fever"]


def test_parse_drops_entries_without_a_description():
    assert parse_profile('[{"importance": "strong", "kind": "symptom"}]') == []


def test_parse_returns_empty_on_malformed_json():
    assert parse_profile("not json at all") == []


async def test_node_builds_one_profile_per_candidate():
    with patch("nodes.profile_node.llm_client") as llm, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        llm.complete = AsyncMock(return_value=VALID)
        state = await ProfileNode()({"candidates": ["Appendicitis", "Migraine"]})
    assert set(state["profiles"]) == {"Appendicitis", "Migraine"}


async def test_node_marks_ungrounded_when_no_passages_retrieved():
    with patch("nodes.profile_node.llm_client") as llm, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(return_value=[])):
        llm.complete = AsyncMock(return_value=VALID)
        state = await ProfileNode()({"candidates": ["Appendicitis"]})
    assert state["grounded"]["Appendicitis"] is False


async def test_second_call_for_same_diagnosis_hits_cache():
    llm = AsyncMock(return_value=VALID)
    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        client.complete = llm
        await ProfileNode()({"candidates": ["Appendicitis"]})
        await ProfileNode()({"candidates": ["Appendicitis"]})
    assert llm.await_count == 1


async def test_a_failing_candidate_does_not_fail_the_others():
    async def flaky(messages, **kw):
        if "Migraine" in messages[1]["content"]:
            raise RuntimeError("upstream 500")
        return VALID

    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        client.complete = AsyncMock(side_effect=flaky)
        state = await ProfileNode()({"candidates": ["Appendicitis", "Migraine"]})
    assert len(state["profiles"]["Appendicitis"]) == 1
    assert state["profiles"]["Migraine"] == []


async def test_patient_text_never_reaches_the_prompt():
    # The load-bearing isolation property. If the presentation is in context
    # while criteria are written, the model writes criteria that fit the
    # patient and every criterion later returns supported — the mechanism
    # collapses into self-agreement, silently.
    sentinel = "SENTINEL_PATIENT_NARRATIVE_9137"
    captured = []

    async def capture(messages, **kw):
        captured.append(messages)
        return VALID

    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        client.complete = AsyncMock(side_effect=capture)
        await ProfileNode()({
            "candidates": ["Appendicitis"],
            "patient_text": sentinel,
            "symptoms": sentinel,
        })

    assert captured, "the node made no LLM call"
    for messages in captured:
        for message in messages:
            assert sentinel not in message["content"]


async def test_cached_profile_keeps_its_ungrounded_flag():
    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(return_value=[])):
        client.complete = AsyncMock(return_value=VALID)
        first = await ProfileNode()({"candidates": ["Appendicitis"]})
        second = await ProfileNode()({"candidates": ["Appendicitis"]})
    assert first["grounded"]["Appendicitis"] is False
    assert second["grounded"]["Appendicitis"] is False


async def test_cached_profile_keeps_its_grounded_flag():
    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        client.complete = AsyncMock(return_value=VALID)
        first = await ProfileNode()({"candidates": ["Appendicitis"]})
        second = await ProfileNode()({"candidates": ["Appendicitis"]})
    assert first["grounded"]["Appendicitis"] is True
    assert second["grounded"]["Appendicitis"] is True


async def test_profiles_are_not_aliased_to_the_shared_cache():
    with patch("nodes.profile_node.llm_client") as client, \
         patch("nodes.profile_node.retrieve_criteria_passages", new=AsyncMock(
             return_value=[Passage("txt", "statpearls", "1")])):
        client.complete = AsyncMock(return_value=VALID)
        first = await ProfileNode()({"candidates": ["Appendicitis"]})
        first["profiles"]["Appendicitis"].clear()
        first["profiles"]["Appendicitis"] = []
        second = await ProfileNode()({"candidates": ["Appendicitis"]})
    assert len(second["profiles"]["Appendicitis"]) == 1
