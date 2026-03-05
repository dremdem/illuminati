import type {
  AccountResponse,
  TransactionResponse,
  PaginatedResponse,
  CreateAccountRequest,
  CreateTransactionRequest,
} from "../types/api";

const BASE = "/api";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function fetchAccounts(
  limit: number,
  offset: number
): Promise<PaginatedResponse<AccountResponse>> {
  return request(`${BASE}/accounts?limit=${limit}&offset=${offset}`);
}

export function fetchAllAccounts(): Promise<
  PaginatedResponse<AccountResponse>
> {
  return request(`${BASE}/accounts`);
}

export function createAccount(
  data: CreateAccountRequest
): Promise<AccountResponse> {
  return request(`${BASE}/accounts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function fetchTransactions(
  limit: number,
  offset: number,
  accountId?: string,
  startDate?: string,
  endDate?: string
): Promise<PaginatedResponse<TransactionResponse>> {
  if (accountId) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    return request(
      `${BASE}/accounts/${accountId}/transactions?${params.toString()}`
    );
  } else {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    return request(`${BASE}/transactions?${params.toString()}`);
  }
}

export function createTransaction(
  data: CreateTransactionRequest
): Promise<TransactionResponse> {
  return request(`${BASE}/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
