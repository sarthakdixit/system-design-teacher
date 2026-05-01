import { useCallback, useMemo, useRef, useState } from "react";
import { PageLayout } from "@/shared/components/PageLayout";
import { ErrorState } from "@/shared/components/ErrorState";
import {
  rateLimitDetailFromError,
  formatResetIn,
} from "@/shared/hooks/useRateLimitFromError";
import { Canvas, type CanvasHandle } from "./components/Canvas";
import { ComponentPalette } from "./components/ComponentPalette";
import { QuestionHeader } from "./components/QuestionHeader";
import { FeedbackPanel } from "./components/FeedbackPanel";
import { SubmittingOverlay } from "./components/SubmittingOverlay";
import {
  selectAffectedComponentIds,
  selectHighlightSeverity,
  useCanvasStore,
} from "./store";
import { useDesignQuestion } from "./hooks/useDesignQuestion";
import { useSubmitDesign } from "./hooks/useSubmitDesign";
import { useDiagramExport } from "./hooks/useDiagramExport";

export default function DesignCanvasPage() {
  const question = useCanvasStore((s) => s.question);
  const feedback = useCanvasStore((s) => s.feedback);
  const cacheHit = useCanvasStore((s) => s.cacheHit);
  const selectedFeedbackItem = useCanvasStore((s) => s.selectedFeedbackItem);
  const submissionStatus = useCanvasStore((s) => s.submissionStatus);
  const submissionError = useCanvasStore((s) => s.submissionError);
  const userNotes = useCanvasStore((s) => s.userNotes);

  const setQuestion = useCanvasStore((s) => s.setQuestion);
  const setFeedback = useCanvasStore((s) => s.setFeedback);
  const selectFeedbackItem = useCanvasStore((s) => s.selectFeedbackItem);
  const setSubmissionStatus = useCanvasStore((s) => s.setSubmissionStatus);
  const setUserNotes = useCanvasStore((s) => s.setUserNotes);

  const affectedIds = useCanvasStore(selectAffectedComponentIds);
  const highlightSeverity = useCanvasStore(selectHighlightSeverity);

  const [counts, setCounts] = useState({ nodes: 0, edges: 0 });
  const [rateLimit, setRateLimit] = useState<{ remaining: number; limit: number } | null>(null);

  const canvasHandleRef = useRef<CanvasHandle | null>(null);
  const exportDiagram = useDiagramExport();

  const fetchQuestion = useDesignQuestion((q) => {
    setQuestion(q);
    canvasHandleRef.current?.reset();
  });

  const submit = useSubmitDesign(
    (response) => {
      setFeedback(response.feedback, response.cacheHit);
      setRateLimit({
        remaining: response.rateLimit.userRemaining,
        limit: response.rateLimit.userLimit,
      });
    },
    (error) => {
      const detail = rateLimitDetailFromError(error);
      if (detail) {
        const reset = formatResetIn(detail.resetInSeconds);
        setSubmissionStatus(
          "failed",
          `You've used today's submissions. Resets ${reset}.`,
        );
        setRateLimit({ remaining: 0, limit: detail.userLimit });
        return;
      }
      const message =
        error instanceof Error ? error.message : "Submission failed. Please try again.";
      setSubmissionStatus("failed", message);
    },
  );

  const handleSubmit = useCallback(() => {
    if (!question) return;
    const handle = canvasHandleRef.current;
    if (!handle) return;
    const nodes = handle.getNodes();
    const edges = handle.getEdges();
    if (nodes.length === 0) {
      setSubmissionStatus("failed", "Add at least one component before submitting.");
      return;
    }
    setSubmissionStatus("submitting");
    const payload = exportDiagram({
      questionId: question.id,
      nodes,
      edges,
      userNotes,
    });
    submit.mutate(payload);
  }, [question, userNotes, exportDiagram, submit, setSubmissionStatus]);

  const handleFetchQuestion = useCallback(
    (params: { difficulty?: string }) => {
      fetchQuestion.mutate(params);
    },
    [fetchQuestion],
  );

  const isSubmitting = submissionStatus === "submitting";
  const canSubmit = useMemo(
    () =>
      question !== null &&
      counts.nodes > 0 &&
      submissionStatus !== "submitting" &&
      (rateLimit === null || rateLimit.remaining > 0),
    [question, counts.nodes, submissionStatus, rateLimit],
  );

  return (
    <PageLayout variant="fullWidth">
      <div className="flex h-full flex-col">
        <QuestionHeader
          question={question}
          isFetchingQuestion={fetchQuestion.isPending}
          onFetchQuestion={handleFetchQuestion}
          onSubmit={handleSubmit}
          canSubmit={canSubmit}
          isSubmitting={isSubmitting}
          nodeCount={counts.nodes}
          edgeCount={counts.edges}
          remainingToday={rateLimit?.remaining ?? null}
          dailyLimit={rateLimit?.limit ?? null}
        />

        {fetchQuestion.isError && !question && (
          <div className="p-4">
            <ErrorState
              message="Couldn't load a design question. Please try again."
              onRetry={() => handleFetchQuestion({})}
            />
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          <ComponentPalette disabled={isSubmitting} />

          <main className="relative flex-1 bg-white">
            <Canvas
              affectedComponentIds={affectedIds}
              highlightSeverity={highlightSeverity}
              onChange={setCounts}
              registerHandle={(h) => {
                canvasHandleRef.current = h;
              }}
              readOnly={isSubmitting}
            />
            {isSubmitting && <SubmittingOverlay />}
          </main>

          {feedback ? (
            <FeedbackPanel
              feedback={feedback}
              cacheHit={cacheHit}
              selectedItem={selectedFeedbackItem}
              onSelectItem={selectFeedbackItem}
            />
          ) : (
            <aside className="flex h-full w-96 flex-shrink-0 flex-col border-l border-slate-200 bg-slate-50 p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Your notes
              </h2>
              <textarea
                value={userNotes}
                onChange={(e) => setUserNotes(e.target.value)}
                placeholder="Capture your reasoning here. The AI will read these as part of evaluating your design (5000 char limit)."
                maxLength={5000}
                className="mt-2 flex-1 resize-none rounded-md border border-slate-300 bg-white p-3 text-xs text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-400"
                disabled={isSubmitting}
              />
              <p className="mt-1 text-[10px] text-slate-400">
                {userNotes.length} / 5000 characters
              </p>

              {submissionStatus === "failed" && submissionError && (
                <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                  {submissionError}
                </div>
              )}

              {!question && (
                <p className="mt-3 text-xs text-slate-500">
                  Load a question above to start designing.
                </p>
              )}
            </aside>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
