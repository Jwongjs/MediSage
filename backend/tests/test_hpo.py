import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.hpo import normalize, parse_obo

SAMPLE = """
format-version: 1.2

[Term]
id: HP:0002027
name: Abdominal pain
synonym: "Belly pain" EXACT layperson []
synonym: "Pain in stomach" EXACT layperson []

[Term]
id: HP:0001945
name: Fever
synonym: "Hyperthermia" EXACT []
synonym: "High temperature" EXACT layperson []

[Term]
id: HP:0100749
name: Chest pain

[Term]
id: HP:0000822
name: Hypertension
is_obsolete: true
"""


def test_normalize_lowercases_and_strips_punctuation():
    assert normalize("  Abdominal Pain!  ") == "abdominal pain"


def test_normalize_strips_leading_article():
    assert normalize("The Fever") == "fever"


def test_normalize_collapses_whitespace():
    assert normalize("chest    pain") == "chest pain"


def test_lookup_matches_primary_label():
    idx = parse_obo(SAMPLE)
    assert idx.lookup("Abdominal pain") == "HP:0002027"


def test_lookup_matches_layperson_synonym():
    idx = parse_obo(SAMPLE)
    assert idx.lookup("belly pain") == "HP:0002027"


def test_lookup_returns_none_for_unknown_term():
    idx = parse_obo(SAMPLE)
    assert idx.lookup("rebound tenderness") is None


def test_label_returns_primary_name_not_synonym():
    idx = parse_obo(SAMPLE)
    assert idx.label("HP:0002027") == "Abdominal pain"


def test_obsolete_terms_are_excluded():
    idx = parse_obo(SAMPLE)
    assert idx.lookup("hypertension") is None


def test_terms_yields_id_label_pairs_for_embedding():
    idx = parse_obo(SAMPLE)
    ids = {hp_id for hp_id, _ in idx.terms()}
    assert ids == {"HP:0002027", "HP:0001945", "HP:0100749"}
