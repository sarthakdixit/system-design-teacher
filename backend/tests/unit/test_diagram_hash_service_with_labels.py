from __future__ import annotations

import pytest

from app.core.domain.diagram import Diagram, DiagramEdge, DiagramNode
from app.core.services.diagram_hash_service import DiagramHashService

_QUESTION_ID = "q-test-1"


def _make_diagram(*, edge_labels: list[str | None] | None = None) -> Diagram:
    nodes = [
        DiagramNode(id="n1", type="user", label="User"),
        DiagramNode(id="n2", type="api_gateway", label="API Gateway"),
        DiagramNode(id="n3", type="cache", label="Cache"),
        DiagramNode(id="n4", type="database", label="Database"),
    ]
    raw_edges = [
        ("e1", "n1", "n2"),
        ("e2", "n2", "n3"),
        ("e3", "n3", "n4"),
    ]
    labels = edge_labels or [None] * len(raw_edges)
    edges = [
        DiagramEdge(id=eid, source_id=src, target_id=tgt, label=label)
        for (eid, src, tgt), label in zip(raw_edges, labels, strict=True)
    ]
    return Diagram(nodes=nodes, edges=edges)


@pytest.mark.unit
def test_unlabeled_and_labeled_diagrams_hash_differently() -> None:
    service = DiagramHashService()
    unlabeled = _make_diagram()
    labeled = _make_diagram(edge_labels=["entry", "read path", "fallback"])

    h_unlabeled = service.hash(question_id=_QUESTION_ID, diagram=unlabeled)
    h_labeled = service.hash(question_id=_QUESTION_ID, diagram=labeled)

    assert h_unlabeled != h_labeled


@pytest.mark.unit
def test_identical_diagrams_with_same_labels_hash_identically() -> None:
    service = DiagramHashService()
    a = _make_diagram(edge_labels=["entry", "read path", "fallback"])
    b = _make_diagram(edge_labels=["entry", "read path", "fallback"])

    assert service.hash(question_id=_QUESTION_ID, diagram=a) == service.hash(
        question_id=_QUESTION_ID, diagram=b
    )


@pytest.mark.unit
def test_different_labels_hash_differently() -> None:
    service = DiagramHashService()
    a = _make_diagram(edge_labels=["entry", "read path", "fallback"])
    b = _make_diagram(edge_labels=["entry", "WRITE path", "fallback"])

    assert service.hash(question_id=_QUESTION_ID, diagram=a) != service.hash(
        question_id=_QUESTION_ID, diagram=b
    )


@pytest.mark.unit
def test_label_normalization_makes_case_irrelevant() -> None:
    service = DiagramHashService()
    a = _make_diagram(edge_labels=["READ PATH", None, None])
    b = _make_diagram(edge_labels=["read path", None, None])

    assert service.hash(question_id=_QUESTION_ID, diagram=a) == service.hash(
        question_id=_QUESTION_ID, diagram=b
    )


@pytest.mark.unit
def test_label_whitespace_makes_no_difference() -> None:
    service = DiagramHashService()
    a = _make_diagram(edge_labels=["  read path  ", None, None])
    b = _make_diagram(edge_labels=["read path", None, None])

    assert service.hash(question_id=_QUESTION_ID, diagram=a) == service.hash(
        question_id=_QUESTION_ID, diagram=b
    )
