import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAnnotator } from "@/components/AnnotatorGate";
import { api } from "@/services/api";
import type { Decision } from "@/types/api";

// decisionsKey scopes the cache to one annotator so pages cannot cross-read.
const decisionsKey = (annotator: string) => ["decisions", annotator] as const;

// usePairs loads every update pair and the file it was read from.
export function usePairs() {
  return useQuery({ queryKey: ["pairs"], queryFn: api.pairs });
}

// useDecisions loads the signed-in annotator's own decisions.
export function useDecisions() {
  const { annotator } = useAnnotator();
  return useQuery({
    queryKey: decisionsKey(annotator),
    queryFn: () => api.decisions(annotator),
  });
}

// useAnnotators loads each annotator's decision count, without their labels.
export function useAnnotators() {
  return useQuery({ queryKey: ["annotators"], queryFn: api.annotators });
}

// useResults loads every recorded model run for one pair, for EA4 error analysis.
export function useResults(pairId: string | undefined) {
  return useQuery({
    queryKey: ["results", pairId],
    queryFn: () => api.results(pairId!),
    enabled: Boolean(pairId),
  });
}

// useSaveDecision patches one pair's decision and refreshes the cached list.
export function useSaveDecision() {
  const { annotator } = useAnnotator();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Decision }) =>
      api.saveDecision(annotator, id, patch),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: decisionsKey(annotator) }),
  });
}
