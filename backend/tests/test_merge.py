import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.merge import merge_profiles, local_key, normalize, Criterion


def _crit(text, importance="strong", kind="symptom", plain_label=None):
    crit = {"text": text, "importance": importance, "kind": kind}
    if plain_label is not None:
        crit["plain_label"] = plain_label
    return crit


def test_normalize_lowercases_and_strips_punctuation():
    assert normalize("  Abdominal Pain!  ") == "abdominal pain"


def test_normalize_strips_leading_article():
    assert normalize("The Fever") == "fever"


def test_normalize_collapses_whitespace():
    assert normalize("chest    pain") == "chest pain"


@pytest.mark.asyncio
async def test_identical_terms_across_diagnoses_merge_to_one_key():
    # Not an HPO synonym pair -- literally the same text, case/punctuation
    # variant. Exact-string equality (via normalize()) is the entire
    # cross-diagnosis linking mechanism now.
    profiles = {
        "Appendicitis": [_crit("Abdominal pain")],
        "Gastroenteritis": [_crit("abdominal pain!")],
    }
    result = await merge_profiles(profiles)
    assert len(result.canonical) == 1
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_differently_worded_criteria_stay_separate():
    # "Fever" and "Elevated temperature" are not linked -- there is no
    # ontology to know they're related, by design.
    profiles = {
        "Appendicitis": [_crit("Fever")],
        "Influenza": [_crit("Elevated temperature")],
    }
    result = await merge_profiles(profiles)
    assert len(result.canonical) == 2


@pytest.mark.asyncio
async def test_merged_criterion_keeps_the_first_seen_text_as_label():
    profiles = {
        "Appendicitis": [_crit("Abdominal pain")],
        "Gastroenteritis": [_crit("abdominal pain!")],
    }
    result = await merge_profiles(profiles)
    assert result.canonical[0].label == "Abdominal pain"


@pytest.mark.asyncio
async def test_plain_label_is_threaded_through_from_the_profile():
    profiles = {"Appendicitis": [_crit("Abdominal pain", plain_label="belly pain")]}
    result = await merge_profiles(profiles)
    assert result.canonical[0].plain_label == "belly pain"


@pytest.mark.asyncio
async def test_plain_label_falls_back_to_the_raw_criterion_text_when_missing():
    profiles = {"Appendicitis": [_crit("Abdominal pain")]}
    result = await merge_profiles(profiles)
    assert result.canonical[0].plain_label == "Abdominal pain"


@pytest.mark.asyncio
async def test_matrix_keeps_per_diagnosis_importance():
    profiles = {
        "Appendicitis": [_crit("Abdominal pain", "strong")],
        "Gastroenteritis": [_crit("Abdominal pain", "weak")],
    }
    result = await merge_profiles(profiles)
    key = result.canonical[0].key
    assert result.matrix["Appendicitis"][key] == "strong"
    assert result.matrix["Gastroenteritis"][key] == "weak"


@pytest.mark.asyncio
async def test_symptom_gets_a_local_key():
    profiles = {"Appendicitis": [_crit("Rebound tenderness")]}
    result = await merge_profiles(profiles)
    assert result.canonical[0].key.startswith("LOCAL:")


@pytest.mark.asyncio
async def test_local_key_is_stable_for_equivalent_strings():
    assert local_key("Rebound Tenderness!") == local_key("rebound tenderness")


@pytest.mark.asyncio
async def test_matrix_covers_every_diagnosis_even_with_no_criteria():
    profiles = {"Appendicitis": [_crit("Fever")], "Migraine": []}
    result = await merge_profiles(profiles)
    assert result.matrix["Migraine"] == {}


@pytest.mark.asyncio
async def test_a_criterion_with_no_kind_field_defaults_to_symptom():
    profiles = {"Influenza": [{"text": "Fever", "importance": "strong"}]}
    result = await merge_profiles(profiles)
    assert result.canonical[0].kind == "symptom"
