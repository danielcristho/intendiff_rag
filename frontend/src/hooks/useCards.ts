import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAnnotator } from "@/components/AnnotatorGate";
import { api } from "@/services/api";
import type { CardText } from "@/types/api";

const CARDS_KEY = ["cards"] as const;

export function useCards() {
  return useQuery({ queryKey: CARDS_KEY, queryFn: api.cards });
}

export function useSampleFiles(cardId: string) {
  return useQuery({ queryKey: ["sample-files", cardId], queryFn: () => api.sampleFiles(cardId) });
}

export function useSampleFile(cardId: string, path: string | undefined) {
  return useQuery({
    queryKey: ["sample-file", cardId, path],
    queryFn: () => api.sampleFile(cardId, path!),
    enabled: Boolean(path),
  });
}

export function useWriteCard() {
  const { annotator } = useAnnotator();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, text, submit }: { id: string; text: CardText; submit: boolean }) =>
      api.writeCard(annotator, id, text, submit),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CARDS_KEY }),
  });
}

export function useReviewCard() {
  const { annotator } = useAnnotator();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, approve, note }: { id: string; approve: boolean; note: string }) =>
      api.reviewCard(annotator, id, approve, note),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CARDS_KEY }),
  });
}
