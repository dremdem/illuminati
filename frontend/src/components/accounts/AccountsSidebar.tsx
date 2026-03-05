import type { AccountResponse, AccountType } from "../../types/api";

const TYPES: AccountType[] = ["ASSET", "LIABILITY", "REVENUE", "EXPENSE"];

const LABEL_COLORS: Record<string, string> = {
  ASSET: "text-blue-700",
  LIABILITY: "text-red-700",
  REVENUE: "text-green-700",
  EXPENSE: "text-yellow-700",
};

interface AccountsSidebarProps {
  accounts: AccountResponse[];
}

export default function AccountsSidebar({ accounts }: AccountsSidebarProps) {
  const totals = TYPES.map((type) => {
    const sum = accounts
      .filter((a) => a.type === type)
      .reduce((acc, a) => acc + parseFloat(a.balance), 0);
    return { type, sum };
  });

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wide">
        Totals by Type
      </h3>
      <dl className="space-y-2">
        {totals.map(({ type, sum }) => (
          <div key={type} className="flex justify-between">
            <dt className={`text-sm font-medium ${LABEL_COLORS[type]}`}>
              {type}
            </dt>
            <dd className="text-sm font-mono">{sum.toFixed(2)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
