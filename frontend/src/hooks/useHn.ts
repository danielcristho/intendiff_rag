import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { HnVerifyRequest } from "@/types/api";

const QUEUE_KEY = ["hn-queue"] as const;

export function useHnQueue() {
  return useQuery({ queryKey: QUEUE_KEY, queryFn: api.hnQueue });
}

export function useHnCandidate(id: string | undefined) {
  return useQuery({
    queryKey: ["hn-candidate", id],
    queryFn: () => api.hnCandidate(id!),
    enabled: Boolean(id),
  });
}

export function useVerifyHn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: HnVerifyRequest }) => api.verifyHn(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUEUE_KEY }),
  });
}
