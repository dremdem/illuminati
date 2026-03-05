import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAccounts, fetchAllAccounts, createAccount } from "../api/client";
import type { CreateAccountRequest } from "../types/api";

export function useAccounts(limit: number, offset: number) {
  return useQuery({
    queryKey: ["accounts", limit, offset],
    queryFn: () => fetchAccounts(limit, offset),
  });
}

export function useAllAccounts() {
  return useQuery({
    queryKey: ["accounts", "all"],
    queryFn: () => fetchAllAccounts(),
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateAccountRequest) => createAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}
