"""Shared data shapes for the diagnosis graph.

`Explanation` holds a candidate's plain-language definition, produced by
Node A (see `nodes/differential_node.py`) directly from the LLM's own
knowledge -- no retrieval involved.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    text: str
    source: str
    url: str
