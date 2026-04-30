import { useQuery } from "@tanstack/react-query";
import { fetchAllRateLimits } from "@/features/situation-practice/api";

export function useRateLimits() {
  return useQuery({
    queryKey: ["rate-limits"],
    queryFn: fetchAllRateLimits,
    staleTime: 30_000,
  });
}
