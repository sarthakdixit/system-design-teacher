import { useMutation } from "@tanstack/react-query";
import { fetchSituationQuestion, type FetchFilters } from "@/features/situation-practice/api";

export function useSituationQuestion() {
  return useMutation({
    mutationFn: (filters: FetchFilters) => fetchSituationQuestion(filters),
  });
}
