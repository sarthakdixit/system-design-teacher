import clsx from "clsx";
import type { RateLimitMeta } from "@/features/situation-practice/types";
import { formatResetIn } from "@/shared/hooks/useRateLimitFromError";

type Props = {
  rateLimit: RateLimitMeta | null;
  className?: string;
};

export function RateLimitBanner({ rateLimit, className }: Props) {
  if (rateLimit === null) return null;

  const { userRemaining, userLimit, globalRemaining, globalLimit, resetInSeconds } = rateLimit;

  const userExhausted = userRemaining === 0;
  const globalExhausted = globalRemaining === 0;
  const tone = userExhausted || globalExhausted ? "warn" : "info";

  return (
    <div
      className={clsx(
        "rounded-md border px-4 py-2 text-sm",
        tone === "warn"
          ? "border-amber-200 bg-amber-50 text-amber-800"
          : "border-slate-200 bg-slate-50 text-slate-700",
        className,
      )}
      role="status"
    >
      <p>
        <strong>You:</strong> {userRemaining} of {userLimit} fetches remaining today
        {globalRemaining < globalLimit / 4 && (
          <>
            {" · "}
            <strong>Global:</strong> {globalRemaining} of {globalLimit} remaining
          </>
        )}
        {" · resets in "}
        <span>{formatResetIn(resetInSeconds)}</span>
      </p>
    </div>
  );
}
