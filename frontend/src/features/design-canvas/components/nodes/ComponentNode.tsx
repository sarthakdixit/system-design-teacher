import { Handle, Position, type NodeProps } from "@xyflow/react";
import clsx from "clsx";
import type { ComponentNodeData, Severity } from "../../types";
import { PALETTE_BY_TYPE } from "../../palette";

type Props = NodeProps & {
  data: ComponentNodeData & {
    highlightSeverity?: Severity | null;
    isHighlighted?: boolean;
    isDimmed?: boolean;
    onLabelChange?: (id: string, label: string) => void;
    onDelete?: (id: string) => void;
  };
};

const SEVERITY_RING: Record<Severity, string> = {
  critical: "ring-4 ring-rose-500 ring-offset-2",
  important: "ring-4 ring-amber-500 ring-offset-2",
  suggestion: "ring-4 ring-sky-500 ring-offset-2",
};

const HANDLE_BASE =
  "!h-3 !w-3 !border-2 !border-white !bg-slate-400 hover:!bg-brand-500 transition-colors";

export function ComponentNode({ id, data, selected }: Props) {
  const palette = PALETTE_BY_TYPE[data.componentType];
  if (!palette) return null;

  const ringClass =
    data.isHighlighted && data.highlightSeverity
      ? SEVERITY_RING[data.highlightSeverity]
      : "";

  return (
    <div
      className={clsx(
        "group relative rounded-lg border bg-white px-4 py-3 shadow-sm transition-all min-w-[140px]",
        selected ? "border-brand-500 shadow-md" : "border-slate-200",
        data.isDimmed && "opacity-30",
        ringClass,
      )}
      data-testid={`node-${id}`}
    >
      <Handle id="top" type="source" position={Position.Top} className={HANDLE_BASE} />
      <Handle id="right" type="source" position={Position.Right} className={HANDLE_BASE} />
      <Handle id="bottom" type="source" position={Position.Bottom} className={HANDLE_BASE} />
      <Handle id="left" type="source" position={Position.Left} className={HANDLE_BASE} />

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          data.onDelete?.(id);
        }}
        className={clsx(
          "absolute -right-2 -top-2 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[11px] font-bold text-white shadow-md transition-opacity hover:bg-rose-600",
          selected ? "opacity-100" : "opacity-0 group-hover:opacity-100",
        )}
        aria-label="Delete component"
        title="Delete this component (or press Backspace when selected)"
      >
        ×
      </button>

      <div className="flex items-start gap-2">
        <span className="text-xl leading-none" aria-hidden="true">
          {palette.icon}
        </span>
        <div className="flex-1 min-w-0">
          <input
            value={data.label}
            onChange={(e) => data.onLabelChange?.(id, e.target.value)}
            className="w-full bg-transparent text-sm font-medium text-slate-900 outline-none focus:bg-slate-50"
            aria-label={`Label for ${palette.label}`}
            maxLength={80}
          />
          <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">
            {palette.label}
          </p>
        </div>
      </div>
    </div>
  );
}
