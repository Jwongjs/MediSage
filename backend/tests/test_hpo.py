import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.hpo import parse_obo

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


def test_lookup_strips_prose_wrappers_that_hpo_does_not_use():
    # Node B writes clinical prose; HPO names bare concepts. Measured on real
    # Node B output this lifts exact-match resolution from 9% to 35%.
    idx = parse_obo(SAMPLE)
    assert idx.lookup("Presence of fever") == "HP:0001945"
    assert idx.lookup("Fever (typically low-grade)") == "HP:0001945"
    assert idx.lookup("Abdominal pain, often localized to the right lower quadrant") == "HP:0002027"


def test_lookup_does_not_split_compound_criteria():
    # "Nausea and/or vomiting" is not the same criterion as "Nausea".
    # Mapping a compound onto one part silently drops the other concept.
    idx = parse_obo(SAMPLE)
    assert idx.lookup("Fever and chills") is None


def test_strip_prose_leaves_a_plain_term_untouched():
    from diagnosis.hpo import strip_prose
    assert strip_prose("Abdominal pain") == "Abdominal pain"
