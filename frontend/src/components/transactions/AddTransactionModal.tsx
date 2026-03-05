import { useState } from "react";
import Modal from "../Modal";
import { useCreateTransaction } from "../../hooks/useTransactions";
import type {
  AccountResponse,
  EntryType,
  TransactionEntryRequest,
} from "../../types/api";

interface EntryRow {
  accountId: string;
  type: EntryType;
  amount: string;
}

const emptyEntry = (): EntryRow => ({
  accountId: "",
  type: "DEBIT",
  amount: "",
});

interface AddTransactionModalProps {
  open: boolean;
  onClose: () => void;
  accounts: AccountResponse[];
}

export default function AddTransactionModal({
  open,
  onClose,
  accounts,
}: AddTransactionModalProps) {
  const [description, setDescription] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [entries, setEntries] = useState<EntryRow[]>([
    emptyEntry(),
    emptyEntry(),
  ]);
  const mutation = useCreateTransaction();

  function updateEntry(index: number, patch: Partial<EntryRow>) {
    setEntries((prev) =>
      prev.map((e, i) => (i === index ? { ...e, ...patch } : e))
    );
  }

  function removeEntry(index: number) {
    setEntries((prev) => prev.filter((_, i) => i !== index));
  }

  const totalDebits = entries
    .filter((e) => e.type === "DEBIT")
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);
  const totalCredits = entries
    .filter((e) => e.type === "CREDIT")
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);
  const balanced = Math.abs(totalDebits - totalCredits) < 0.001;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const apiEntries: TransactionEntryRequest[] = entries.map((row) => ({
      accountId: row.accountId,
      type: row.type,
      amount: parseFloat(row.amount),
    }));
    mutation.mutate(
      { description: description.trim(), date: `${date}T00:00:00`, entries: apiEntries },
      {
        onSuccess: () => {
          setDescription("");
          setDate(new Date().toISOString().slice(0, 10));
          setEntries([emptyEntry(), emptyEntry()]);
          onClose();
        },
      }
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Add Transaction">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Office supplies purchase"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Entries</span>
            <button
              type="button"
              onClick={() => setEntries((prev) => [...prev, emptyEntry()])}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              + Add entry
            </button>
          </div>
          <div className="space-y-2">
            {entries.map((entry, i) => (
              <div key={i} className="flex gap-2 items-center">
                <select
                  value={entry.accountId}
                  onChange={(e) =>
                    updateEntry(i, { accountId: e.target.value })
                  }
                  required
                  className="flex-1 border rounded px-2 py-1.5 text-sm"
                >
                  <option value="">Account…</option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
                <select
                  value={entry.type}
                  onChange={(e) =>
                    updateEntry(i, { type: e.target.value as EntryType })
                  }
                  className="border rounded px-2 py-1.5 text-sm w-24"
                >
                  <option value="DEBIT">Debit</option>
                  <option value="CREDIT">Credit</option>
                </select>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={entry.amount}
                  onChange={(e) => updateEntry(i, { amount: e.target.value })}
                  required
                  placeholder="0.00"
                  className="w-28 border rounded px-2 py-1.5 text-sm text-right font-mono"
                />
                {entries.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeEntry(i)}
                    className="text-red-400 hover:text-red-600 text-lg leading-none"
                  >
                    &times;
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div
          className={`text-sm font-mono px-3 py-2 rounded ${balanced ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
        >
          Debits: {totalDebits.toFixed(2)} | Credits: {totalCredits.toFixed(2)}{" "}
          {balanced ? "— Balanced" : "— Unbalanced"}
        </div>

        {mutation.isError && (
          <p className="text-sm text-red-600">
            {(mutation.error as Error).message}
          </p>
        )}

        <div className="flex justify-end space-x-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !balanced}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Creating…" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
