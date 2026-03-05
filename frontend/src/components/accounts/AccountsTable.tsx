import type { AccountResponse } from "../../types/api";

const TYPE_COLORS: Record<string, string> = {
  ASSET: "bg-blue-100 text-blue-800",
  LIABILITY: "bg-red-100 text-red-800",
  REVENUE: "bg-green-100 text-green-800",
  EXPENSE: "bg-yellow-100 text-yellow-800",
};

interface AccountsTableProps {
  accounts: AccountResponse[];
}

export default function AccountsTable({ accounts }: AccountsTableProps) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-gray-500">
          <th className="py-2 font-medium">Name</th>
          <th className="py-2 font-medium">Type</th>
          <th className="py-2 font-medium text-right">Balance</th>
        </tr>
      </thead>
      <tbody>
        {accounts.map((a) => (
          <tr key={a.id} className="border-b last:border-0 hover:bg-gray-50">
            <td className="py-2">{a.name}</td>
            <td className="py-2">
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${TYPE_COLORS[a.type] ?? ""}`}
              >
                {a.type}
              </span>
            </td>
            <td className="py-2 text-right font-mono">{a.balance}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
