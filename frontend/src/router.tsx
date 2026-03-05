import { createBrowserRouter } from "react-router";
import Layout from "./components/Layout";
import AccountsPage from "./components/accounts/AccountsPage";
import TransactionsPage from "./components/transactions/TransactionsPage";

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <AccountsPage /> },
      { path: "/transactions", element: <TransactionsPage /> },
    ],
  },
]);
