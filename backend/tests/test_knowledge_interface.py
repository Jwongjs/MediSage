import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from knowledge.interface import Passage, retrieve_criteria_passages


async def test_retrieve_returns_a_list():
    passages = await retrieve_criteria_passages("Appendicitis")
    assert isinstance(passages, list)


async def test_retrieve_respects_k():
    passages = await retrieve_criteria_passages("Appendicitis", k=3)
    assert len(passages) <= 3


async def test_retrieve_returns_passage_objects():
    passages = await retrieve_criteria_passages("Appendicitis")
    assert all(isinstance(p, Passage) for p in passages)


async def test_unknown_diagnosis_returns_empty_not_error():
    assert await retrieve_criteria_passages("Zzzznotacondition") == []
