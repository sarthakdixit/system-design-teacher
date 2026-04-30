import { ApiError } from "@/shared/api/errors";

type RateLimitDetail = {
  detail: string;
  limit: number;
  resetInSeconds: number;
};

export function rateLimitDetailFromError(error: unknown): RateLimitDetail | null {
  if (!(error instanceof ApiError) || !error.isRateLimited()) {
    return null;
  }
  const data = error.data;
  if (typeof data !== "object" || data === null) {
    return null;
  }
  const record = data as Record<string, unknown>;
  const limit = typeof record.limit === "number" ? record.limit : null;
  const resetInSeconds =
    typeof record.reset_in_seconds === "number" ? record.reset_in_seconds : null;
  if (limit === null || resetInSeconds === null) {
    return null;
  }
  return {
    detail: error.message,
    limit,
    resetInSeconds,
  };
}

export function formatResetIn(seconds: number): string {
  if (seconds <= 0) return "now";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m`;
  }
  return `${seconds}s`;
}
