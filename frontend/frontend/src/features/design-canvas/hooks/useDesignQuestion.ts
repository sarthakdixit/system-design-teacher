import { useMutation } from "@tanstack/react-query";
import { fetchRandomDesignQuestion } from "../api";
import type { DesignQuestion } from "../types";

type Params = {
  category?: string;
  difficulty?: string;
};

export function useDesignQuestion(onSuccess?: (q: DesignQuestion) => void) {
  return useMutation({
    mutationFn: (params: Params) => fetchRandomDesignQuestion(params),
    onSuccess,
  });
}
