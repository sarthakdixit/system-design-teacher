import { useAuthStore } from "@/features/auth/store";
import { LoginButton } from "@/features/auth/components/LoginButton";
import { ProfileCard } from "@/features/auth/components/ProfileCard";

export function HomePage() {
  const isAuthenticated = useAuthStore((s) => s.accessToken !== null);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-4">
          <h1 className="text-xl font-semibold text-slate-900">System Design Teacher</h1>
          <p className="text-sm text-slate-600">Practice your system design interview skills.</p>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-12">
        {isAuthenticated ? (
          <ProfileCard />
        ) : (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
            <h2 className="text-2xl font-semibold text-slate-900">Welcome</h2>
            <p className="mx-auto mt-3 max-w-md text-sm text-slate-600">
              Sign in to start practicing system design interviews. In development this uses a mock
              user — no Microsoft account required.
            </p>
            <div className="mt-6 flex justify-center">
              <LoginButton />
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
