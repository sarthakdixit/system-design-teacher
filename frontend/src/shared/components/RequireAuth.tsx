import { ReactNode } from "react";
import { env } from "@/config/env";
import { useAuthStore } from "@/features/auth/store";
import { LoginButton } from "@/features/auth/components/LoginButton";

type Props = {
  children: ReactNode;
};

export function RequireAuth({ children }: Props) {
  const isAuthenticated = useAuthStore((s) => s.accessToken !== null);

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return <>{children}</>;
}

function LoginScreen() {
  const isMockMode = env.VITE_AUTH_MODE === "mock";

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-5">
      <aside className="relative flex flex-col justify-between overflow-hidden bg-[#1d3557] px-8 py-10 text-white lg:col-span-3 lg:px-16 lg:py-16">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: "radial-gradient(#f1faee 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />

        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="h-8 w-1 rounded-sm bg-[#e63946]" aria-hidden="true" />
            <span className="font-mono text-xs uppercase tracking-widest text-[#a8dadc]">
              system design teacher
            </span>
          </div>
        </div>

        <div className="relative max-w-xl">
          <h1 className="text-3xl font-bold leading-tight tracking-tight md:text-4xl lg:text-5xl">
            Practice for system-design interviews
            <span className="text-[#e63946]">.</span>
          </h1>
          <p className="mt-4 text-base leading-relaxed text-[#a8dadc] md:text-lg">
            Drag, drop, label, submit. Get senior-grade AI feedback on your
            architecture in seconds.
          </p>

          <ul className="mt-10 space-y-5">
            <Benefit
              num="01"
              title="Real interview questions"
              body="Fifty curated prompts with reference answers. Filter by category and difficulty."
            />
            <Benefit
              num="02"
              title="Drag-and-drop architecture canvas"
              body="Fifteen component types. Edge labels. Live highlighting on submitted feedback."
            />
            <Benefit
              num="03"
              title="Structured AI feedback"
              body="Severity-graded gaps, trade-off questions, and an estimated level — junior, mid, or senior."
            />
          </ul>
        </div>

        <div className="relative flex items-center gap-2 font-mono text-[11px] text-[#a8dadc]">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#2a9d8f]" />
          <span>open source</span>
          <span className="text-white/30">·</span>
          <a
            href="https://github.com/sarthakdixit/system-design-teacher"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            github.com/sarthakdixit/system-design-teacher
          </a>
        </div>
      </aside>

      <main className="flex items-center justify-center bg-[#f1faee] px-6 py-12 lg:col-span-2 lg:px-12">
        <div className="w-full max-w-sm">
          <div className="mb-10">
            <p className="font-mono text-xs uppercase tracking-widest text-[#e63946]">
              Welcome
            </p>
            <h2 className="mt-2 text-3xl font-bold text-[#1d3557]">
              Sign in to continue
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Microsoft account required. We never see your password.
            </p>
          </div>

          <LoginButton />

          {isMockMode && (
            <div className="mt-6 rounded-md border border-dashed border-[#1d3557]/30 bg-white/50 px-4 py-3">
              <p className="font-mono text-[10px] uppercase tracking-widest text-[#e63946]">
                Local dev mode
              </p>
              <p className="mt-1 text-xs text-slate-600">
                Auth is mocked. The button above signs in as a fake user without
                contacting Microsoft.
              </p>
            </div>
          )}

          <div className="mt-12 border-t border-slate-200 pt-6">
            <p className="text-xs text-slate-500">
              By signing in you agree to be a good test subject. No data is
              shared with third parties beyond what is needed to provide AI
              feedback.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

type BenefitProps = {
  num: string;
  title: string;
  body: string;
};

function Benefit({ num, title, body }: BenefitProps) {
  return (
    <li className="flex gap-4">
      <span className="font-mono text-sm font-bold text-[#e63946]">{num}</span>
      <div>
        <p className="text-base font-semibold text-white">{title}</p>
        <p className="mt-1 text-sm leading-relaxed text-[#a8dadc]">{body}</p>
      </div>
    </li>
  );
}
