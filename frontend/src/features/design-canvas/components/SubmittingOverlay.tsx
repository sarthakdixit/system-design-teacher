import { useEffect, useState } from "react";

const PROGRESS_MESSAGES = [
  "Reading your architecture…",
  "Checking for missing components…",
  "Looking at trade-offs and bottlenecks…",
  "Calibrating feedback to your level…",
  "Almost there…",
];

export function SubmittingOverlay() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % PROGRESS_MESSAGES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/90 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4 rounded-lg border border-slate-200 bg-white px-8 py-6 shadow-lg">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand-500" />
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-900">Generating feedback</p>
          <p className="mt-1 min-h-[1rem] text-xs text-slate-600 transition-opacity">
            {PROGRESS_MESSAGES[messageIndex]}
          </p>
        </div>
        <p className="text-[11px] text-slate-400">This usually takes 10–30 seconds</p>
      </div>
    </div>
  );
}
