import clsx from "clsx";
import type { SituationQuestion } from "@/features/situation-practice/types";

type Props = {
  question: SituationQuestion;
};

const DIFFICULTY_CLASSES: Record<SituationQuestion["difficulty"], string> = {
  junior: "bg-emerald-100 text-emerald-800",
  mid: "bg-amber-100 text-amber-800",
  senior: "bg-rose-100 text-rose-800",
};

const DIFFICULTY_LABEL: Record<SituationQuestion["difficulty"], string> = {
  junior: "Junior",
  mid: "Mid",
  senior: "Senior",
};

export function QuestionCard({ question }: Props) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-xl font-semibold text-slate-900">{question.title}</h2>
        <div className="flex flex-shrink-0 items-center gap-2">
          <span
            className={clsx(
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
              DIFFICULTY_CLASSES[question.difficulty],
            )}
          >
            {DIFFICULTY_LABEL[question.difficulty]}
          </span>
          <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
            {question.category}
          </span>
        </div>
      </div>

      <p className="mt-4 whitespace-pre-line text-sm leading-6 text-slate-700">{question.prompt}</p>

      {question.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {question.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded bg-slate-50 px-2 py-0.5 text-xs text-slate-600 ring-1 ring-inset ring-slate-200"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
