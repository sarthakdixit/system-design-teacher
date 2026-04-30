import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/shared/components/Button";
import { EmptyState } from "@/shared/components/EmptyState";

type Props = {
  referenceAnswer: string | null;
};

export function AnswerReveal({ referenceAnswer }: Props) {
  const [revealed, setRevealed] = useState(false);

  if (referenceAnswer === null || referenceAnswer.trim() === "") {
    return (
      <EmptyState
        title="No reference answer yet"
        message="The reference answer for this question hasn't been generated yet. Run the generate_answers script to create one."
      />
    );
  }

  if (!revealed) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Try answering first</h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-600">
          Take a moment to think through your approach. Use the notes field below to capture your
          thoughts. When you're ready, reveal the reference answer to compare.
        </p>
        <div className="mt-4 flex justify-center">
          <Button onClick={() => setRevealed(true)}>Reveal reference answer</Button>
        </div>
      </div>
    );
  }

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <header className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Reference answer</h3>
        <Button variant="ghost" size="sm" onClick={() => setRevealed(false)}>
          Hide
        </Button>
      </header>
      <div className="markdown-body text-sm leading-7 text-slate-800">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{referenceAnswer}</ReactMarkdown>
      </div>
    </article>
  );
}
