import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAnnotator } from "@/components/AnnotatorGate";
import { api } from "@/services/api";
import type { Decision } from "@/types/api";

// Scoped per annotator so one page cannot read another's cache.
const decisionsKey = (annotator: string) => ["decisions", annotator] as const;

export function usePairs() {
  return useQuery({ queryKey: ["pairs"], queryFn: api.pairs });
}

export function useDecisions() {
  const { annotator } = useAnnotator();
  return useQuery({
    queryKey: decisionsKey(annotator),
    queryFn: () => api.decisions(annotator),
  });
}

export function useAnnotators() {
  return useQuery({ queryKey: ["annotators"], queryFn: api.annotators });
}

// Feeds the EA4 error taxonomy.
export function useResults(pairId: string | undefined) {
  return useQuery({
    queryKey: ["results", pairId],
    queryFn: () => api.results(pairId!),
    enabled: Boolean(pairId),
  });
}

export function useSaveDecision() {
  const { annotator } = useAnnotator();
  const queryClient = useQueryClient();
  return useMutation({
    // Blur and verdict clicks can save adjacent fields; keep their writes ordered.
    scope: { id: `annotation-${annotator}` },
    mutationFn: ({ id, patch }: { id: string; patch: Decision }) =>
      api.saveDecision(annotator, id, patch),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: decisionsKey(annotator) }),
  });
}
