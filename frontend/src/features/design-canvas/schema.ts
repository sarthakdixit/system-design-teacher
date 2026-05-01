import { z } from "zod";

const ComponentTypeSchema = z.enum([
  "user",
  "load_balancer",
  "api_gateway",
  "microservice",
  "auth_service",
  "cache",
  "database",
  "object_storage",
  "search_index",
  "cdn",
  "queue",
  "notification_service",
  "analytics",
  "rate_limiter",
]);

const SeveritySchema = z.enum(["critical", "important", "suggestion"]);

const FeedbackCategorySchema = z.enum([
  "scalability",
  "reliability",
  "security",
  "cost",
  "data",
  "consistency",
  "observability",
  "other",
]);

const EstimatedLevelSchema = z.enum(["junior", "mid", "senior"]);

const DifficultySchema = z.enum(["junior", "mid", "senior"]);

export const DesignQuestionSchema = z
  .object({
    id: z.string(),
    type: z.literal("design_system"),
    title: z.string(),
    prompt: z.string(),
    category: z.string(),
    difficulty: DifficultySchema,
    tags: z.array(z.string()),
    is_ai_generated: z.boolean(),
    created_at: z.string(),
  })
  .transform((raw) => ({
    id: raw.id,
    type: raw.type,
    title: raw.title,
    prompt: raw.prompt,
    category: raw.category,
    difficulty: raw.difficulty,
    tags: raw.tags,
    isAiGenerated: raw.is_ai_generated,
    createdAt: raw.created_at,
  }));

const FeedbackItemSchema = z
  .object({
    severity: SeveritySchema,
    category: FeedbackCategorySchema,
    title: z.string(),
    description: z.string(),
    affected_components: z.array(z.string()),
    suggested_change: z.string(),
  })
  .transform((raw) => ({
    severity: raw.severity,
    category: raw.category,
    title: raw.title,
    description: raw.description,
    affectedComponents: raw.affected_components,
    suggestedChange: raw.suggested_change,
  }));

const DesignFeedbackSchema = z
  .object({
    overall_score: z.number().int().min(1).max(10),
    strengths: z.array(z.string()),
    gaps: z.array(FeedbackItemSchema),
    missing_components: z.array(z.string()),
    tradeoff_questions: z.array(z.string()),
    estimated_level: EstimatedLevelSchema,
    llm_model: z.string(),
    llm_tokens_used: z.number().int().nonnegative(),
  })
  .transform((raw) => ({
    overallScore: raw.overall_score,
    strengths: raw.strengths,
    gaps: raw.gaps,
    missingComponents: raw.missing_components,
    tradeoffQuestions: raw.tradeoff_questions,
    estimatedLevel: raw.estimated_level,
    llmModel: raw.llm_model,
    llmTokensUsed: raw.llm_tokens_used,
  }));

const RateLimitMetaSchema = z
  .object({
    user_remaining: z.number().int().nonnegative(),
    user_limit: z.number().int().positive(),
    global_remaining: z.number().int().nonnegative(),
    global_limit: z.number().int().positive(),
    reset_in_seconds: z.number().int().nonnegative(),
  })
  .transform((raw) => ({
    userRemaining: raw.user_remaining,
    userLimit: raw.user_limit,
    globalRemaining: raw.global_remaining,
    globalLimit: raw.global_limit,
    resetInSeconds: raw.reset_in_seconds,
  }));

const AttemptSummarySchema = z
  .object({
    id: z.string(),
    user_id: z.string(),
    question_id: z.string(),
    type: z.enum(["situation", "design_system"]),
    user_notes: z.string().nullable(),
    created_at: z.string(),
  })
  .transform((raw) => ({
    id: raw.id,
    userId: raw.user_id,
    questionId: raw.question_id,
    type: raw.type,
    userNotes: raw.user_notes,
    createdAt: raw.created_at,
  }));

export const SubmitDesignResponseSchema = z
  .object({
    attempt: AttemptSummarySchema,
    feedback: DesignFeedbackSchema,
    cache_hit: z.boolean(),
    rate_limit: RateLimitMetaSchema,
  })
  .transform((raw) => ({
    attempt: raw.attempt,
    feedback: raw.feedback,
    cacheHit: raw.cache_hit,
    rateLimit: raw.rate_limit,
  }));

export { ComponentTypeSchema };
