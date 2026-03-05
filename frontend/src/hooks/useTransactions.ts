import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTransactions, createTransaction } from "../api/client";
import type { CreateTransactionRequest } from "../types/api";

export function useTransactions(
  limit: number,
  offset: number,
  accountId?: string,
  startDate?: string,
  endDate?: string
) {
  return useQuery({
    queryKey: ["transactions", limit, offset, accountId, startDate, endDate],
    queryFn: () =>
      fetchTransactions(limit, offset, accountId, startDate, endDate),
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateTransactionRequest) => createTransaction(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}
