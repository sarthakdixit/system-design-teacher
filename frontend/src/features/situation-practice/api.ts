import { apiClient } from "@/shared/api/client";
import {
  AllRateLimitsResponseSchema,
  AttemptSchema,
  FetchSituationQuestionResponseSchema,
} from "@/features/situation-practice/schema";
import type {
  AllRateLimits,
  Attempt,
  FetchSituationQuestionResult,
} from "@/features/situation-practice/types";

export type FetchFilters = {
  category?: string;
  difficulty?: "junior" | "mid" | "senior";
};

export async function fetchSituationQuestion(
  filters: FetchFilters,
): Promise<FetchSituationQuestionResult> {
  const params: Record<string, string> = {};
  if (filters.category) params.category = filters.category;
  if (filters.difficulty) params.difficulty = filters.difficulty;
  const { data } = await apiClient.get("/api/v1/questions/situation", { params });
  return FetchSituationQuestionResponseSchema.parse(data);
}

export async function recordSituationAttempt(args: {
  questionId: string;
  userNotes: string | null;
}): Promise<Attempt> {
  const { data } = await apiClient.post("/api/v1/attempts/situation", {
    question_id: args.questionId,
    user_notes: args.userNotes,
  });
  return AttemptSchema.parse(data);
}

export async function fetchAllRateLimits(): Promise<AllRateLimits> {
  const { data } = await apiClient.get("/api/v1/rate-limits");
  return AllRateLimitsResponseSchema.parse(data);
}
