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
import { Quotations } from "./components/Quotations";
import { SalesOrders } from "./components/SalesOrders";
import { Tickets } from "./components/Tickets";
import { Calendar } from "./components/Calendar";
import { Calls } from "./components/Calls";
import { Emails } from "./components/Emails";
import { KnowledgeBase } from "./components/KnowledgeBase";
import { Documents } from "./components/Documents";
import { Workflows } from "./components/Workflows";
import { Integrations } from "./components/Integrations";
import { Notifications } from "./components/Notifications";
import { Admin } from "./components/Admin";
import { Settings } from "./components/Settings";
import { Products } from "./components/Products";
import { AIWorkspace } from "./components/AIWorkspace";
import { isAuthenticated, getUser } from "../lib/auth";

function AuthGuard({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AdminGuard({ children }: { children: React.ReactNode }) {
  const user = getUser();
  if (!user || (user.role !== "Admin" && user.role !== "System Administrator")) {
    return <Navigate to="/" replace />;
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
      { path: "quotations", Component: Quotations },
      { path: "sales-orders", Component: SalesOrders },
      { path: "invoices", Component: Invoices },
      { path: "tasks", Component: Tasks },
      { path: "tickets", Component: Tickets },
      { path: "analytics", Component: Analytics },
      { path: "calendar", Component: Calendar },
      { path: "calls", Component: Calls },
      { path: "emails", Component: Emails },
      { path: "knowledge-base", Component: KnowledgeBase },
      { path: "documents", Component: Documents },
      { path: "workflows", Component: Workflows },
      { path: "integrations", Component: Integrations },
      { path: "notifications", Component: Notifications },
      { path: "products", Component: Products },
      { path: "ai", Component: AIWorkspace },
      { path: "settings", Component: Settings },
      { 
        path: "admin", 
        element: (
          <AdminGuard>
            <Admin />
          </AdminGuard>
        ) 
      },
    ],
  },
]);
