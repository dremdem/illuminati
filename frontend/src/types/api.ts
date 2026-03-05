export type AccountType = "ASSET" | "LIABILITY" | "REVENUE" | "EXPENSE";
export type EntryType = "DEBIT" | "CREDIT";

export interface AccountResponse {
  id: string;
  name: string;
  type: AccountType;
  balance: string;
}

export interface TransactionEntryResponse {
  id: string;
  accountId: string;
  type: EntryType;
  amount: string;
}

export interface TransactionResponse {
  id: string;
  description: string;
  timestamp: string;
  entries: TransactionEntryResponse[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number | null;
  offset: number;
}

export interface CreateAccountRequest {
  name: string;
  type: AccountType;
}

export interface TransactionEntryRequest {
  accountId: string;
  type: EntryType;
  amount: number;
}

export interface CreateTransactionRequest {
  description: string;
  date: string;
  entries: TransactionEntryRequest[];
}
