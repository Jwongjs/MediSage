import sys, os, json
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.hpo import load_hpo
from diagnosis.ranking import rank

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "maccrobat_sample.json")


def _cases():
    if not os.path.exists(FIXTURE):
        pytest.skip("MACCROBAT fixture not present")
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


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
