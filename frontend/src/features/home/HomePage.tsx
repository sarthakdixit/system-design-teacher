import { Link } from "react-router-dom";
import { PageLayout } from "@/shared/components/PageLayout";

export function HomePage() {
  return (
    <PageLayout title="Practice modes">
      <p className="mb-6 max-w-2xl text-slate-600">
        Pick a mode to practice for system-design interviews. Each mode is independent — you can
        switch any time.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/practice/situation"
          className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
        >
          <div className="text-3xl" aria-hidden>
            📚
          </div>
          <h2 className="mt-3 text-lg font-semibold text-slate-900 group-hover:text-brand-600">
            Situation practice
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Read a real-world scenario, think through your approach, and compare against a
            reference answer. Best for warming up.
          </p>
          <div className="mt-3 text-sm font-medium text-brand-600">Start &rarr;</div>
        </Link>
        <Link
          to="/practice/design"
          className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
        >
          <div className="text-3xl" aria-hidden>
            🎨
          </div>
          <h2 className="mt-3 text-lg font-semibold text-slate-900 group-hover:text-brand-600">
            Design canvas
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Drag system components onto a canvas, connect them, and submit for AI feedback. The
            headline interview workout.
          </p>
          <div className="mt-3 text-sm font-medium text-brand-600">Start &rarr;</div>
        </Link>
      </div>
    </PageLayout>
  );
}
