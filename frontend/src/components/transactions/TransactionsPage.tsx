import { useState, useMemo } from "react";
import { useTransactions } from "../../hooks/useTransactions";
import { useAllAccounts } from "../../hooks/useAccounts";
import TransactionFilters from "./TransactionFilters";
import TransactionJournal from "./TransactionJournal";
import AddTransactionModal from "./AddTransactionModal";
import Pagination from "../Pagination";
import type { AccountResponse } from "../../types/api";

const LIMIT = 10;

export default function TransactionsPage() {
  const [offset, setOffset] = useState(0);
  const [accountId, setAccountId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, isError } = useTransactions(
    LIMIT,
    offset,
    accountId || undefined,
    startDate || undefined,
    endDate || undefined
  );
  const allAccounts = useAllAccounts();

  const accountMap = useMemo(() => {
    const map = new Map<string, AccountResponse>();
    if (allAccounts.data) {
      for (const a of allAccounts.data.items) {
        map.set(a.id, a);
      }
    }
    return map;
  }, [allAccounts.data]);

  function handleFilterChange(setter: (v: string) => void) {
    return (value: string) => {
      setter(value);
      setOffset(0);
    };
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">Transactions</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Add Transaction
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <TransactionFilters
          accounts={allAccounts.data?.items ?? []}
          accountId={accountId}
          startDate={startDate}
          endDate={endDate}
          onAccountChange={handleFilterChange(setAccountId)}
          onStartDateChange={handleFilterChange(setStartDate)}
          onEndDateChange={handleFilterChange(setEndDate)}
        />
      </div>

      {isLoading && <p className="text-gray-500">Loading transactions…</p>}
      {isError && (
        <p className="text-red-600">Failed to load transactions.</p>
      )}
      {data && (
        <div className="bg-white rounded-lg shadow p-4">
          <TransactionJournal
            transactions={data.items}
            accountMap={accountMap}
          />
          <Pagination
            total={data.total}
            limit={LIMIT}
            offset={offset}
            onOffsetChange={setOffset}
          />
        </div>
      )}

      <AddTransactionModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        accounts={allAccounts.data?.items ?? []}
      />
    </div>
  );
}
