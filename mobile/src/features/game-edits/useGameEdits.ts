/**
 * TanStack Query hooks for retroactive game editing.
 *
 * Every mutation invalidates settlement, buy-ins, final-stacks, and game-edits
 * queries so the UI refreshes after each edit.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/queryKeys";
import * as gameEditService from "@/features/game-edits/gameEditService";
import type {
  ClosedGameBuyInCreate,
  ClosedGameBuyInUpdate,
  ClosedGameFinalStackUpdate,
} from "@/types/game";

export function useGameEdits(gameId: string) {
  return useQuery({
    queryKey: queryKeys.gameEdits(gameId),
    queryFn: () => gameEditService.listEdits(gameId),
    enabled: !!gameId,
  });
}

function useInvalidateAfterEdit(gameId: string) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.settlement(gameId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.buyIns(gameId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.finalStacks(gameId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.gameEdits(gameId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.game(gameId) });
  };
}

export function useCreateClosedBuyIn(gameId: string) {
  const invalidate = useInvalidateAfterEdit(gameId);
  return useMutation({
    mutationFn: (data: ClosedGameBuyInCreate) =>
      gameEditService.createBuyIn(gameId, data),
    onSuccess: invalidate,
  });
}

export function useUpdateClosedBuyIn(gameId: string) {
  const invalidate = useInvalidateAfterEdit(gameId);
  return useMutation({
    mutationFn: ({ buyInId, data }: { buyInId: string; data: ClosedGameBuyInUpdate }) =>
      gameEditService.updateBuyIn(gameId, buyInId, data),
    onSuccess: invalidate,
  });
}

export function useDeleteClosedBuyIn(gameId: string) {
  const invalidate = useInvalidateAfterEdit(gameId);
  return useMutation({
    mutationFn: (buyInId: string) =>
      gameEditService.deleteBuyIn(gameId, buyInId),
    onSuccess: invalidate,
  });
}

export function useUpdateClosedFinalStack(gameId: string) {
  const invalidate = useInvalidateAfterEdit(gameId);
  return useMutation({
    mutationFn: ({ participantId, data }: { participantId: string; data: ClosedGameFinalStackUpdate }) =>
      gameEditService.updateFinalStack(gameId, participantId, data),
    onSuccess: invalidate,
  });
}
