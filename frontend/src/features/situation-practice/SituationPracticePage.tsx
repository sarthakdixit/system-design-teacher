import { useState } from "react";
import { PageLayout } from "@/shared/components/PageLayout";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { Button } from "@/shared/components/Button";
import { ErrorState } from "@/shared/components/ErrorState";
import { Skeleton } from "@/shared/components/Skeleton";
import { rateLimitDetailFromError, formatResetIn } from "@/shared/hooks/useRateLimitFromError";
import { FilterBar } from "@/features/situation-practice/components/FilterBar";
import { QuestionCard } from "@/features/situation-practice/components/QuestionCard";
import { AnswerReveal } from "@/features/situation-practice/components/AnswerReveal";
import { NotesField } from "@/features/situation-practice/components/NotesField";
import { RateLimitBanner } from "@/features/situation-practice/components/RateLimitBanner";
import { useSituationQuestion } from "@/features/situation-practice/hooks/useSituationQuestion";
import { useRecordAttempt } from "@/features/situation-practice/hooks/useRecordAttempt";
import { useRateLimits } from "@/features/situation-practice/hooks/useRateLimits";
import type {
  CategoryValue,
  DifficultyValue,
} from "@/features/situation-practice/constants";

export function SituationPracticePage() {
  return (
    <RequireAuth>
      <PageLayout>
        <SituationPracticeContent />
      </PageLayout>
    </RequireAuth>
  );
}

function SituationPracticeContent() {
  const [category, setCategory] = useState<CategoryValue | "">("");
  const [difficulty, setDifficulty] = useState<DifficultyValue | "">("");
  const [notes, setNotes] = useState("");
  const [attemptRecorded, setAttemptRecorded] = useState(false);

  const fetcher = useSituationQuestion();
  const recorder = useRecordAttempt();
  const rateLimitsQuery = useRateLimits();

  const question = fetcher.data?.question ?? null;
  const fetchRateLimit = fetcher.data?.rateLimit ?? null;
  const rateLimitFromError = rateLimitDetailFromError(fetcher.error);

  const handleFetch = () => {
    setNotes("");
    setAttemptRecorded(false);
    recorder.reset();
    fetcher.mutate({
      category: category || undefined,
      difficulty: (difficulty || undefined) as "junior" | "mid" | "senior" | undefined,
    });
  };

  const handleRecordAttempt = () => {
    if (!question) return;
    recorder.mutate(
      { questionId: question.id, userNotes: notes.trim() || null },
      {
        onSuccess: () => setAttemptRecorded(true),
      },
    );
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">Situation Practice</h1>
        <p className="mt-1 text-sm text-slate-600">
          Pick filters and fetch a curated system-design situation. Try answering before revealing.
        </p>
      </header>

      {rateLimitsQuery.data && (
        <div className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-700">
          <p>
            <strong>Today&apos;s budget:</strong> {rateLimitsQuery.data.situationFetch.userRemaining} of{" "}
            {rateLimitsQuery.data.situationFetch.userLimit} situation fetches remaining · resets in{" "}
            {formatResetIn(rateLimitsQuery.data.situationFetch.resetInSeconds)}
          </p>
        </div>
      )}

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <FilterBar
          category={category}
          difficulty={difficulty}
          onCategoryChange={setCategory}
          onDifficultyChange={setDifficulty}
          disabled={fetcher.isPending}
        />
        <div className="mt-4 flex items-center gap-3">
          <Button onClick={handleFetch} disabled={fetcher.isPending}>
            {fetcher.isPending ? "Fetching…" : question ? "Fetch a different question" : "Fetch a question"}
          </Button>
          {question && !fetcher.isPending && (
            <span className="text-xs text-slate-500">Each fetch consumes one of your daily budget.</span>
          )}
        </div>
      </section>

      {fetcher.isPending && (
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
      )}

      {fetcher.isError && rateLimitFromError && (
        <ErrorState
          title="Daily limit reached"
          message={`${rateLimitFromError.detail}. Resets in ${formatResetIn(rateLimitFromError.resetInSeconds)}.`}
        />
      )}

      {fetcher.isError && !rateLimitFromError && (
        <ErrorState
          message={
            fetcher.error instanceof Error
              ? fetcher.error.message
              : "Could not fetch a question. Please try again."
          }
          onRetry={handleFetch}
        />
      )}

      {question && (
        <>
          <RateLimitBanner rateLimit={fetchRateLimit} />

          <QuestionCard question={question} />

          <NotesField value={notes} onChange={setNotes} disabled={recorder.isPending} />

          <AnswerReveal referenceAnswer={question.referenceAnswer} />

          <div className="flex items-center justify-end gap-3">
            {attemptRecorded ? (
              <span className="text-sm text-emerald-700">Attempt recorded ✓</span>
            ) : (
              <Button
                variant="secondary"
                onClick={handleRecordAttempt}
                disabled={recorder.isPending}
              >
                {recorder.isPending ? "Saving…" : "Record this attempt"}
              </Button>
            )}
          </div>

          {recorder.isError && (
            <ErrorState
              message={
                recorder.error instanceof Error
                  ? recorder.error.message
                  : "Could not save the attempt."
              }
            />
          )}
        </>
      )}
    </div>
  );
}
