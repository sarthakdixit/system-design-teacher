from __future__ import annotations

import hashlib
import json

from app.core.domain.diagram import Diagram, DiagramEdge, DiagramNode


class DiagramHashService:
    def hash(self, *, question_id: str, diagram: Diagram) -> str:
        canonical = self._canonical(diagram)
        payload = {
            "question_id": question_id,
            "diagram": canonical,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _canonical(self, diagram: Diagram) -> dict[str, list[dict[str, str]]]:
        node_lookup = {n.id: n for n in diagram.nodes}

        sorted_nodes = sorted(
            diagram.nodes,
            key=lambda n: (n.type, n.label.strip().lower(), n.id),
        )

        sorted_edges = sorted(
            diagram.edges,
            key=lambda e: self._edge_sort_key(e, node_lookup),
        )

        return {
            "nodes": [self._canonical_node(n) for n in sorted_nodes],
            "edges": [self._canonical_edge(e, node_lookup) for e in sorted_edges],
        }

    def _canonical_node(self, node: DiagramNode) -> dict[str, str]:
        return {
            "type": node.type,
            "label": node.label.strip().lower(),
        }

    def _canonical_edge(
        self,
        edge: DiagramEdge,
        node_lookup: dict[str, DiagramNode],
    ) -> dict[str, str]:
        source = node_lookup.get(edge.source_id)
        target = node_lookup.get(edge.target_id)
        return {
            "source_type": source.type if source else "unknown",
            "source_label": source.label.strip().lower() if source else "",
            "target_type": target.type if target else "unknown",
            "target_label": target.label.strip().lower() if target else "",
        }

    def _edge_sort_key(
        self,
        edge: DiagramEdge,
        node_lookup: dict[str, DiagramNode],
    ) -> tuple[str, str, str, str]:
        source = node_lookup.get(edge.source_id)
        target = node_lookup.get(edge.target_id)
        return (
            source.type if source else "unknown",
            source.label.strip().lower() if source else "",
            target.type if target else "unknown",
            target.label.strip().lower() if target else "",
        )