import { AxiosError } from "axios";

export class ApiError extends Error {
  readonly status: number;
  readonly data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }

  isUnauthorized(): boolean {
    return this.status === 401;
  }

  isRateLimited(): boolean {
    return this.status === 429;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isServerError(): boolean {
    return this.status >= 500;
  }
}

export function normalizeError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  if (error instanceof AxiosError) {
    const status = error.response?.status ?? 0;
    const data = error.response?.data;
    const detail =
      (typeof data === "object" && data !== null && "detail" in data && typeof data.detail === "string"
        ? data.detail
        : null) ?? error.message;
    return new ApiError(detail, status, data);
  }
  if (error instanceof Error) {
    return new ApiError(error.message, 0, null);
  }
  return new ApiError("Unknown error", 0, error);
}
