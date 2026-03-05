import { NavLink, Outlet } from "react-router";

function navClass({ isActive }: { isActive: boolean }) {
  const base = "px-3 py-2 rounded-md text-sm font-medium";
  if (isActive) {
    return `${base} bg-gray-900 text-white`;
  } else {
    return `${base} text-gray-300 hover:bg-gray-700 hover:text-white`;
  }
}

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-800">
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex h-14 items-center justify-between">
            <span className="text-white font-bold text-lg">
              Financial Ledger
            </span>
            <div className="flex space-x-2">
              <NavLink to="/" className={navClass} end>
                Accounts
              </NavLink>
              <NavLink to="/transactions" className={navClass}>
                Transactions
              </NavLink>
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
