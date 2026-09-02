import sys, os, json
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.hpo import load_hpo
from diagnosis.merge import merge_profiles
from diagnosis.ranking import rank, open_questions

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "maccrobat_sample.json")


def _cases():
    if not os.path.exists(FIXTURE):
        pytest.skip("MACCROBAT fixture not present")
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


async def test_merge_collapses_duplicate_symptoms_across_profiles():
    hpo = load_hpo()
    if not hpo.labels:
        pytest.skip("hp.obo not downloaded")

    # "Stomach pain" is a real HPO synonym of HP:0002027. The plan used
    # "Belly pain", which the fixture ontology invented but the published
    # ontology does not carry, so it would never have merged.
    profiles = {
        "Appendicitis": [
            {"text": "Abdominal pain", "importance": "strong", "kind": "symptom"},
            {"text": "Fever", "importance": "moderate", "kind": "symptom"},
        ],
        "Acute gastroenteritis": [
            {"text": "Stomach pain", "importance": "strong", "kind": "symptom"},
            {"text": "Fever", "importance": "weak", "kind": "symptom"},
        ],
    }
    result = await merge_profiles(profiles, hpo)
    # Two diagnoses, four raw criteria, two distinct concepts.
    assert len(result.canonical) == 2


async def test_annotated_symptoms_resolve_against_the_ontology():
    """The documented symptoms of real case reports should mostly canonicalize.

    Not an accuracy metric — a regression guard. If a change to normalize() or
    the OBO parser silently breaks lookup, this collapses to LOCAL: keys.
    """
    hpo = load_hpo()
    if not hpo.labels:
        pytest.skip("hp.obo not downloaded")

    symptoms = sorted({s for case in _cases() for s in case["annotated_symptoms"]})
    resolved = [s for s in symptoms if hpo.lookup(s) is not None]
    assert len(resolved) >= len(symptoms) // 2, (
        f"only {len(resolved)}/{len(symptoms)} annotated symptoms resolved: "
        f"{[s for s in symptoms if hpo.lookup(s) is None]}"
    )


async def test_every_fixture_case_produces_a_stable_ranking():
    for case in _cases():
        matrix = {case["documented_diagnosis"]: {"k1": "strong"}, "Alternative": {"k1": "weak"}}
        judgements = {"k1": {"status": "supported", "evidence": "x", "source": "llm"}}
        groups = rank(matrix, judgements)
        assert groups[0] == [case["documented_diagnosis"]]


async def test_questions_are_never_generated_for_fully_judged_criteria():
    from diagnosis.merge import Criterion
    canonical = [Criterion("k1", "Fever", "symptom")]
    matrix = {"A": {"k1": "strong"}, "B": {}}
    judgements = {"k1": {"status": "contradicted", "evidence": "no fever", "source": "llm"}}
    assert open_questions(canonical, matrix, judgements, ["A", "B"]) == []
