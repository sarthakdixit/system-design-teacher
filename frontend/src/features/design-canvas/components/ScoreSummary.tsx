import clsx from "clsx";
import type { DesignFeedback } from "../types";

type Props = {
  feedback: DesignFeedback;
  cacheHit: boolean;
};

const LEVEL_COLOR: Record<DesignFeedback["estimatedLevel"], string> = {
  junior: "bg-amber-100 text-amber-800",
  mid: "bg-sky-100 text-sky-800",
  senior: "bg-emerald-100 text-emerald-800",
};

function scoreColor(score: number): string {
  if (score >= 8) return "text-emerald-600";
  if (score >= 5) return "text-amber-600";
  return "text-rose-600";
}

export function ScoreSummary({ feedback, cacheHit }: Props) {
  return (
    <div className="border-b border-slate-200 bg-white p-4">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Overall score
          </p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className={clsx("text-3xl font-bold", scoreColor(feedback.overallScore))}>
              {feedback.overallScore}
            </span>
            <span className="text-sm text-slate-500">/ 10</span>
          </div>
        </div>
        <span
          className={clsx(
            "rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
            LEVEL_COLOR[feedback.estimatedLevel],
          )}
        >
          {feedback.estimatedLevel}
        </span>
      </div>

      {cacheHit && (
        <p className="mt-3 rounded bg-slate-50 px-2 py-1 text-[11px] text-slate-600">
          Served from cache — feedback was generated for an identical design previously.
        </p>
      )}

      {feedback.strengths.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Strengths
          </h3>
          <ul className="mt-1.5 space-y-1">
            {feedback.strengths.map((s, i) => (
              <li key={i} className="flex gap-1.5 text-xs text-slate-700">
                <span className="text-emerald-600">✓</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
