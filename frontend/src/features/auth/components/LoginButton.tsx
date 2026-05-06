import { useAuth } from "@/features/auth/hooks/useAuth";

export function LoginButton() {
  const { login, isLoggingIn, loginError } = useAuth();

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={() => void login()}
        disabled={isLoggingIn}
        className="group flex w-full items-center justify-center gap-3 rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-[#1d3557] shadow-sm transition hover:border-[#1d3557] hover:shadow-md focus:outline-none focus:ring-2 focus:ring-[#1d3557] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="Sign in with Microsoft"
      >
        <MicrosoftLogo />
        <span>{isLoggingIn ? "Signing in…" : "Sign in with Microsoft"}</span>
      </button>

      {loginError && (
        <div
          role="alert"
          className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {loginError.message}
        </div>
      )}
    </div>
  );
}

function MicrosoftLogo() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 23 23"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="1" y="1" width="10" height="10" fill="#f25022" />
      <rect x="12" y="1" width="10" height="10" fill="#7fba00" />
      <rect x="1" y="12" width="10" height="10" fill="#00a4ef" />
      <rect x="12" y="12" width="10" height="10" fill="#ffb900" />
    </svg>
  );
}
