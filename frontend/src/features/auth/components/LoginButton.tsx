import { useAuth } from "@/features/auth/hooks/useAuth";

export function LoginButton() {
  const { login, isLoggingIn, loginError } = useAuth();

  return (
    <div>
      <button
        type="button"
        onClick={() => void login()}
        disabled={isLoggingIn}
        className="inline-flex items-center justify-center rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-400"
        aria-label="Sign in with Microsoft"
      >
        {isLoggingIn ? "Signing in…" : "Sign in with Microsoft"}
      </button>
      {loginError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {loginError.message}
        </p>
      )}
    </div>
  );
}
