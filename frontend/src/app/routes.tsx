import { createBrowserRouter, Navigate } from "react-router";
import { Root } from "./components/Root";
import { Dashboard } from "./components/Dashboard";
import { Contacts } from "./components/Contacts";
import { Deals } from "./components/Deals";
import { Tasks } from "./components/Tasks";
import { Analytics } from "./components/Analytics";
import { Login } from "./components/Login";
import { Leads } from "./components/Leads";
import { Accounts } from "./components/Accounts";
import { Invoices } from "./components/Invoices";
import { Tickets } from "./components/Tickets";
import { isAuthenticated } from "../lib/auth";

function AuthGuard({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    element: (
      <AuthGuard>
        <Root />
      </AuthGuard>
    ),
    children: [
      { index: true, Component: Dashboard },
      { path: "leads", Component: Leads },
      { path: "contacts", Component: Contacts },
      { path: "accounts", Component: Accounts },
      { path: "deals", Component: Deals },
      { path: "invoices", Component: Invoices },
      { path: "tasks", Component: Tasks },
      { path: "tickets", Component: Tickets },
      { path: "analytics", Component: Analytics },
    ],
  },
]);
