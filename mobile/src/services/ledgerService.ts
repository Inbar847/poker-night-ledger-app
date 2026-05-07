/**
 * Ledger service — buy-ins, expenses, and final stacks.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  BuyIn,
  CreateBuyInRequest,
  CreateExpenseRequest,
  Expense,
  FinalStack,
  UpsertFinalStackRequest,
} from "@/types/game";

// ---------------------------------------------------------------------------
// Buy-ins
// ---------------------------------------------------------------------------

export async function listBuyIns(gameId: string): Promise<BuyIn[]> {
  return apiClient.get<BuyIn[]>(`/games/${gameId}/buy-ins`);
}

export async function createBuyIn(
  gameId: string,
  data: CreateBuyInRequest,
): Promise<BuyIn> {
  return apiClient.post<BuyIn>(`/games/${gameId}/buy-ins`, data);
}

export async function deleteBuyIn(
  gameId: string,
  buyInId: string,
): Promise<void> {
  return apiClient.delete(`/games/${gameId}/buy-ins/${buyInId}`);
}

// ---------------------------------------------------------------------------
// Expenses
// ---------------------------------------------------------------------------

export async function listExpenses(gameId: string): Promise<Expense[]> {
  return apiClient.get<Expense[]>(`/games/${gameId}/expenses`);
}

export async function createExpense(
  gameId: string,
  data: CreateExpenseRequest,
): Promise<Expense> {
  return apiClient.post<Expense>(`/games/${gameId}/expenses`, data);
}

export async function updateExpense(
  gameId: string,
  expenseId: string,
  data: Partial<CreateExpenseRequest>,
): Promise<Expense> {
  return apiClient.patch<Expense>(
    `/games/${gameId}/expenses/${expenseId}`,
    data,
  );
}

export async function deleteExpense(
  gameId: string,
  expenseId: string,
): Promise<void> {
  return apiClient.delete(`/games/${gameId}/expenses/${expenseId}`);
}

// ---------------------------------------------------------------------------
// Final stacks
// ---------------------------------------------------------------------------

export async function listFinalStacks(gameId: string): Promise<FinalStack[]> {
  return apiClient.get<FinalStack[]>(`/games/${gameId}/final-stacks`);
}

export async function upsertFinalStack(
  gameId: string,
  participantId: string,
  data: UpsertFinalStackRequest,
): Promise<FinalStack> {
  return apiClient.put<FinalStack>(
    `/games/${gameId}/final-stacks/${participantId}`,
    data,
  );
}
