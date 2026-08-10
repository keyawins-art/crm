import { useState, useEffect } from "react";
import {
  TrendingUp, TrendingDown, Users, IndianRupee, Target, Activity,
  CheckCircle2, Clock, AlertCircle, ArrowRight, Phone, Mail,
  Calendar, Circle, Edit, AlertTriangle, Trophy, Zap, BarChart3,
  ChevronRight, PhoneCall
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Legend
} from "recharts";
import { dashboardAPI, reportsAPI, tasksAPI, opportunitiesAPI } from "../../lib/api";
import { getUser } from "../../lib/auth";

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [pipelineData, setPipelineData] = useState<any[]>([]);
  const [smartData, setSmartData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const user = getUser();
  const userName = user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "User";

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsResult, revResult, pipeResult, smartResult] = await Promise.allSettled([
          dashboardAPI.stats(),
          reportsAPI.revenue(),
          reportsAPI.sales(),
          dashboardAPI.smart(),
        ]);

        if (!isMounted) return;

        if (statsResult.status === "fulfilled" && statsResult.value?.data) {
          setStats(statsResult.value.data);
        }

        if (revResult.status === "fulfilled" && Array.isArray(revResult.value?.data)) {
          setRevenueData(
            revResult.value.data.map((r: any) => ({
              month: r.month,
              revenue: r.revenue,
            }))
          );
        }

        if (pipeResult.status === "fulfilled" && Array.isArray(pipeResult.value?.data)) {
          setPipelineData(
            pipeResult.value.data.map((p: any) => ({
              stage: (p.stage || "").replace("_", " "),
              count: p.count,
              value: p.total_amount,
            }))
          );
        }

        if (smartResult.status === "fulfilled" && smartResult.value?.data) {
          setSmartData(smartResult.value.data);
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, []);

  const kpis = stats
    ? [
        {
          label: "Total Revenue",
          value: `₹${((stats.revenue || 0) / 1000).toFixed(1)}k`,
          sub: "Closed Won deals",
          icon: IndianRupee,
          color: "#00d4aa",
        },
        {
          label: "Total Leads",
          value: (stats.leads || 0).toString(),
          sub: "Active in database",
          icon: Users,
          color: "#4f7eff",
        },
        {
          label: "Opportunities",
          value: (stats.opportunities || 0).toString(),
          sub: "Deals in pipeline",
          icon: Target,
          color: "#f59e0b",
        },
        {
          label: "Overdue Follow-ups",
          value: smartData?.overdue_followups?.length?.toString() || "0",
          sub: smartData?.overdue_followups?.length > 0 ? "Needs attention!" : "All caught up",
          icon: AlertTriangle,
          color: smartData?.overdue_followups?.length > 0 ? "#f43f5e" : "#00d4aa",
        },
      ]
    : [];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-xl"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        <p className="text-muted-foreground mb-1 font-medium">{label}</p>
        {payload.map((p: any) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.dataKey === "achievement"
              ? "Actual"
              : p.dataKey === "target"
              ? "Target"
              : p.dataKey === "revenue"
              ? "Revenue"
              : p.dataKey === "weighted_forecast"
              ? "Forecast"
              : p.dataKey === "actual"
              ? "Closed Won"
              : p.dataKey}
            : ₹{(p.value / 1000).toFixed(0)}k
          </p>
        ))}
      </div>
    );
  };

  const ratingBadge = (r: string | null) => {
    if (!r) return null;
    const colors: Record<string, string> = {
      hot: "#f43f5e",
      warm: "#f59e0b",
      cold: "#6b7694",
    };
    return (
      <span
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider"
        style={{
          background: (colors[r] || "#6b7694") + "18",
          color: colors[r] || "#6b7694",
        }}
      >
        {r}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  const overdue = smartData?.overdue_followups || [];
  const targetAch = smartData?.target_vs_achievement || [];
  const performers = smartData?.salesperson_performance || [];
  const forecast = smartData?.revenue_forecast || [];
  const maxRevenue = Math.max(...performers.map((p: any) => p.won_revenue), 1);

  return (
    <div className="p-6 space-y-6 min-h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-foreground">
            Good afternoon, {userName.split(" ")[0]}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}{" "}
            · Smart Dashboard
          </p>
        </div>
        <div className="flex items-center gap-2">
          {overdue.length > 0 && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-full animate-pulse"
              style={{ background: "#f43f5e18", color: "#f43f5e" }}>
              <AlertTriangle size={11} />
              {overdue.length} overdue
            </span>
          )}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-4 space-y-3 hover:border-primary/20 transition-colors">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                {label}
              </p>
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{ background: color + "18" }}
              >
                <Icon size={13} style={{ color }} />
              </div>
            </div>
            <div>
              <p
                className="text-2xl font-semibold text-foreground tracking-tight"
                style={{ fontFamily: "var(--font-mono)" }}
              >
                {value}
              </p>
              <span className="text-[11px] text-muted-foreground">{sub}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row — Revenue Trend + Pipeline */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Revenue trend */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs font-semibold text-foreground">Revenue Trend</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">Monthly actuals</p>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground">
              <span className="inline-block w-3 h-0.5 rounded bg-chart-1" /> Revenue
            </span>
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
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `₹${v / 1000}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#4f7eff"
                  strokeWidth={2}
                  fill="url(#revGrad)"
                  dot={false}
                />
              </AreaChart>
            ) : (
              <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground">
                Not enough data
              </div>
            )}
          </ResponsiveContainer>
        </div>

        {/* Pipeline by stage */}
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Pipeline by Stage</p>
          <p className="text-[11px] text-muted-foreground mb-4">Deal count</p>
          <ResponsiveContainer width="100%" height={180}>
            {pipelineData.length > 0 ? (
              <BarChart
                data={pipelineData}
                layout="vertical"
                margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
              >
                <XAxis
                  type="number"
                  tick={{ fill: "#6b7694", fontSize: 9, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="stage"
                  tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  width={80}
                />
                <Tooltip
                  cursor={{ fill: "rgba(255,255,255,0.03)" }}
                  content={({ active, payload }) =>
                    active && payload?.length ? (
                      <div className="rounded-lg border border-border bg-popover px-3 py-1.5 text-xs font-mono capitalize shadow-xl">
                        <p className="text-muted-foreground">{payload[0].payload.stage}</p>
                        <p className="text-foreground">{payload[0].value} deals</p>
                        <p style={{ color: "#00d4aa" }}>
                          ₹{((payload[0].payload.value || 0) / 1000).toFixed(0)}k value
                        </p>
                      </div>
                    ) : null
                  }
                />
                <Bar dataKey="count" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {pipelineData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={["#4f7eff", "#00d4aa", "#f59e0b", "#a78bfa", "#f43f5e"][i % 5]}
                    />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground">
                No pipeline data
              </div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* ─── SMART DASHBOARD WIDGETS ─────────────────────────────────────── */}

      {/* Row: Overdue Follow-ups + Target vs Achievement */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Overdue Follow-ups */}
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: "#f43f5e18" }}>
                <AlertTriangle size={12} style={{ color: "#f43f5e" }} />
              </div>
              <div>
                <p className="text-xs font-semibold text-foreground">Overdue Follow-ups</p>
                <p className="text-[10px] text-muted-foreground">Leads past follow-up date</p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md font-bold"
              style={{ background: overdue.length > 0 ? "#f43f5e18" : "#00d4aa18", color: overdue.length > 0 ? "#f43f5e" : "#00d4aa" }}>
              {overdue.length}
            </span>
          </div>
          <div className="divide-y divide-border max-h-[260px] overflow-y-auto">
            {overdue.length > 0 ? (
              overdue.map((lead: any, i: number) => (
                <div key={lead.id || i} className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold"
                    style={{ background: "#f43f5e18", color: "#f43f5e" }}>
                    {lead.days_overdue}d
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-medium text-foreground truncate">{lead.name}</p>
                      {ratingBadge(lead.rating)}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-muted-foreground truncate">{lead.company}</span>
                      <span className="text-[10px] text-muted-foreground/50">·</span>
                      <span className="text-[10px] text-muted-foreground truncate">{lead.assigned_to}</span>
                    </div>
                  </div>
                  {lead.phone && (
                    <div className="w-6 h-6 rounded-md flex items-center justify-center shrink-0 cursor-pointer hover:bg-primary/10 transition-colors"
                      style={{ background: "#00d4aa18", color: "#00d4aa" }}
                      title={`Call ${lead.phone}`}>
                      <PhoneCall size={11} />
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="p-8 text-center">
                <CheckCircle2 size={20} className="mx-auto mb-2" style={{ color: "#00d4aa" }} />
                <p className="text-xs text-muted-foreground">All follow-ups are on track!</p>
              </div>
            )}
          </div>
        </div>

        {/* Target vs Achievement */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: "#a78bfa18" }}>
                <Target size={12} style={{ color: "#a78bfa" }} />
              </div>
              <div>
                <p className="text-xs font-semibold text-foreground">Target vs Achievement</p>
                <p className="text-[10px] text-muted-foreground">Monthly comparison · {new Date().getFullYear()}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: "#4f7eff" }} /> Actual
              </span>
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: "#a78bfa40" }} /> Target
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            {targetAch.length > 0 ? (
              <BarChart data={targetAch} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#6b7694", fontSize: 9, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#6b7694", fontSize: 9, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `₹${v / 1000}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="target" fill="#a78bfa40" radius={[3, 3, 0, 0]} maxBarSize={12} />
                <Bar dataKey="achievement" fill="#4f7eff" radius={[3, 3, 0, 0]} maxBarSize={12} />
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground">
                No data yet
              </div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row: Sales Leaderboard + Revenue Forecast */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Sales-person Performance Leaderboard */}
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: "#f59e0b18" }}>
                <Trophy size={12} style={{ color: "#f59e0b" }} />
              </div>
              <div>
                <p className="text-xs font-semibold text-foreground">Sales Leaderboard</p>
                <p className="text-[10px] text-muted-foreground">Performance by revenue</p>
              </div>
            </div>
          </div>
          <div className="divide-y divide-border">
            {performers.length > 0 ? (
              performers.map((p: any, i: number) => {
                const medals = ["🥇", "🥈", "🥉"];
                const pct = maxRevenue > 0 ? (p.won_revenue / maxRevenue) * 100 : 0;
                return (
                  <div key={p.email} className="px-4 py-3 hover:bg-white/[0.02] transition-colors">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[11px] font-mono font-bold text-primary shrink-0">
                        {medals[i] || `#${i + 1}`}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground truncate">{p.name}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{p.email}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-xs font-mono font-semibold text-foreground">
                          ₹{(p.won_revenue / 1000).toFixed(0)}k
                        </p>
                        <p className="text-[10px] text-muted-foreground">{p.deals_won} deals</p>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${Math.max(pct, 2)}%`,
                          background: i === 0 ? "#f59e0b" : i === 1 ? "#4f7eff" : "#a78bfa",
                        }}
                      />
                    </div>
                    {/* Stats row */}
                    <div className="flex items-center gap-4 mt-2 text-[10px] font-mono text-muted-foreground">
                      <span>Pipeline: ₹{(p.pipeline_value / 1000).toFixed(0)}k</span>
                      <span>Leads: {p.total_leads}</span>
                      <span>Conv: {p.conversion_rate}%</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-xs text-muted-foreground">No sales data</div>
            )}
          </div>
        </div>

        {/* Revenue Forecast */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: "#00d4aa18" }}>
                <Zap size={12} style={{ color: "#00d4aa" }} />
              </div>
              <div>
                <p className="text-xs font-semibold text-foreground">Revenue Forecast</p>
                <p className="text-[10px] text-muted-foreground">Weighted pipeline · Next 3 months</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: "#00d4aa" }} /> Forecast
              </span>
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: "#4f7eff" }} /> Actual
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            {forecast.length > 0 ? (
              <AreaChart data={forecast} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f7eff" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#4f7eff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `₹${v / 1000}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#4f7eff"
                  strokeWidth={2}
                  fill="url(#actualGrad)"
                  dot={false}
                />
                <Area
                  type="monotone"
                  dataKey="weighted_forecast"
                  stroke="#00d4aa"
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  fill="url(#forecastGrad)"
                  dot={{ r: 3, fill: "#00d4aa", strokeWidth: 0 }}
                />
              </AreaChart>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <BarChart3 size={20} className="mx-auto mb-2" style={{ color: "#6b7694" }} />
                  <p className="text-[11px] text-muted-foreground">No open deals in pipeline for forecasting</p>
                </div>
              </div>
            )}
          </ResponsiveContainer>
          {/* Forecast summary cards */}
          {forecast.length > 0 && (
            <div className="grid grid-cols-3 gap-2 mt-3">
              {forecast.slice(0, 3).map((f: any) => (
                <div key={f.month + f.year} className="rounded-md p-2 text-center" style={{ background: "rgba(255,255,255,0.02)" }}>
                  <p className="text-[10px] text-muted-foreground font-mono">{f.month}</p>
                  <p className="text-xs font-mono font-semibold text-foreground mt-0.5">
                    ₹{(f.weighted_forecast / 1000).toFixed(0)}k
                  </p>
                  <p className="text-[9px] text-muted-foreground">{f.deal_count} deals</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
