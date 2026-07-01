import { useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis
} from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Users, Target, Award } from "lucide-react";

const revenueMonthly = [
  { month: "Jan", revenue: 142000, deals: 5, leads: 38 },
  { month: "Feb", revenue: 158000, deals: 7, leads: 42 },
  { month: "Mar", revenue: 134000, deals: 4, leads: 31 },
  { month: "Apr", revenue: 175000, deals: 8, leads: 55 },
  { month: "May", revenue: 192000, deals: 9, leads: 61 },
  { month: "Jun", revenue: 218000, deals: 7, leads: 52 },
];

const leadSources = [
  { name: "Website", value: 38, color: "#4f7eff" },
  { name: "Referral", value: 27, color: "#00d4aa" },
  { name: "LinkedIn", value: 18, color: "#a78bfa" },
  { name: "Cold Outreach", value: 11, color: "#f59e0b" },
  { name: "Events", value: 6, color: "#f43f5e" },
];

const teamPerformance = [
  { name: "James Dunn", calls: 47, emails: 124, deals: 7, revenue: 342000, winRate: 58, quota: 400000 },
  { name: "Sarah Chen", calls: 38, emails: 98, deals: 5, revenue: 218000, winRate: 42, quota: 300000 },
  { name: "Tom Okafor", calls: 29, emails: 76, deals: 4, revenue: 163000, winRate: 36, quota: 250000 },
];

const conversionFunnel = [
  { stage: "Leads", count: 279, rate: 100 },
  { stage: "Qualified", count: 143, rate: 51.3 },
  { stage: "Proposal", count: 67, rate: 24.0 },
  { stage: "Negotiation", count: 28, rate: 10.0 },
  { stage: "Closed Won", count: 16, rate: 5.7 },
];

const winLoss = [
  { month: "Jan", won: 5, lost: 3 },
  { month: "Feb", won: 7, lost: 2 },
  { month: "Mar", won: 4, lost: 5 },
  { month: "Apr", won: 8, lost: 3 },
  { month: "May", won: 9, lost: 4 },
  { month: "Jun", won: 7, lost: 2 },
];

const radarData = [
  { metric: "Pipeline", james: 85, sarah: 72, tom: 61 },
  { metric: "Win Rate", james: 78, sarah: 56, tom: 48 },
  { metric: "Activity", james: 90, sarah: 82, tom: 64 },
  { metric: "Avg Deal", james: 95, sarah: 70, tom: 65 },
  { metric: "Response", james: 72, sarah: 88, tom: 76 },
  { metric: "Forecast", james: 80, sarah: 65, tom: 58 },
];

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border border-border bg-popover px-3 py-2 text-xs" style={{ fontFamily: "var(--font-mono)" }}>
      {label && <p className="text-muted-foreground mb-1">{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || p.fill }}>
          {p.name}: {typeof p.value === "number" && p.value > 1000 ? `$${(p.value / 1000).toFixed(0)}k` : p.value}
        </p>
      ))}
    </div>
  );
};

type Period = "MTD" | "QTD" | "YTD";

export function Analytics() {
  const [period, setPeriod] = useState<Period>("YTD");

  const totalRevenue = revenueMonthly.reduce((s, m) => s + m.revenue, 0);
  const totalLeads = revenueMonthly.reduce((s, m) => s + m.leads, 0);
  const totalDeals = revenueMonthly.reduce((s, m) => s + m.deals, 0);
  const avgDeal = Math.round(totalRevenue / totalDeals);

  const kpis = [
    { label: "Total Revenue", value: `$${(totalRevenue / 1000).toFixed(0)}k`, change: "+18.4%", up: true, icon: DollarSign, color: "#00d4aa" },
    { label: "Total Leads", value: totalLeads, change: "+11.2%", up: true, icon: Users, color: "#4f7eff" },
    { label: "Deals Closed", value: totalDeals, change: "-1", up: false, icon: Target, color: "#f59e0b" },
    { label: "Avg Deal Size", value: `$${(avgDeal / 1000).toFixed(0)}k`, change: "+6.7%", up: true, icon: Award, color: "#a78bfa" },
  ];

  return (
    <div className="p-6 space-y-6 min-h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-foreground">Analytics & Reporting</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Performance data · June 2026</p>
        </div>
        <div className="flex items-center gap-1 border border-border rounded overflow-hidden">
          {(["MTD", "QTD", "YTD"] as Period[]).map(p => (
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
              <span className="text-[11px] text-muted-foreground">vs prior period</span>
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
              <p className="text-[11px] text-muted-foreground">Monthly trend · 2026</p>
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
              <YAxis yAxisId="left" tick={{ fill: "#6b7694", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} tickFormatter={v => `$${v / 1000}k`} />
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
          <p className="text-[11px] text-muted-foreground mb-3">Distribution · YTD</p>
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
                {leadSources.map(s => <Cell key={s.name} fill={s.color} />)}
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
          <div className="space-y-1.5 mt-2">
            {leadSources.map(s => (
              <div key={s.name} className="flex items-center justify-between">
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
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
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
                      background: ["#6b7694", "#4f7eff", "#a78bfa", "#f59e0b", "#00d4aa"][i],
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

        {/* Team radar */}
        <div className="rounded border border-border bg-card p-4">
          <p className="text-xs font-semibold text-foreground mb-1">Team Performance Radar</p>
          <p className="text-[11px] text-muted-foreground mb-1">6 KPI dimensions · normalized</p>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "#6b7694", fontSize: 9, fontFamily: "var(--font-mono)" }} />
              <Radar name="James" dataKey="james" stroke="#4f7eff" fill="#4f7eff" fillOpacity={0.15} strokeWidth={1.5} />
              <Radar name="Sarah" dataKey="sarah" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.12} strokeWidth={1.5} />
              <Radar name="Tom" dataKey="tom" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.1} strokeWidth={1.5} />
              <Tooltip content={<ChartTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-4 text-[10px] font-mono">
            {[["James", "#4f7eff"], ["Sarah", "#00d4aa"], ["Tom", "#f59e0b"]].map(([n, c]) => (
              <span key={n} className="flex items-center gap-1 text-muted-foreground">
                <span className="w-2 h-2 rounded-full" style={{ background: c as string }} />{n}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Team table */}
      <div className="rounded border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <p className="text-xs font-semibold text-foreground">Rep Performance · {period}</p>
        </div>
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-border bg-secondary/30">
              {["Rep", "Calls", "Emails", "Deals", "Revenue", "Win Rate", "Quota Attainment"].map(h => (
                <th key={h} className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {teamPerformance.map((rep, i) => {
              const attainment = Math.round((rep.revenue / rep.quota) * 100);
              return (
                <tr key={rep.name} className="border-b border-border last:border-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-mono font-semibold text-primary">
                        {rep.name.split(" ").map(n => n[0]).join("")}
                      </div>
                      <span className="font-medium text-foreground">{rep.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-muted-foreground">{rep.calls}</td>
                  <td className="px-4 py-3 font-mono text-muted-foreground">{rep.emails}</td>
                  <td className="px-4 py-3 font-mono text-foreground font-semibold">{rep.deals}</td>
                  <td className="px-4 py-3 font-mono font-semibold text-foreground">${(rep.revenue / 1000).toFixed(0)}k</td>
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
          </tbody>
        </table>
      </div>
    </div>
  );
}
