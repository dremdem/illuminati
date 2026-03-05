import type { AccountResponse } from "../../types/api";

interface TransactionFiltersProps {
  accounts: AccountResponse[];
  accountId: string;
  startDate: string;
  endDate: string;
  onAccountChange: (id: string) => void;
  onStartDateChange: (d: string) => void;
  onEndDateChange: (d: string) => void;
}

export default function TransactionFilters({
  accounts,
  accountId,
  startDate,
  endDate,
  onAccountChange,
  onStartDateChange,
  onEndDateChange,
}: TransactionFiltersProps) {
  return (
    <div className="flex flex-wrap gap-4 items-end">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Account
        </label>
        <select
          value={accountId}
          onChange={(e) => onAccountChange(e.target.value)}
          className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All accounts</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          From
        </label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          To
        </label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );
}
