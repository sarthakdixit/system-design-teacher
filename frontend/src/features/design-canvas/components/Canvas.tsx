import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  ConnectionMode,
  Controls,
  MarkerType,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeTypes,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { ComponentNodeData, ComponentType, Severity } from "../types";
import { PALETTE_BY_TYPE } from "../palette";
import { ComponentNode } from "./nodes/ComponentNode";
import { EmptyCanvasHint } from "./EmptyCanvasHint";
import { EdgeLabelEditor } from "./EdgeLabelEditor";

export type CanvasHandle = {
  getNodes: () => Node<ComponentNodeData>[];
  getEdges: () => Edge[];
  reset: () => void;
};

type Props = {
  affectedComponentIds: readonly string[];
  highlightSeverity: Severity | null;
  onChange?: (counts: { nodes: number; edges: number }) => void;
  registerHandle?: (handle: CanvasHandle) => void;
  readOnly?: boolean;
};

const NODE_TYPES: NodeTypes = {
  component: ComponentNode,
};

const DELETE_KEYS = ["Backspace", "Delete"];

function makeNodeId(): string {
  return `n_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`;
}

function makeEdgeId(): string {
  return `e_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`;
}

function CanvasInner({
  affectedComponentIds,
  highlightSeverity,
  onChange,
  registerHandle,
  readOnly = false,
}: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<ComponentNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedEdgeIds, setSelectedEdgeIds] = useState<Set<string>>(new Set());
  const [editingEdgeId, setEditingEdgeId] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const rfInstanceRef = useRef<ReactFlowInstance<Node<ComponentNodeData>, Edge> | null>(null);

  const handleLabelChange = useCallback(
    (id: string, label: string) => {
      setNodes((current) =>
        current.map((n) => (n.id === id ? { ...n, data: { ...n.data, label } } : n)),
      );
    },
    [setNodes],
  );

  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes((current) => current.filter((n) => n.id !== nodeId));
      setEdges((current) => current.filter((e) => e.source !== nodeId && e.target !== nodeId));
    },
    [setNodes, setEdges],
  );

  const handleDeleteEdge = useCallback(
    (edgeId: string) => {
      setEdges((current) => current.filter((e) => e.id !== edgeId));
    },
    [setEdges],
  );

  const handleEdgeLabelSave = useCallback(
    (edgeId: string, label: string) => {
      setEdges((current) =>
        current.map((e) => (e.id === edgeId ? { ...e, label: label || undefined } : e)),
      );
      setEditingEdgeId(null);
    },
    [setEdges],
  );

  const affectedSet = useMemo(() => new Set(affectedComponentIds), [affectedComponentIds]);

  const visualNodes = useMemo<Node<ComponentNodeData>[]>(() => {
    const hasSelection = affectedSet.size > 0;
    return nodes.map((n) => ({
      ...n,
      data: {
        ...n.data,
        isHighlighted: affectedSet.has(n.id),
        isDimmed: hasSelection && !affectedSet.has(n.id),
        highlightSeverity: highlightSeverity,
        onLabelChange: handleLabelChange,
        onDelete: handleDeleteNode,
      },
    }));
  }, [nodes, affectedSet, highlightSeverity, handleLabelChange, handleDeleteNode]);

  const visualEdges = useMemo<Edge[]>(() => {
    return edges.map((e) => ({
      ...e,
      style: {
        ...(e.style ?? {}),
        stroke: selectedEdgeIds.has(e.id) ? "#e11d48" : "#475569",
        strokeWidth: selectedEdgeIds.has(e.id) ? 3 : 2,
      },
      labelStyle: {
        fontSize: 11,
        fontWeight: 500,
        fill: "#1d3557",
      },
      labelBgStyle: {
        fill: "#f1faee",
        fillOpacity: 0.95,
      },
      labelBgPadding: [6, 4] as [number, number],
      labelBgBorderRadius: 4,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: selectedEdgeIds.has(e.id) ? "#e11d48" : "#475569",
        width: 18,
        height: 18,
      },
    }));
  }, [edges, selectedEdgeIds]);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id: makeEdgeId(),
            animated: false,
          },
          current,
        ),
      );
    },
    [setEdges],
  );

  const onSelectionChange = useCallback(({ edges: selEdges }: { edges: Edge[] }) => {
    setSelectedEdgeIds(new Set(selEdges.map((e) => e.id)));
    if (selEdges.length !== 1) {
      setEditingEdgeId(null);
    }
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const componentType = event.dataTransfer.getData(
        "application/sdt-component",
      ) as ComponentType;
      if (!componentType) return;
      const palette = PALETTE_BY_TYPE[componentType];
      if (!palette) return;
      const instance = rfInstanceRef.current;
      const wrapper = wrapperRef.current;
      if (!instance || !wrapper) return;
      const bounds = wrapper.getBoundingClientRect();
      const position = instance.screenToFlowPosition({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });
      const newNode: Node<ComponentNodeData> = {
        id: makeNodeId(),
        type: "component",
        position,
        data: {
          componentType,
          label: palette.defaultLabel,
        },
      };
      setNodes((current) => [...current, newNode]);
    },
    [setNodes],
  );

  useEffect(() => {
    if (!registerHandle) return;
    registerHandle({
      getNodes: () => nodes,
      getEdges: () => edges,
      reset: () => {
        setNodes([]);
        setEdges([]);
        setSelectedEdgeIds(new Set());
        setEditingEdgeId(null);
      },
    });
  }, [registerHandle, nodes, edges, setNodes, setEdges]);

  useEffect(() => {
    onChange?.({ nodes: nodes.length, edges: edges.length });
  }, [onChange, nodes.length, edges.length]);

  const selectedEdgeCount = selectedEdgeIds.size;
  const singleSelectedEdgeId = selectedEdgeCount === 1 ? Array.from(selectedEdgeIds)[0] : null;
  const editingEdge =
    editingEdgeId !== null ? edges.find((e) => e.id === editingEdgeId) ?? null : null;

  return (
    <div ref={wrapperRef} className="h-full w-full" onDragOver={onDragOver} onDrop={onDrop}>
      <ReactFlow
        nodes={visualNodes}
        edges={visualEdges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={readOnly ? undefined : onConnect}
        onSelectionChange={onSelectionChange}
        onInit={(instance) => {
          rfInstanceRef.current = instance;
        }}
        nodeTypes={NODE_TYPES}
        connectionMode={ConnectionMode.Loose}
        deleteKeyCode={DELETE_KEYS}
        defaultEdgeOptions={{
          style: { stroke: "#475569", strokeWidth: 2 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: "#475569",
            width: 18,
            height: 18,
          },
        }}
        fitView
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} color="#e2e8f0" />
        <MiniMap pannable zoomable className="!bg-white !border-slate-200" />
        <Controls className="!bg-white !border-slate-200" />
        <Panel position="top-right" className="!m-2">
          <div className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-[11px] text-slate-600 shadow-sm">
            <kbd className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[10px]">Backspace</kbd>{" "}
            or{" "}
            <kbd className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[10px]">Delete</kbd>{" "}
            to remove selected
          </div>
        </Panel>
        {!readOnly && editingEdge && (
          <Panel position="bottom-center" className="!mb-4">
            <EdgeLabelEditor
              edgeId={editingEdge.id}
              initialLabel={typeof editingEdge.label === "string" ? editingEdge.label : ""}
              onSave={handleEdgeLabelSave}
              onCancel={() => setEditingEdgeId(null)}
            />
          </Panel>
        )}
        {!readOnly && !editingEdge && singleSelectedEdgeId && (
          <Panel position="bottom-center" className="!mb-4">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setEditingEdgeId(singleSelectedEdgeId)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-md hover:bg-slate-50"
              >
                {edges.find((e) => e.id === singleSelectedEdgeId)?.label
                  ? "Edit label"
                  : "Add label"}
              </button>
              <button
                type="button"
                onClick={() => {
                  handleDeleteEdge(singleSelectedEdgeId);
                  setSelectedEdgeIds(new Set());
                }}
                className="rounded-md border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 shadow-md hover:bg-rose-50"
              >
                Delete edge
              </button>
            </div>
          </Panel>
        )}
        {!readOnly && !editingEdge && selectedEdgeCount > 1 && (
          <Panel position="bottom-center" className="!mb-4">
            <button
              type="button"
              onClick={() => {
                selectedEdgeIds.forEach(handleDeleteEdge);
                setSelectedEdgeIds(new Set());
              }}
              className="rounded-md border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 shadow-md hover:bg-rose-50"
            >
              Delete {selectedEdgeCount} edges
            </button>
          </Panel>
        )}
        {nodes.length === 0 && <EmptyCanvasHint />}
      </ReactFlow>
    </div>
  );
}

export function Canvas(props: Props) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
