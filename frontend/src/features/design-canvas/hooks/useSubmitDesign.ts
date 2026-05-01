import { useMutation } from "@tanstack/react-query";
import { submitDesign } from "../api";
import type { SubmitDesignPayload, SubmitDesignResponse } from "../types";

export function useSubmitDesign(
  onSuccess?: (response: SubmitDesignResponse) => void,
  onError?: (error: unknown) => void,
) {
  return useMutation<SubmitDesignResponse, unknown, SubmitDesignPayload>({
    mutationFn: submitDesign,
    onSuccess,
    onError,
  });
}
