import { useMutation, useQueryClient } from "@tanstack/react-query";
import { recordSituationAttempt } from "@/features/situation-practice/api";

export function useRecordAttempt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: recordSituationAttempt,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["attempts"] });
    },
  });
}
