import { z } from "zod";

const DifficultySchema = z.enum(["junior", "mid", "senior"]);
const QuestionTypeSchema = z.enum(["situation", "design_system"]);
const AttemptTypeSchema = z.enum(["situation", "design_system"]);

export const SituationQuestionSchema = z
  .object({
    id: z.string(),
    type: QuestionTypeSchema,
    title: z.string(),
    prompt: z.string(),
    category: z.string(),
    difficulty: DifficultySchema,
    tags: z.array(z.string()),
    is_ai_generated: z.boolean(),
    created_at: z.string(),
    reference_answer: z.string().nullable(),
  })
  .transform((q) => ({
    id: q.id,
    type: q.type,
    title: q.title,
    prompt: q.prompt,
    category: q.category,
    difficulty: q.difficulty,
    tags: q.tags,
    isAiGenerated: q.is_ai_generated,
    createdAt: q.created_at,
    referenceAnswer: q.reference_answer,
  }));

export const RateLimitMetaSchema = z
  .object({
    user_remaining: z.number().int().nonnegative(),
    user_limit: z.number().int().positive(),
    global_remaining: z.number().int().nonnegative(),
    global_limit: z.number().int().positive(),
    reset_in_seconds: z.number().int().nonnegative(),
  })
  .transform((m) => ({
    userRemaining: m.user_remaining,
    userLimit: m.user_limit,
    globalRemaining: m.global_remaining,
    globalLimit: m.global_limit,
    resetInSeconds: m.reset_in_seconds,
  }));

export const FetchSituationQuestionResponseSchema = z
  .object({
    question: SituationQuestionSchema,
    rate_limit: RateLimitMetaSchema,
  })
  .transform((r) => ({
    question: r.question,
    rateLimit: r.rate_limit,
  }));

export const AttemptSchema = z
  .object({
    id: z.string(),
    user_id: z.string(),
    question_id: z.string(),
    type: AttemptTypeSchema,
    user_notes: z.string().nullable(),
    created_at: z.string(),
  })
  .transform((a) => ({
    id: a.id,
    userId: a.user_id,
    questionId: a.question_id,
    type: a.type,
    userNotes: a.user_notes,
    createdAt: a.created_at,
  }));

export const RateLimitStatusSchema = z
  .object({
    user_current: z.number().int().nonnegative(),
    user_limit: z.number().int().positive(),
    user_remaining: z.number().int().nonnegative(),
    global_current: z.number().int().nonnegative(),
    global_limit: z.number().int().positive(),
    global_remaining: z.number().int().nonnegative(),
    reset_in_seconds: z.number().int().nonnegative(),
  })
  .transform((s) => ({
    userCurrent: s.user_current,
    userLimit: s.user_limit,
    userRemaining: s.user_remaining,
    globalCurrent: s.global_current,
    globalLimit: s.global_limit,
    globalRemaining: s.global_remaining,
    resetInSeconds: s.reset_in_seconds,
  }));

export const AllRateLimitsResponseSchema = z
  .object({
    situation_fetch: RateLimitStatusSchema,
    design_submission: RateLimitStatusSchema,
  })
  .transform((r) => ({
    situationFetch: r.situation_fetch,
    designSubmission: r.design_submission,
  }));
