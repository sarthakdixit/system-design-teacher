export type Difficulty = "junior" | "mid" | "senior";
export type AttemptType = "situation" | "design_system";

export type SituationQuestion = {
  id: string;
  type: "situation" | "design_system";
  title: string;
  prompt: string;
  category: string;
  difficulty: Difficulty;
  tags: string[];
  isAiGenerated: boolean;
  createdAt: string;
  referenceAnswer: string | null;
};

export type RateLimitMeta = {
  userRemaining: number;
  userLimit: number;
  globalRemaining: number;
  globalLimit: number;
  resetInSeconds: number;
};

export type FetchSituationQuestionResult = {
  question: SituationQuestion;
  rateLimit: RateLimitMeta;
};

export type Attempt = {
  id: string;
  userId: string;
  questionId: string;
  type: AttemptType;
  userNotes: string | null;
  createdAt: string;
};

export type RateLimitStatus = {
  userCurrent: number;
  userLimit: number;
  userRemaining: number;
  globalCurrent: number;
  globalLimit: number;
  globalRemaining: number;
  resetInSeconds: number;
};

export type AllRateLimits = {
  situationFetch: RateLimitStatus;
  designSubmission: RateLimitStatus;
};
