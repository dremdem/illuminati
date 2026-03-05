import { useState } from "react";
import { useAccounts, useAllAccounts } from "../../hooks/useAccounts";
import AccountsTable from "./AccountsTable";
import AccountsSidebar from "./AccountsSidebar";
import AddAccountModal from "./AddAccountModal";
import Pagination from "../Pagination";

const LIMIT = 10;

export default function AccountsPage() {
  const [offset, setOffset] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, isError } = useAccounts(LIMIT, offset);
  const allAccounts = useAllAccounts();

  if (isLoading) return <p className="text-gray-500">Loading accounts…</p>;
  if (isError) return <p className="text-red-600">Failed to load accounts.</p>;

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-gray-900">Accounts</h1>
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + Add Account
          </button>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <AccountsTable accounts={data!.items} />
          <Pagination
            total={data!.total}
            limit={LIMIT}
            offset={offset}
            onOffsetChange={setOffset}
          />
        </div>
      </div>
      <div className="w-64 shrink-0">
        {allAccounts.data && (
          <AccountsSidebar accounts={allAccounts.data.items} />
        )}
      </div>
      <AddAccountModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
}
