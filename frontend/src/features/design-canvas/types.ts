export type ComponentType =
  | "user"
  | "load_balancer"
  | "api_gateway"
  | "microservice"
  | "auth_service"
  | "cache"
  | "database"
  | "object_storage"
  | "search_index"
  | "cdn"
  | "queue"
  | "notification_service"
  | "analytics"
  | "rate_limiter";

export type Severity = "critical" | "important" | "suggestion";

export type FeedbackCategory =
  | "scalability"
  | "reliability"
  | "security"
  | "cost"
  | "data"
  | "consistency"
  | "observability"
  | "other";

export type EstimatedLevel = "junior" | "mid" | "senior";

export type Difficulty = "junior" | "mid" | "senior";

export type DesignQuestion = {
  id: string;
  type: "design_system";
  title: string;
  prompt: string;
  category: string;
  difficulty: Difficulty;
  tags: string[];
  isAiGenerated: boolean;
  createdAt: string;
};

export type ComponentNodeData = {
  componentType: ComponentType;
  label: string;
};

export type FeedbackItem = {
  severity: Severity;
  category: FeedbackCategory;
  title: string;
  description: string;
  affectedComponents: string[];
  suggestedChange: string;
};

export type DesignFeedback = {
  overallScore: number;
  strengths: string[];
  gaps: FeedbackItem[];
  missingComponents: string[];
  tradeoffQuestions: string[];
  estimatedLevel: EstimatedLevel;
  llmModel: string;
  llmTokensUsed: number;
};

export type RateLimitMeta = {
  userRemaining: number;
  userLimit: number;
  globalRemaining: number;
  globalLimit: number;
  resetInSeconds: number;
};

export type AttemptSummary = {
  id: string;
  userId: string;
  questionId: string;
  type: "situation" | "design_system";
  userNotes: string | null;
  createdAt: string;
};

export type SubmitDesignResponse = {
  attempt: AttemptSummary;
  feedback: DesignFeedback;
  cacheHit: boolean;
  rateLimit: RateLimitMeta;
};

export type SubmitDesignPayload = {
  questionId: string;
  diagram: {
    nodes: { id: string; type: ComponentType; label: string }[];
    edges: { id: string; sourceId: string; targetId: string; label: string | null }[];
  };
  userNotes: string | null;
};
