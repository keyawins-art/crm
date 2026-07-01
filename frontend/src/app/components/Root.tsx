import { NavLink, Outlet, useLocation } from "react-router";
import {
  LayoutDashboard, Users, TrendingUp, CheckSquare, BarChart3,
  Bell, Search, Settings, ChevronRight, Zap, LogOut,
  MessageSquare, FileText, Shield, HelpCircle, Menu, X,
  UserPlus, Building2, LifeBuoy, Target
} from "lucide-react";
import { useState } from "react";
import { logout, getUser } from "../../lib/auth";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/leads", icon: UserPlus, label: "Leads" },
  { to: "/contacts", icon: Users, label: "Contacts" },
  { to: "/accounts", icon: Building2, label: "Accounts" },
  { to: "/deals", icon: TrendingUp, label: "Deals" },
  { to: "/invoices", icon: FileText, label: "Invoices" },
  { to: "/tasks", icon: CheckSquare, label: "Tasks" },
  { to: "/tickets", icon: LifeBuoy, label: "Tickets" },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
];

const bottomItems = [
  { icon: MessageSquare, label: "Messages", badge: 3 },
  { icon: Shield, label: "Security" },
  { icon: HelpCircle, label: "Help" },
  { icon: Settings, label: "Settings" },
];

export function Root() {
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState("");
  const location = useLocation();
  const user = getUser();

  const pageTitle = navItems.find(n => n.end ? location.pathname === n.to : location.pathname.startsWith(n.to))?.label ?? "CRM";
  const userInitials = user ? `${(user.first_name || "U")[0]}${(user.last_name || "")[0]}`.toUpperCase() : "U";
  const userName = user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "User";
  const userRole = user?.role || "Sales Executive";

  return (
    <div className="flex h-screen bg-background overflow-hidden" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col shrink-0 border-r border-border transition-all duration-200"
        style={{
          width: collapsed ? 64 : 220,
          background: "var(--sidebar)",
          borderColor: "var(--sidebar-border)",
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-14 border-b shrink-0" style={{ borderColor: "var(--sidebar-border)" }}>
          <div className="flex items-center justify-center w-7 h-7 rounded bg-primary shrink-0">
            <Zap size={14} className="text-white" />
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold tracking-tight text-foreground truncate">
              NexusCRM
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 overflow-y-auto">
          <div className="px-2 space-y-0.5">
            {navItems.map(({ to, icon: Icon, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-2.5 py-2 rounded text-xs font-medium transition-colors cursor-pointer ${
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon size={15} className="shrink-0" />
                    {!collapsed && <span className="truncate">{label}</span>}
                    {!collapsed && isActive && <ChevronRight size={12} className="ml-auto opacity-60" />}
                  </>
                )}
              </NavLink>
            ))}
          </div>

          {!collapsed && (
            <div className="mt-6 px-4">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50 mb-2">
                Quick Access
              </p>
              <div className="space-y-0.5">
                {bottomItems.map(({ icon: Icon, label, badge }) => (
                  <button
                    key={label}
                    className="flex items-center gap-3 px-2.5 py-2 rounded text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors w-full"
                  >
                    <Icon size={15} className="shrink-0" />
                    <span className="truncate">{label}</span>
                    {badge && (
                      <span className="ml-auto bg-primary text-white text-[10px] font-mono px-1.5 py-0.5 rounded-full">
                        {badge}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </nav>

        {/* User */}
        <div className="border-t p-3 shrink-0" style={{ borderColor: "var(--sidebar-border)" }}>
          {collapsed ? (
            <div className="w-7 h-7 rounded-full bg-primary/20 mx-auto flex items-center justify-center text-xs font-mono font-semibold text-primary">
              {userInitials}
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-mono font-semibold text-primary shrink-0">
                {userInitials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground truncate">{userName}</p>
                <p className="text-[10px] text-muted-foreground truncate">{userRole}</p>
              </div>
              <button
                onClick={logout}
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="Logout"
              >
                <LogOut size={13} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center gap-4 px-6 h-14 border-b border-border shrink-0 bg-background">
          <button
            onClick={() => setCollapsed(c => !c)}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            {collapsed ? <Menu size={16} /> : <X size={16} />}
          </button>

          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">{pageTitle}</span>
          </div>

          <div className="flex-1 max-w-sm ml-4">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search contacts, deals, tasks..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
              />
              <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono text-muted-foreground/50">⌘K</span>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <button className="relative text-muted-foreground hover:text-foreground transition-colors">
              <Bell size={16} />
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-primary rounded-full" />
            </button>
            <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-mono font-semibold text-primary">
              {userInitials}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
