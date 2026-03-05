import { useState } from "react";
import Modal from "../Modal";
import { useCreateAccount } from "../../hooks/useAccounts";
import type { AccountType } from "../../types/api";

const ACCOUNT_TYPES: AccountType[] = [
  "ASSET",
  "LIABILITY",
  "REVENUE",
  "EXPENSE",
];

interface AddAccountModalProps {
  open: boolean;
  onClose: () => void;
}

export default function AddAccountModal({
  open,
  onClose,
}: AddAccountModalProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState<AccountType>("ASSET");
  const mutation = useCreateAccount();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(
      { name: name.trim(), type },
      {
        onSuccess: () => {
          setName("");
          setType("ASSET");
          onClose();
        },
      }
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Add Account">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. Cash"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type
          </label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as AccountType)}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ACCOUNT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
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
            disabled={mutation.isPending}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Creating…" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
