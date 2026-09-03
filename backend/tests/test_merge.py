import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.hpo import parse_obo
from diagnosis.merge import merge_profiles, local_key

SAMPLE = """
[Term]
id: HP:0002027
name: Abdominal pain
synonym: "Belly pain" EXACT layperson []

[Term]
id: HP:0001945
name: Fever
synonym: "Low-grade fever" EXACT []

[Term]
id: HP:0100749
name: Chest pain

[Term]
id: HP:0031352
name: Chest tightness
"""

HPO = parse_obo(SAMPLE)


def _crit(text, importance="strong", kind="symptom", plain_label=None):
    crit = {"text": text, "importance": importance, "kind": kind}
    if plain_label is not None:
        crit["plain_label"] = plain_label
    return crit


@pytest.mark.asyncio
async def test_identical_terms_across_diagnoses_merge_to_one_key():
    profiles = {
        "Appendicitis": [_crit("Abdominal pain")],
        "Gastroenteritis": [_crit("Belly pain")],
    }
    result = await merge_profiles(profiles, HPO)
    assert len(result.canonical) == 1
    assert result.canonical[0].key == "HP:0002027"


@pytest.mark.asyncio
async def test_merged_criterion_uses_hpo_primary_label():
    profiles = {"Gastroenteritis": [_crit("Belly pain")]}
    result = await merge_profiles(profiles, HPO)
    assert result.canonical[0].label == "Abdominal pain"


@pytest.mark.asyncio
async def test_plain_label_is_threaded_through_from_the_profile():
    profiles = {"Appendicitis": [_crit("Abdominal pain", plain_label="belly pain")]}
    result = await merge_profiles(profiles, HPO)
    assert result.canonical[0].plain_label == "belly pain"


@pytest.mark.asyncio
async def test_plain_label_falls_back_to_the_raw_criterion_text_when_missing():
    profiles = {"Appendicitis": [_crit("Abdominal pain")]}
    result = await merge_profiles(profiles, HPO)
    assert result.canonical[0].plain_label == "Abdominal pain"


@pytest.mark.asyncio
async def test_matrix_keeps_per_diagnosis_importance():
    profiles = {
        "Appendicitis": [_crit("Abdominal pain", "strong")],
        "Gastroenteritis": [_crit("Belly pain", "weak")],
    }
    result = await merge_profiles(profiles, HPO)
    assert result.matrix["Appendicitis"]["HP:0002027"] == "strong"
    assert result.matrix["Gastroenteritis"]["HP:0002027"] == "weak"


@pytest.mark.asyncio
async def test_unmatched_symptom_gets_local_key():
    profiles = {"Appendicitis": [_crit("Rebound tenderness")]}
    result = await merge_profiles(profiles, HPO)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_non_symptom_kinds_bypass_hpo_entirely():
    profiles = {"Appendicitis": [_crit("Abdominal pain", kind="lab")]}
    result = await merge_profiles(profiles, HPO)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_local_key_is_stable_for_equivalent_strings():
    assert local_key("Rebound Tenderness!") == local_key("rebound tenderness")


@pytest.mark.asyncio
async def test_embedding_fallback_accepts_confident_unambiguous_match():
    # "Pyrexia" is close to Fever and far from everything else.
    vectors = {
        "Pyrexia": [1.0, 0.0, 0.0],
        "Fever": [0.99, 0.14, 0.0],
        "Abdominal pain": [0.0, 1.0, 0.0],
        "Chest pain": [0.0, 0.0, 1.0],
        "Chest tightness": [0.0, 0.0, 1.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Influenza": [_crit("Pyrexia")]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key == "HP:0001945"


@pytest.mark.asyncio
async def test_margin_guard_rejects_ambiguous_match():
    # Equidistant from Chest pain and Chest tightness — must NOT merge into either.
    vectors = {
        "Chest discomfort": [0.0, 0.0, 1.0],
        "Chest pain": [0.0, 0.0, 1.0],
        "Chest tightness": [0.0, 0.0, 1.0],
        "Fever": [1.0, 0.0, 0.0],
        "Abdominal pain": [0.0, 1.0, 0.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Angina": [_crit("Chest discomfort")]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_matrix_covers_every_diagnosis_even_with_no_criteria():
    profiles = {"Appendicitis": [_crit("Fever")], "Migraine": []}
    result = await merge_profiles(profiles, HPO)
    assert result.matrix["Migraine"] == {}


@pytest.mark.asyncio
async def test_accept_threshold_rejects_a_confident_looking_but_low_score_match():
    # cos == 0.85 against Fever, margin 0.85 — only the accept gate can reject this.
    vectors = {
        "Febrile sensation": [1.0, 0.0, 0.0],
        "Fever": [0.85, 0.5267827, 0.0],
        "Abdominal pain": [0.0, 1.0, 0.0],
        "Chest pain": [0.0, 0.0, 1.0],
        "Chest tightness": [0.0, 0.0, 1.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Influenza": [_crit("Febrile sensation")]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_margin_guard_rejects_a_two_point_margin():
    # Both scores clear the accept gate; margin is 0.02, just under 0.03.
    vectors = {
        "Pyrexial episode": [1.0, 0.0, 0.0],
        "Fever": [0.95, 0.3122499, 0.0],
        "Abdominal pain": [0.93, 0.0, 0.3675595],
        "Chest pain": [0.0, 1.0, 0.0],
        "Chest tightness": [0.0, 0.0, 1.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Influenza": [_crit("Pyrexial episode")]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_margin_guard_accepts_a_four_point_margin():
    # Same shape, margin 0.04 — above the gate, so this one must merge.
    vectors = {
        "Raised temperature": [1.0, 0.0, 0.0],
        "Fever": [0.95, 0.3122499, 0.0],
        "Abdominal pain": [0.91, 0.0, 0.4146082],
        "Chest pain": [0.0, 1.0, 0.0],
        "Chest tightness": [0.0, 0.0, 1.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Influenza": [_crit("Raised temperature")]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key == "HP:0001945"


@pytest.mark.asyncio
async def test_criterion_with_no_kind_field_still_reaches_the_embedding_fallback():
    # An LLM may omit "kind" entirely. merge_profiles defaults it to symptom, so
    # the fallback gate must default it the same way or the criterion silently
    # takes a LOCAL key instead of merging.
    vectors = {
        "Pyrexia": [1.0, 0.0, 0.0],
        "Fever": [0.99, 0.14, 0.0],
        "Abdominal pain": [0.0, 1.0, 0.0],
        "Chest pain": [0.0, 0.0, 1.0],
        "Chest tightness": [0.0, 0.0, 1.0],
    }

    async def embed(text):
        return vectors[text]

    profiles = {"Influenza": [{"text": "Pyrexia", "importance": "strong"}]}
    result = await merge_profiles(profiles, HPO, embed_fn=embed)
    assert result.canonical[0].key == "HP:0001945"
