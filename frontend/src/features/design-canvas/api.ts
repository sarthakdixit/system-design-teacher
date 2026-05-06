import { apiClient } from "@/shared/api/client";
import {
  DesignQuestionSchema,
  SubmitDesignResponseSchema,
} from "./schema";
import type {
  DesignQuestion,
  SubmitDesignPayload,
  SubmitDesignResponse,
} from "./types";

export async function fetchRandomDesignQuestion(params: {
  category?: string;
  difficulty?: string;
}): Promise<DesignQuestion> {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.difficulty) search.set("difficulty", params.difficulty);
  const queryString = search.toString();
  const url = `/api/v1/questions/design${queryString ? `?${queryString}` : ""}`;

  const { data } = await apiClient.get(url);
  return DesignQuestionSchema.parse(data);
}

export async function fetchDesignQuestionById(questionId: string): Promise<DesignQuestion> {
  const { data } = await apiClient.get(`/api/v1/questions/design/${questionId}`);
  return DesignQuestionSchema.parse(data);
}

export async function submitDesign(payload: SubmitDesignPayload): Promise<SubmitDesignResponse> {
  const body = {
    question_id: payload.questionId,
    diagram: {
      nodes: payload.diagram.nodes,
      edges: payload.diagram.edges.map((e) => ({
        id: e.id,
        source_id: e.sourceId,
        target_id: e.targetId,
        label: e.label,
      })),
    },
    user_notes: payload.userNotes,
  };

  const { data } = await apiClient.post("/api/v1/attempts/design", body);
  return SubmitDesignResponseSchema.parse(data);
}
