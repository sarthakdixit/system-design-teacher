import { Link } from "react-router-dom";
import { PageLayout } from "@/shared/components/PageLayout";
import { Button } from "@/shared/components/Button";
import { useAuthStore } from "@/features/auth/store";
import { LoginButton } from "@/features/auth/components/LoginButton";
import { ProfileCard } from "@/features/auth/components/ProfileCard";

export function HomePage() {
  const isAuthenticated = useAuthStore((s) => s.accessToken !== null);

  return (
    <PageLayout>
      {isAuthenticated ? <AuthenticatedHome /> : <UnauthenticatedHome />}
    </PageLayout>
  );
}

function UnauthenticatedHome() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
      <h2 className="text-2xl font-semibold text-slate-900">Welcome</h2>
      <p className="mx-auto mt-3 max-w-md text-sm text-slate-600">
        Sign in to start practicing system design interviews. In development this uses a mock user —
        no Microsoft account required.
      </p>
      <div className="mt-6 flex justify-center">
        <LoginButton />
      </div>
    </div>
  );
}

function AuthenticatedHome() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-6">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Practice modes</h2>
          <p className="mt-1 text-sm text-slate-600">
            Choose how you want to practice today.
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <Link
              to="/practice/situation"
              className="block rounded-lg border border-slate-200 p-4 transition hover:border-brand-500 hover:bg-brand-50"
            >
              <h3 className="text-base font-semibold text-slate-900">Situation practice</h3>
              <p className="mt-1 text-sm text-slate-600">
                Quick scenario-based questions. Read the prompt, jot your approach, then compare to a
                reference answer.
              </p>
              <div className="mt-3">
                <Button variant="secondary" size="sm">Start →</Button>
              </div>
            </Link>

            <div className="block rounded-lg border border-dashed border-slate-300 p-4 opacity-60">
              <h3 className="text-base font-semibold text-slate-900">Design canvas</h3>
              <p className="mt-1 text-sm text-slate-600">
                Drag-and-drop architecture practice with AI feedback. Coming in the next batch.
              </p>
              <div className="mt-3">
                <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                  Coming soon
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <aside>
        <ProfileCard />
      </aside>
    </div>
  );
}
