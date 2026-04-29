import { useQuery } from "@tanstack/react-query";
import { fetchCurrentUser } from "@/features/auth/api";
import { useAuthStore } from "@/features/auth/store";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function ProfileCard() {
  const cachedUser = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const { logout } = useAuth();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const user = await fetchCurrentUser();
      setUser(user);
      return user;
    },
    initialData: cachedUser ?? undefined,
  });

  if (isLoading && !data) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="h-4 w-32 animate-pulse rounded bg-slate-200" />
        <div className="mt-3 h-3 w-48 animate-pulse rounded bg-slate-100" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6" role="alert">
        <p className="text-sm font-medium text-red-800">Could not load your profile.</p>
        <p className="mt-1 text-sm text-red-700">{error.message}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Signed in</h2>
      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-500">Name</dt>
          <dd className="font-medium text-slate-900">{data.displayName}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Email</dt>
          <dd className="font-medium text-slate-900">{data.email}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">User ID</dt>
          <dd className="font-mono text-xs text-slate-700">{data.id}</dd>
        </div>
      </dl>
      <button
        type="button"
        onClick={logout}
        className="mt-6 inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
      >
        Sign out
      </button>
    </div>
  );
}
