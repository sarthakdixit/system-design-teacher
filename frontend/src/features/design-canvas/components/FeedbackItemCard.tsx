import clsx from "clsx";
import type { FeedbackItem } from "../types";

type Props = {
  item: FeedbackItem;
  isSelected: boolean;
  onSelect: (item: FeedbackItem) => void;
};

const SEVERITY_STYLES = {
  critical: {
    border: "border-rose-300",
    badge: "bg-rose-100 text-rose-800",
    selected: "border-rose-500 bg-rose-50 ring-2 ring-rose-200",
  },
  important: {
    border: "border-amber-300",
    badge: "bg-amber-100 text-amber-800",
    selected: "border-amber-500 bg-amber-50 ring-2 ring-amber-200",
  },
  suggestion: {
    border: "border-sky-300",
    badge: "bg-sky-100 text-sky-800",
    selected: "border-sky-500 bg-sky-50 ring-2 ring-sky-200",
  },
} as const;

export function FeedbackItemCard({ item, isSelected, onSelect }: Props) {
  const styles = SEVERITY_STYLES[item.severity];

  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className={clsx(
        "w-full rounded-md border p-3 text-left text-xs transition-all",
        isSelected ? styles.selected : `bg-white ${styles.border} hover:bg-slate-50`,
      )}
      aria-pressed={isSelected}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold leading-snug text-slate-900">{item.title}</h4>
        <span
          className={clsx(
            "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
            styles.badge,
          )}
        >
          {item.severity}
        </span>
      </div>
      <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">{item.category}</p>
      <p className="mt-2 leading-relaxed text-slate-700">{item.description}</p>
      {item.suggestedChange && (
        <div className="mt-2 rounded bg-slate-50 p-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Suggested change
          </p>
          <p className="mt-0.5 leading-relaxed text-slate-700">{item.suggestedChange}</p>
        </div>
      )}
      {item.affectedComponents.length > 0 && (
        <p className="mt-2 text-[10px] text-slate-500">
          Affects {item.affectedComponents.length} component
          {item.affectedComponents.length === 1 ? "" : "s"}{" "}
          {isSelected ? "(highlighted on canvas)" : "(click to highlight)"}
        </p>
      )}
    </button>
  );
}
