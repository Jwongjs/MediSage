import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.ranking import tally, sort_key, rank


def _j(**kw):
    return {k: {"status": v, "evidence": None, "source": "llm"} for k, v in kw.items()}


def test_tally_counts_by_importance_and_status():
    matrix = {"A": {"k1": "strong", "k2": "strong", "k3": "weak"}}
    judgements = _j(k1="supported", k2="not_mentioned", k3="contradicted")
    counts = tally("A", matrix, judgements)
    assert counts[("strong", "supported")] == 1
    assert counts[("strong", "not_mentioned")] == 1
    assert counts[("weak", "contradicted")] == 1


def test_tally_treats_unjudged_key_as_not_mentioned():
    matrix = {"A": {"k1": "strong"}}
    counts = tally("A", matrix, {})
    assert counts[("strong", "not_mentioned")] == 1


def test_more_strong_support_ranks_higher():
    matrix = {
        "A": {"k1": "strong", "k2": "strong"},
        "B": {"k1": "strong"},
    }
    judgements = _j(k1="supported", k2="supported")
    groups = rank(matrix, judgements)
    assert groups[0] == ["A"]
    assert groups[1] == ["B"]


def test_strong_contradiction_dominates_strong_support():
    # A has two strong supports and one strong contradiction.
    # B has one strong support and nothing contradicted. B must win.
    matrix = {
        "A": {"k1": "strong", "k2": "strong", "k3": "strong"},
        "B": {"k1": "strong"},
    }
    judgements = _j(k1="supported", k2="supported", k3="contradicted")
    groups = rank(matrix, judgements)
    assert groups[0] == ["B"]
    assert groups[1] == ["A"]


def test_fewer_strong_missing_breaks_a_support_tie():
    matrix = {
        "A": {"k1": "strong", "k2": "strong"},
        "B": {"k1": "strong"},
    }
    judgements = _j(k1="supported", k2="not_mentioned")
    groups = rank(matrix, judgements)
    assert groups[0] == ["B"]


def test_identical_evidence_produces_one_tie_group():
    matrix = {"A": {"k1": "strong"}, "B": {"k1": "strong"}}
    judgements = _j(k1="supported")
    assert rank(matrix, judgements) == [["A", "B"]]


def test_moderate_only_breaks_ties_after_all_strong_fields():
    matrix = {
        "A": {"k1": "strong", "k2": "moderate"},
        "B": {"k1": "strong", "k3": "moderate"},
    }
    judgements = _j(k1="supported", k2="supported", k3="not_mentioned")
    groups = rank(matrix, judgements)
    assert groups[0] == ["A"]


def test_diagnosis_with_no_criteria_is_neutral_not_last():
    # An empty tally is (0,) * 8 — neutral, not worst. It ranks below a
    # candidate carrying support, but ABOVE one whose criteria are all
    # unconfirmed. Documented deliberately: a candidate whose profile failed
    # to generate must not be read as a well-evidenced one.
    assert rank({"A": {"k1": "strong"}, "Empty": {}}, _j(k1="supported")) == [["A"], ["Empty"]]
    assert rank({"A": {"k1": "strong"}, "Empty": {}}, _j(k1="not_mentioned")) == [["Empty"], ["A"]]


def test_moderate_contradiction_outweighs_an_unconfirmed_moderate():
    matrix = {"A": {"m1": "moderate"}, "B": {"m2": "moderate"}}
    judgements = _j(m1="contradicted", m2="not_mentioned")
    assert rank(matrix, judgements) == [["B"], ["A"]]


def test_more_moderate_support_ranks_higher():
    matrix = {"A": {"m1": "moderate", "m2": "moderate"}, "B": {"m1": "moderate"}}
    judgements = _j(m1="supported", m2="supported")
    assert rank(matrix, judgements) == [["A"], ["B"]]


def test_fewer_unconfirmed_moderate_ranks_higher():
    matrix = {"A": {"m1": "moderate", "m2": "moderate"}, "B": {"m1": "moderate"}}
    judgements = _j(m1="not_mentioned", m2="not_mentioned")
    assert rank(matrix, judgements) == [["B"], ["A"]]


def test_weak_contradiction_ranks_below_an_unconfirmed_weak():
    # B's weak_missing is absent from the tuple, so B's key is all zeros.
    matrix = {"A": {"w1": "weak"}, "B": {"w2": "weak"}}
    judgements = _j(w1="contradicted", w2="not_mentioned")
    assert rank(matrix, judgements) == [["B"], ["A"]]


def test_weak_support_ranks_above_an_unconfirmed_weak():
    matrix = {"A": {"w1": "weak"}, "B": {"w2": "weak"}}
    judgements = _j(w1="supported", w2="not_mentioned")
    assert rank(matrix, judgements) == [["A"], ["B"]]
