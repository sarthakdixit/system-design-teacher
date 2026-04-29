import { ReactNode } from "react";
import { useAuthStore } from "@/features/auth/store";
import { LoginButton } from "@/features/auth/components/LoginButton";

type Props = {
  children: ReactNode;
};

export function RequireAuth({ children }: Props) {
  const isAuthenticated = useAuthStore((s) => s.accessToken !== null);

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="mb-4 text-xl font-semibold text-slate-900">Sign in required</h2>
          <p className="mb-6 text-sm text-slate-600">
            You need to be signed in to access this page.
          </p>
          <LoginButton />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
