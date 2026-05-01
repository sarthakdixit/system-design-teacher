import { useCallback } from "react";
import type { Edge, Node } from "@xyflow/react";
import type { ComponentNodeData, ComponentType, SubmitDesignPayload } from "../types";

export function useDiagramExport() {
  return useCallback(
    (params: {
      questionId: string;
      nodes: Node<ComponentNodeData>[];
      edges: Edge[];
      userNotes: string;
    }): SubmitDesignPayload => {
      const exportedNodes = params.nodes.map((node) => ({
        id: node.id,
        type: node.data.componentType as ComponentType,
        label: node.data.label,
      }));

      const exportedEdges = params.edges.map((edge) => ({
        id: edge.id,
        sourceId: edge.source,
        targetId: edge.target,
      }));

      const trimmedNotes = params.userNotes.trim();

      return {
        questionId: params.questionId,
        diagram: {
          nodes: exportedNodes,
          edges: exportedEdges,
        },
        userNotes: trimmedNotes === "" ? null : trimmedNotes,
      };
    },
    [],
  );
}
