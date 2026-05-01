import { useState } from "react";
import clsx from "clsx";
import { Button } from "@/shared/components/Button";
import type { DesignQuestion, Difficulty } from "../types";

const DIFFICULTIES: { id: Difficulty; label: string }[] = [
  { id: "junior", label: "Junior" },
  { id: "mid", label: "Mid" },
  { id: "senior", label: "Senior" },
];

type Props = {
  question: DesignQuestion | null;
  isFetchingQuestion: boolean;
  onFetchQuestion: (params: { difficulty?: Difficulty }) => void;
  onSubmit: () => void;
  canSubmit: boolean;
  isSubmitting: boolean;
  nodeCount: number;
  edgeCount: number;
  remainingToday: number | null;
  dailyLimit: number | null;
};

export function QuestionHeader({
  question,
  isFetchingQuestion,
  onFetchQuestion,
  onSubmit,
  canSubmit,
  isSubmitting,
  nodeCount,
  edgeCount,
  remainingToday,
  dailyLimit,
}: Props) {
  const [difficulty, setDifficulty] = useState<Difficulty | "">("");
  const [expanded, setExpanded] = useState(false);

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="flex items-start gap-4 px-4 py-3">
        <div className="flex-1 min-w-0">
          {question ? (
            <>
              <div className="flex items-center gap-2">
                <h1 className="truncate text-sm font-semibold text-slate-900">{question.title}</h1>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-600">
                  {question.difficulty}
                </span>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-600">
                  {question.category}
                </span>
                <button
                  type="button"
                  onClick={() => setExpanded((v) => !v)}
                  className="text-xs font-medium text-brand-600 hover:underline"
                >
                  {expanded ? "Hide prompt" : "Show prompt"}
                </button>
              </div>
              {expanded && (
                <p className="mt-2 max-w-3xl text-xs leading-relaxed text-slate-700">
                  {question.prompt}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">
              Pick a difficulty to load a design challenge.
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as Difficulty | "")}
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-400"
            aria-label="Difficulty filter"
            disabled={isFetchingQuestion}
          >
            <option value="">Any difficulty</option>
            {DIFFICULTIES.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              onFetchQuestion(difficulty ? { difficulty } : {})
            }
            disabled={isFetchingQuestion || isSubmitting}
          >
            {question ? "New question" : "Load question"}
          </Button>
          <Button
            onClick={onSubmit}
            disabled={!canSubmit || isSubmitting}
            size="sm"
          >
            {isSubmitting ? "Submitting…" : "Submit design"}
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4 border-t border-slate-100 bg-slate-50 px-4 py-1.5 text-xs">
        <span className="text-slate-600">
          {nodeCount} node{nodeCount === 1 ? "" : "s"} · {edgeCount} edge{edgeCount === 1 ? "" : "s"}
        </span>
        {remainingToday !== null && dailyLimit !== null && (
          <span className={clsx(
            "font-medium",
            remainingToday === 0 ? "text-rose-600" : "text-slate-700"
          )}>
            {remainingToday} of {dailyLimit} submissions remaining today
          </span>
        )}
      </div>
    </header>
  );
}
