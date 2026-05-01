import { create } from "zustand";
import type { DesignFeedback, DesignQuestion, FeedbackItem, Severity } from "./types";

type SubmissionStatus = "idle" | "submitting" | "succeeded" | "failed";

type CanvasStore = {
  question: DesignQuestion | null;
  feedback: DesignFeedback | null;
  selectedFeedbackItem: FeedbackItem | null;
  cacheHit: boolean;
  submissionStatus: SubmissionStatus;
  submissionError: string | null;
  userNotes: string;

  setQuestion: (question: DesignQuestion | null) => void;
  setFeedback: (feedback: DesignFeedback | null, cacheHit: boolean) => void;
  selectFeedbackItem: (item: FeedbackItem | null) => void;
  setSubmissionStatus: (status: SubmissionStatus, error?: string | null) => void;
  setUserNotes: (notes: string) => void;
  resetSession: () => void;
};

export const useCanvasStore = create<CanvasStore>((set) => ({
  question: null,
  feedback: null,
  selectedFeedbackItem: null,
  cacheHit: false,
  submissionStatus: "idle",
  submissionError: null,
  userNotes: "",

  setQuestion: (question) =>
    set({
      question,
      feedback: null,
      selectedFeedbackItem: null,
      cacheHit: false,
      submissionStatus: "idle",
      submissionError: null,
    }),

  setFeedback: (feedback, cacheHit) =>
    set({
      feedback,
      cacheHit,
      selectedFeedbackItem: null,
      submissionStatus: feedback ? "succeeded" : "idle",
      submissionError: null,
    }),

  selectFeedbackItem: (item) => set({ selectedFeedbackItem: item }),

  setSubmissionStatus: (status, error = null) =>
    set({ submissionStatus: status, submissionError: error }),

  setUserNotes: (notes) => set({ userNotes: notes }),

  resetSession: () =>
    set({
      feedback: null,
      selectedFeedbackItem: null,
      cacheHit: false,
      submissionStatus: "idle",
      submissionError: null,
      userNotes: "",
    }),
}));

export const selectAffectedComponentIds = (state: CanvasStore): readonly string[] =>
  state.selectedFeedbackItem?.affectedComponents ?? EMPTY_ARRAY;

export const selectHighlightSeverity = (state: CanvasStore): Severity | null =>
  state.selectedFeedbackItem?.severity ?? null;

const EMPTY_ARRAY: readonly string[] = Object.freeze([]);
