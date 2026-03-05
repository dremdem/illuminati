import { useState } from "react";
import type { TransactionResponse, AccountResponse } from "../../types/api";

interface TransactionJournalProps {
  transactions: TransactionResponse[];
  accountMap: Map<string, AccountResponse>;
  dateSortOrder: "asc" | "desc";
  onDateSortToggle: () => void;
}

export default function TransactionJournal({
  transactions,
  accountMap,
  dateSortOrder,
  onDateSortToggle,
}: TransactionJournalProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-gray-500">
          <th className="py-2 w-8"></th>
          <th
            className="py-2 font-medium cursor-pointer select-none hover:text-gray-700"
            onClick={onDateSortToggle}
          >
            Date {dateSortOrder === "asc" ? "▲" : "▼"}
          </th>
          <th className="py-2 font-medium">Description</th>
          <th className="py-2 font-medium text-right">Entries</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map((tx) => {
          const isOpen = expanded.has(tx.id);
          return (
            <TransactionRow
              key={tx.id}
              tx={tx}
              isOpen={isOpen}
              onToggle={() => toggle(tx.id)}
              accountMap={accountMap}
            />
          );
        })}
      </tbody>
    </table>
  );
}

function TransactionRow({
  tx,
  isOpen,
  onToggle,
  accountMap,
}: {
  tx: TransactionResponse;
  isOpen: boolean;
  onToggle: () => void;
  accountMap: Map<string, AccountResponse>;
}) {
  const date = new Date(tx.timestamp).toLocaleDateString();

  return (
    <>
      <tr
        onClick={onToggle}
        className="border-b cursor-pointer hover:bg-gray-50"
      >
        <td className="py-2 text-gray-400">{isOpen ? "▾" : "▸"}</td>
        <td className="py-2">{date}</td>
        <td className="py-2">{tx.description}</td>
        <td className="py-2 text-right text-gray-500">
          {tx.entries.length} entries
        </td>
      </tr>
      {isOpen && (
        <tr>
          <td colSpan={4} className="bg-gray-50 px-8 py-3">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400">
                  <th className="text-left py-1">Account</th>
                  <th className="text-right py-1">Debit</th>
                  <th className="text-right py-1">Credit</th>
                </tr>
              </thead>
              <tbody>
                {tx.entries.map((entry) => {
                  const acct = accountMap.get(entry.accountId);
                  return (
                    <tr key={entry.id} className="border-t border-gray-200">
                      <td className="py-1">
                        {acct ? acct.name : entry.accountId}
                      </td>
                      <td className="py-1 text-right font-mono">
                        {entry.type === "DEBIT" ? entry.amount : ""}
                      </td>
                      <td className="py-1 text-right font-mono">
                        {entry.type === "CREDIT" ? entry.amount : ""}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}
