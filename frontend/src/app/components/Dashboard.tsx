import { useState, useEffect } from "react";
import {
  TrendingUp, TrendingDown, Users, IndianRupee, Target, Activity,
  CheckCircle2, Clock, AlertCircle, ArrowRight, Phone, Mail,
  Calendar, Circle, Edit
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { dashboardAPI, reportsAPI, tasksAPI, opportunitiesAPI } from "../../lib/api";
import { getUser } from "../../lib/auth";

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [pipelineData, setPipelineData] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [upcomingTasks, setUpcomingTasks] = useState<any[]>([]);
  const [topContacts, setTopContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const user = getUser();
  const userName = user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "User";

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [
          statsRes, revRes, pipeRes, auditRes, tasksRes, oppsRes
        ] = await Promise.all([
          dashboardAPI.stats(),
          reportsAPI.revenue(),
          reportsAPI.sales(),
          dashboardAPI.auditLogs(6),
          tasksAPI.list(1, 5),
          opportunitiesAPI.list(1, 5) // Fetch recent/top opportunities
        ]);

        setStats(statsRes.data);
        
        // Transform revenue data to match Recharts expected format
        const rev = revRes.data.map((r: any) => ({
          month: r.month,
          revenue: r.revenue,
          target: r.revenue * 0.9 // Mocking a target based on revenue for now
        }));
        setRevenueData(rev);

        // Transform pipeline data
        const pipe = pipeRes.data.map((p: any) => ({
          stage: (p.stage || "").replace("_", " "),
          count: p.count,
          value: p.total_amount
        }));
        setPipelineData(pipe);

        // Transform audit logs to activities
        const acts = auditRes.data.map((a: any) => ({
          type: "action",
          user: a.user.first_name || "System",
          contact: "—",
          company: a.entity_type,
          time: new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          note: a.details || a.action
        }));
        setActivities(acts);

        // Transform tasks
        const tasks = tasksRes.data.items.filter((t: any) => t.status !== "completed").slice(0, 5).map((t: any) => ({
          title: t.title,
          due: t.due_date ? new Date(t.due_date).toLocaleDateString() : "No date",
          priority: t.priority,
          contact: null
        }));
        setUpcomingTasks(tasks);

        // Transform top opportunities
        const opps = oppsRes.data.items.map((o: any) => ({
          name: o.name,
          company: "—",
          value: `₹${(o.amount / 1000).toFixed(0)}k`,
          stage: o.stage.replace("_", " "),
          avatar: o.name.substring(0, 2).toUpperCase()
        }));
        setTopContacts(opps);

      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const kpis = stats ? [
    {
      label: "Total Revenue",
      value: `₹${((stats.revenue || 0) / 1000).toFixed(1)}k`,
      change: "",
      up: true,
      sub: "From Closed Won deals",
      icon: IndianRupee,
      color: "#00d4aa",
    },
    {
      label: "Total Leads",
      value: (stats.leads || 0).toString(),
      change: "",
      up: true,
      sub: "Active in database",
      icon: Users,
      color: "#4f7eff",
    },
    {
      label: "Opportunities",
      value: (stats.opportunities || 0).toString(),
      change: "",
      up: true,
      sub: "Deals in pipeline",
      icon: Target,
      color: "#f59e0b",
    },
    {
      label: "Accounts",
      value: (stats.accounts || 0).toString(),
      change: "",
      up: true,
      sub: "Active companies",
      icon: Activity,
      color: "#a78bfa",
    },
  ] : [];

  const activityIcon = (type: string) => {
    switch (type) {
      case "call": return <Phone size={11} />;
      case "email": return <Mail size={11} />;
      case "deal": return <TrendingUp size={11} />;
      case "task": return <CheckCircle2 size={11} />;
      case "action": return <Edit size={11} />;
      default: return <Circle size={11} />;
    }
  };

  const activityColor = (type: string) => {
    switch (type) {
      case "call": return "#00d4aa";
      case "email": return "#4f7eff";
      case "deal": return "#f59e0b";
      case "task": return "#a78bfa";
      case "action": return "#6b7694";
      default: return "#6b7694";
    }
  };

  const priorityDot = (p: string) => {
    const c = p === "high" ? "#f43f5e" : p === "medium" ? "#f59e0b" : "#6b7694";
    return <span className="inline-block w-1.5 h-1.5 rounded-full shrink-0 mt-1" style={{ background: c }} />;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded border border-border bg-popover px-3 py-2 text-xs" style={{ fontFamily: "var(--font-mono)" }}>
        <p className="text-muted-foreground mb-1">{label}</p>
        {payload.map((p: any) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.dataKey === "revenue" ? "Revenue" : "Target"}: ${(p.value / 1000).toFixed(0)}k
          </p>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 min-h-full" style={{ fontFamily: "var(--font-sans)" }}>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-foreground">Good afternoon, {userName.split(" ")[0]}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })} · Here's your pipeline at a glance.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            + New Deal
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="rounded border border-border bg-card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
              <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: color + "18" }}>
                <Icon size={13} style={{ color }} />
              </div>
            </div>
            <div>
              <p className="text-2xl font-semibold text-foreground tracking-tight" style={{ fontFamily: "var(--font-mono)" }}>
                {value}
              </p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-[11px] text-muted-foreground truncate">{sub}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Revenue trend */}
        <div className="lg:col-span-2 rounded border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs font-semibold text-foreground">Revenue Trend</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">Monthly actuals</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-muted-foreground"><span className="inline-block w-3 h-0.5 rounded bg-chart-1" /> Revenue</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            {revenueData.length > 0 ? (
              <AreaChart data={revenueData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f7eff" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#4f7eff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="month" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v / 1000}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="revenue" stroke="#4f7eff" strokeWidth={2} fill="url(#revGrad)" dot={false} />
              </AreaChart>
            ) : (
              <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground">Not enough data</div>
            )}
          </ResponsiveContainer>
        </div>

        {/* Pipeline by stage */}
        <div className="rounded border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Pipeline by Stage</p>
          <p className="text-[11px] text-muted-foreground mb-4">Deal count</p>
          <ResponsiveContainer width="100%" height={180}>
            {pipelineData.length > 0 ? (
              <BarChart data={pipelineData} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <XAxis type="number" tick={{ fill: "#6b7694", fontSize: 9, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="stage" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} width={80} />
                <Tooltip
                  cursor={{ fill: "rgba(255,255,255,0.03)" }}
                  content={({ active, payload }) =>
                    active && payload?.length ? (
                      <div className="rounded border border-border bg-popover px-3 py-1.5 text-xs font-mono capitalize">
                        <p className="text-muted-foreground">{payload[0].payload.stage}</p>
                        <p className="text-foreground">{payload[0].value} deals</p>
                        <p style={{ color: "#00d4aa" }}>₹{((payload[0].payload.value || 0) / 1000).toFixed(0)}k value</p>
                      </div>
                    ) : null
                  }
                />
                <Bar dataKey="count" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {pipelineData.map((_, i) => (
                    <Cell key={i} fill={["#4f7eff", "#00d4aa", "#f59e0b", "#a78bfa", "#f43f5e"][i % 5]} />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground">No pipeline data</div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Activity feed */}
        <div className="lg:col-span-2 rounded border border-border bg-card">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <p className="text-xs font-semibold text-foreground">Recent Audit Logs</p>
            <button className="flex items-center gap-1 text-[11px] text-primary hover:text-primary/80 transition-colors">
              View all <ArrowRight size={11} />
            </button>
          </div>
          <div className="divide-y divide-border">
            {activities.length > 0 ? activities.map((a, i) => (
              <div key={i} className="flex items-start gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                  style={{ background: activityColor(a.type) + "18", color: activityColor(a.type) }}
                >
                  {activityIcon(a.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-foreground">
                    <span className="font-medium">{a.user}</span>
                    {a.company && <span className="text-muted-foreground capitalize"> on {a.company.replace("_", " ")}</span>}
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{a.note}</p>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground/50 shrink-0 mt-0.5">{a.time}</span>
              </div>
            )) : (
              <div className="p-4 text-center text-xs text-muted-foreground">No recent activity.</div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Tasks due */}
          <div className="rounded border border-border bg-card">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <p className="text-xs font-semibold text-foreground">Upcoming Tasks</p>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary">{upcomingTasks.length} tasks</span>
            </div>
            <div className="divide-y divide-border">
              {upcomingTasks.length > 0 ? upcomingTasks.map((t, i) => (
                <div key={i} className="flex items-start gap-2.5 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                  {priorityDot(t.priority)}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground truncate">{t.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] font-mono text-muted-foreground">{t.due}</span>
                      {t.contact && <span className="text-[10px] text-muted-foreground/60 truncate">{t.contact}</span>}
                    </div>
                  </div>
                </div>
              )) : (
                <div className="p-4 text-center text-xs text-muted-foreground">No upcoming tasks.</div>
              )}
            </div>
          </div>

          {/* Top contacts */}
          <div className="rounded border border-border bg-card">
            <div className="px-4 py-3 border-b border-border">
              <p className="text-xs font-semibold text-foreground">Recent Opportunities</p>
            </div>
            <div className="divide-y divide-border">
              {topContacts.length > 0 ? topContacts.map((c, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                  <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-mono font-semibold text-primary shrink-0">
                    {c.avatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{c.name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-mono font-semibold text-foreground">{c.value}</p>
                    <p className="text-[10px] text-muted-foreground capitalize">{c.stage}</p>
                  </div>
                </div>
              )) : (
                <div className="p-4 text-center text-xs text-muted-foreground">No open deals.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
