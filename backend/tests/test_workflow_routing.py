import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graphs.patient_workflow import _route_after_diagnosis, _route_after_followup


def test_route_diagnosis_low_confidence_goes_to_followup():
    state = {"average_confidence": 0.5, "requires_skin_cancer_screening": False}
    assert _route_after_diagnosis(state) == "generate_followup_questions"


def test_route_diagnosis_skin_cancer_flag_goes_to_followup():
    state = {"average_confidence": 0.9, "requires_skin_cancer_screening": True}
    assert _route_after_diagnosis(state) == "generate_followup_questions"


def test_route_diagnosis_high_confidence_no_screening_goes_to_overall():
    state = {"average_confidence": 0.8, "requires_skin_cancer_screening": False}
    assert _route_after_diagnosis(state) == "overall_analysis"


def test_route_diagnosis_no_confidence_field_goes_to_overall():
    state = {}
    assert _route_after_diagnosis(state) == "overall_analysis"


def test_route_followup_requires_input_loops_back():
    state = {"requires_user_input": True}
    assert _route_after_followup(state) == "generate_followup_questions"


def test_route_followup_done_goes_to_overall():
    state = {"requires_user_input": False}
    assert _route_after_followup(state) == "overall_analysis"


def test_route_followup_no_flag_defaults_to_overall():
    state = {}
    assert _route_after_followup(state) == "overall_analysis"
