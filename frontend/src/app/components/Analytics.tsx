import { useState, useEffect } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis
} from "recharts";
import { TrendingUp, TrendingDown, IndianRupee, Users, Target, Award } from "lucide-react";
import { leadsAPI, opportunitiesAPI, usersAPI } from "../../lib/api";

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border border-border bg-popover px-3 py-2 text-xs" style={{ fontFamily: "var(--font-mono)" }}>
      {label && <p className="text-muted-foreground mb-1">{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || p.fill }}>
          {p.name}: {typeof p.value === "number" && p.value > 1000 ? `₹${(p.value / 1000).toFixed(0)}k` : p.value}
        </p>
      ))}
    </div>
  );
};

type Period = "Today" | "This Week" | "This Month" | "QTD" | "YTD" | "All Time";

export function Analytics() {
  const [period, setPeriod] = useState<Period>("All Time");
  const [loading, setLoading] = useState(true);
  
  // Real data state
  const [revenueMonthly, setRevenueMonthly] = useState<any[]>([]);
  const [leadSources, setLeadSources] = useState<any[]>([]);
  const [teamPerformance, setTeamPerformance] = useState<any[]>([]);
  const [conversionFunnel, setConversionFunnel] = useState<any[]>([]);
  const [winLoss, setWinLoss] = useState<any[]>([]);
  
  const [kpiData, setKpiData] = useState({
    totalRevenue: 0,
    totalLeads: 0,
    totalDeals: 0,
    avgDeal: 0
  });

  useEffect(() => {
    loadData();
  }, [period]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [leadsRes, oppsRes, usersRes] = await Promise.all([
        leadsAPI.list(1, 1000),
        opportunitiesAPI.list(1, 1000),
        usersAPI.list()
      ]);

      const rawLeads = leadsRes.data.items || [];
      const rawOpps = oppsRes.data.items || [];
      const users = usersRes.data.items || [];

      // Filter by period
      let startDate = new Date(0);
      const now = new Date();
      if (period === "Today") {
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      } else if (period === "This Week") {
        const firstDay = now.getDate() - now.getDay();
        startDate = new Date(now.getFullYear(), now.getMonth(), firstDay);
      } else if (period === "This Month") {
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
      } else if (period === "QTD") {
        const quarter = Math.floor(now.getMonth() / 3);
        startDate = new Date(now.getFullYear(), quarter * 3, 1);
      } else if (period === "YTD") {
        startDate = new Date(now.getFullYear(), 0, 1);
      }

      const leads = rawLeads.filter((l: any) => new Date(l.created_at) >= startDate);
      const opps = rawOpps.filter((o: any) => new Date(o.created_at) >= startDate);

      // Process KPIs
      const totalLeads = leads.length;
      const wonOpps = opps.filter((o: any) => o.stage === 'Closed Won');
      const totalDeals = wonOpps.length;
      const totalRevenue = wonOpps.reduce((sum: number, o: any) => sum + (Number(o.amount) || 0), 0);
      const avgDeal = totalDeals > 0 ? Math.round(totalRevenue / totalDeals) : 0;
      setKpiData({ totalRevenue, totalLeads, totalDeals, avgDeal });

      // Process Monthly Revenue & Leads (Jan-Dec)
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const revMap: any = {};
      const winLossMap: any = {};
      months.forEach(m => {
        revMap[m] = { month: m, revenue: 0, deals: 0, leads: 0 };
        winLossMap[m] = { month: m, won: 0, lost: 0 };
      });

      leads.forEach((l: any) => {
        if (l.created_at) {
          const d = new Date(l.created_at);
          const m = months[d.getMonth()];
          revMap[m].leads++;
        }
      });

      opps.forEach((o: any) => {
        if (o.created_at) {
          const d = new Date(o.created_at);
          const m = months[d.getMonth()];
          if (o.stage === 'Closed Won') {
            revMap[m].revenue += Number(o.amount) || 0;
            revMap[m].deals++;
            winLossMap[m].won++;
          } else if (o.stage === 'Closed Lost') {
            winLossMap[m].lost++;
          }
        }
      });

      // Filter months up to current month to avoid trailing empty data
      const currentMonth = new Date().getMonth();
      const filteredMonthly = months.slice(0, currentMonth + 1).map(m => revMap[m]);
      setRevenueMonthly(filteredMonthly);
      setWinLoss(months.slice(0, currentMonth + 1).map(m => winLossMap[m]));

      // Process Lead Sources
      const sourceMap: Record<string, number> = {};
      leads.forEach((l: any) => {
        const src = l.source || 'Other';
        sourceMap[src] = (sourceMap[src] || 0) + 1;
      });
      const colors = ["#4f7eff", "#00d4aa", "#a78bfa", "#f59e0b", "#f43f5e", "#6b7694"];
      const sources = Object.keys(sourceMap).map((k, i) => ({
        name: k,
        value: Math.round((sourceMap[k] / totalLeads) * 100) || 0,
        color: colors[i % colors.length]
      })).filter(s => s.value > 0).sort((a, b) => b.value - a.value);
      setLeadSources(sources.length > 0 ? sources : [{ name: "No Data", value: 100, color: "#cbd5e1" }]);

      // Process Funnel
      const funnelStages = [
        { stage: "Leads", count: leads.length, rate: 100 },
        { stage: "Qualification", count: opps.filter((o: any) => ['Qualification', 'Proposal', 'Negotiation', 'Closed Won'].includes(o.stage)).length, rate: 0 },
        { stage: "Proposal", count: opps.filter((o: any) => ['Proposal', 'Negotiation', 'Closed Won'].includes(o.stage)).length, rate: 0 },
        { stage: "Negotiation", count: opps.filter((o: any) => ['Negotiation', 'Closed Won'].includes(o.stage)).length, rate: 0 },
        { stage: "Closed Won", count: wonOpps.length, rate: 0 }
      ];
      funnelStages.forEach(f => {
        f.rate = leads.length > 0 ? Number(((f.count / leads.length) * 100).toFixed(1)) : 0;
      });
      setConversionFunnel(funnelStages);

      // Process Team Performance
      const userStats: Record<string, any> = {};
      users.forEach((u: any) => {
        userStats[u.id] = { name: u.first_name ? `${u.first_name} ${u.last_name || ''}` : u.email, deals: 0, revenue: 0, winRate: 0, quota: 500000, won: 0, lost: 0 };
      });
      opps.forEach((o: any) => {
        if (o.assigned_to_id && userStats[o.assigned_to_id]) {
          if (o.stage === 'Closed Won') {
            userStats[o.assigned_to_id].revenue += Number(o.amount) || 0;
            userStats[o.assigned_to_id].deals++;
            userStats[o.assigned_to_id].won++;
          } else if (o.stage === 'Closed Lost') {
            userStats[o.assigned_to_id].lost++;
          }
        }
      });
      const team = Object.values(userStats).map(u => {
        const total = u.won + u.lost;
        u.winRate = total > 0 ? Math.round((u.won / total) * 100) : 0;
        return u;
      }).filter(u => u.deals > 0 || u.name !== 'admin@crm.com'); // hide inactive admins
      setTeamPerformance(team);

    } catch (error) {
      console.error("Failed to load analytics data", error);
    } finally {
      setLoading(false);
    }
  };

  const kpis = [
    { label: "Total Revenue", value: `₹${(kpiData.totalRevenue / 1000).toFixed(0)}k`, change: "Actual", up: true, icon: IndianRupee, color: "#00d4aa" },
    { label: "Total Leads", value: kpiData.totalLeads, change: "Actual", up: true, icon: Users, color: "#4f7eff" },
    { label: "Deals Closed", value: kpiData.totalDeals, change: "Actual", up: true, icon: Target, color: "#f59e0b" },
    { label: "Avg Deal Size", value: `₹${(kpiData.avgDeal / 1000).toFixed(0)}k`, change: "Actual", up: true, icon: Award, color: "#a78bfa" },
  ];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-full">
        <span className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 min-h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-foreground">Analytics & Reporting</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Real-time Performance Data</p>
        </div>
        <div className="flex items-center gap-1 border border-border rounded overflow-hidden">
          {(["Today", "This Week", "This Month", "QTD", "YTD", "All Time"] as Period[]).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-xs font-mono font-medium transition-colors ${period === p ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground hover:bg-white/5"}`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(({ label, value, change, up, icon: Icon, color }) => (
          <div key={label} className="rounded border border-border bg-card p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
              <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: color + "18" }}>
                <Icon size={13} style={{ color }} />
              </div>
            </div>
            <p className="text-2xl font-mono font-semibold text-foreground">{value}</p>
            <div className="flex items-center gap-1 mt-1">
              {up ? <TrendingUp size={11} style={{ color: "#00d4aa" }} /> : <TrendingDown size={11} style={{ color: "#f43f5e" }} />}
              <span className="text-[11px] font-mono" style={{ color: up ? "#00d4aa" : "#f43f5e" }}>{change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Revenue & Leads */}
        <div className="lg:col-span-2 rounded border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs font-semibold text-foreground">Revenue & Lead Volume</p>
              <p className="text-[11px] text-muted-foreground">Monthly trend</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-muted-foreground"><span className="inline-block w-3 h-0.5 rounded" style={{ background: "#4f7eff" }} /> Revenue</span>
              <span className="flex items-center gap-1 text-muted-foreground"><span className="inline-block w-3 h-0.5 rounded" style={{ background: "#00d4aa" }} /> Leads</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={revenueMonthly} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="revGrad2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f7eff" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#4f7eff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="leadGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v / 1000}k`} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area yAxisId="left" type="monotone" dataKey="revenue" name="Revenue" stroke="#4f7eff" strokeWidth={2} fill="url(#revGrad2)" dot={false} />
              <Area yAxisId="right" type="monotone" dataKey="leads" name="Leads" stroke="#00d4aa" strokeWidth={2} fill="url(#leadGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Lead sources */}
        <div className="rounded border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Lead Sources</p>
          <p className="text-[11px] text-muted-foreground mb-3">Distribution</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={leadSources}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
              >
                {leadSources.map((s, i) => <Cell key={i} fill={s.color} />)}
              </Pie>
              <Tooltip
                content={({ active, payload }) =>
                  active && payload?.length ? (
                    <div className="rounded border border-border bg-popover px-2.5 py-1.5 text-xs font-mono">
                      <p style={{ color: payload[0].payload.color }}>{payload[0].name}: {payload[0].value}%</p>
                    </div>
                  ) : null
                }
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2 max-h-24 overflow-y-auto">
            {leadSources.map((s, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: s.color }} />
                  <span className="text-[11px] text-muted-foreground">{s.name}</span>
                </div>
                <span className="text-[11px] font-mono text-foreground">{s.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Conversion funnel */}
        <div className="rounded border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Conversion Funnel</p>
          <p className="text-[11px] text-muted-foreground mb-4">Lead → Close · overall</p>
          <div className="space-y-2">
            {conversionFunnel.map((f, i) => (
              <div key={f.stage}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-muted-foreground">{f.stage}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-foreground">{f.count}</span>
                    <span className="text-[10px] font-mono text-muted-foreground">{f.rate}%</span>
                  </div>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${f.rate}%`,
                      background: ["#6b7694", "#4f7eff", "#a78bfa", "#f59e0b", "#00d4aa"][i % 5],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Win/Loss */}
        <div className="rounded border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Won vs. Lost Deals</p>
          <p className="text-[11px] text-muted-foreground mb-3">Monthly count</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={winLoss} margin={{ top: 0, right: 0, left: -20, bottom: 0 }} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="won" name="Won" fill="#00d4aa" radius={[2, 2, 0, 0]} maxBarSize={16} />
              <Bar dataKey="lost" name="Lost" fill="#f43f5e" radius={[2, 2, 0, 0]} maxBarSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Team table */}
      <div className="rounded border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <p className="text-xs font-semibold text-foreground">Rep Performance · {period}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse min-w-[600px]">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                {["Rep", "Deals Won", "Revenue", "Win Rate", "Quota Attainment"].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {teamPerformance.map((rep, i) => {
                const attainment = Math.round((rep.revenue / rep.quota) * 100);
                return (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-mono font-semibold text-primary">
                          {rep.name.substring(0, 2).toUpperCase()}
                        </div>
                        <span className="font-medium text-foreground truncate max-w-[120px]">{rep.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-foreground font-semibold">{rep.deals}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-foreground">₹{(rep.revenue / 1000).toFixed(0)}k</td>
                    <td className="px-4 py-3">
                      <span className="font-mono font-semibold" style={{ color: rep.winRate > 50 ? "#00d4aa" : rep.winRate > 35 ? "#f59e0b" : "#f43f5e" }}>
                        {rep.winRate}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full bg-white/5 max-w-24 overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.min(attainment, 100)}%`,
                              background: attainment >= 80 ? "#00d4aa" : attainment >= 60 ? "#f59e0b" : "#f43f5e",
                            }}
                          />
                        </div>
                        <span className="font-mono text-[11px] text-foreground">{attainment}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {teamPerformance.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-muted-foreground">No active reps found for this period.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
