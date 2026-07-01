import { useState, useEffect } from "react";
import {
  Plus, MoreHorizontal, TrendingUp, IndianRupee,
  Calendar, User2, ChevronRight, Search, SlidersHorizontal,
  ArrowUpRight, Clock, Target
} from "lucide-react";
import { opportunitiesAPI } from "../../lib/api";

type Stage = "Prospecting" | "Qualification" | "Proposal" | "Negotiation" | "Closed Won" | "Closed Lost";

type Deal = {
  id: string;
  name: string;
  amount: number;
  stage: Stage;
  probability: number;
  close_date: string;
  account_id?: string;
  contact_id?: string;
  created_at: string;
};

const stageConfig: Record<string, { color: string; bg: string; border: string }> = {
  "Prospecting":  { color: "#6b7694", bg: "#6b769410", border: "#6b769430" },
  "Qualification":{ color: "#4f7eff", bg: "#4f7eff10", border: "#4f7eff30" },
  "Proposal":     { color: "#a78bfa", bg: "#a78bfa10", border: "#a78bfa30" },
  "Negotiation":  { color: "#f59e0b", bg: "#f59e0b10", border: "#f59e0b30" },
  "Closed Won":   { color: "#00d4aa", bg: "#00d4aa10", border: "#00d4aa30" },
  "Closed Lost":  { color: "#f43f5e", bg: "#f43f5e10", border: "#f43f5e30" },
};

const stages: Stage[] = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"];

const fmt = (v: number | null | undefined) => {
  if (v == null) return "₹0";
  return v >= 1000000 ? `₹${(v / 1000000).toFixed(1)}M` : `₹${(v / 1000).toFixed(0)}k`;
};

export function Deals() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);

  useEffect(() => {
    loadDeals();
  }, []);

  const loadDeals = async () => {
    try {
      setLoading(true);
      const res = await opportunitiesAPI.list(1, 100);
      setDeals(res.data.items || []);
    } catch (err) {
      console.error("Failed to load deals:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = deals.filter(d => {
    const q = search.toLowerCase();
    return !q || d.name?.toLowerCase().includes(q);
  });

  const byStage = (s: string) => filtered.filter(d => d.stage === s);

  const totalPipeline = deals
    .filter(d => d.stage !== "Closed Won" && d.stage !== "Closed Lost")
    .reduce((sum, d) => sum + (d.amount || 0), 0);

  const weightedPipeline = deals
    .filter(d => d.stage !== "Closed Lost")
    .reduce((sum, d) => sum + ((d.amount || 0) * (d.probability || 0)) / 100, 0);

  const closedWon = deals.filter(d => d.stage === "Closed Won").reduce((sum, d) => sum + (d.amount || 0), 0);

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search deals…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-56"
          />
        </div>
        <button className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-muted-foreground border border-border rounded hover:text-foreground transition-colors">
          <SlidersHorizontal size={12} /> Filter
        </button>
        <div className="ml-auto flex items-center gap-4 text-[11px] font-mono">
          <span className="text-muted-foreground">Pipeline: <span className="text-foreground font-semibold">{fmt(totalPipeline)}</span></span>
          <span className="text-muted-foreground">Weighted: <span style={{ color: "#4f7eff" }} className="font-semibold">{fmt(weightedPipeline)}</span></span>
          <span className="text-muted-foreground">Won: <span style={{ color: "#00d4aa" }} className="font-semibold">{fmt(closedWon)}</span></span>
        </div>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
          <Plus size={12} /> New Deal
        </button>
      </div>

      {/* Kanban */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="flex gap-3 p-5 h-full min-w-max">
            {stages.map(stage => {
              const stageDeals = byStage(stage);
              const conf = stageConfig[stage] || stageConfig["Prospecting"];
              const stageTotal = stageDeals.reduce((s, d) => s + (d.amount || 0), 0);

              return (
                <div key={stage} className="flex flex-col w-64 h-full">
                  {/* Column header */}
                  <div className="flex items-center justify-between px-3 py-2.5 rounded-t border border-b-0 mb-0" style={{ borderColor: conf.border, background: conf.bg }}>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ background: conf.color }} />
                      <span className="text-xs font-semibold capitalize" style={{ color: conf.color }}>{stage.replace("_", " ")}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-mono text-muted-foreground">{stageDeals.length}</span>
                      <button className="text-muted-foreground hover:text-foreground transition-colors">
                        <Plus size={12} />
                      </button>
                    </div>
                  </div>

                  {stageTotal > 0 && (
                    <div className="px-3 py-1.5 border-x border-border bg-card/50 text-[10px] font-mono text-muted-foreground">
                      {fmt(stageTotal)} total value
                    </div>
                  )}

                  {/* Cards */}
                  <div className="flex-1 overflow-y-auto border border-t-0 border-border rounded-b bg-secondary/20 p-2 space-y-2">
                    {stageDeals.map(deal => (
                      <button
                        key={deal.id}
                        onClick={() => setSelectedDeal(selectedDeal?.id === deal.id ? null : deal)}
                        className={`w-full text-left rounded border p-3 transition-all cursor-pointer ${
                          selectedDeal?.id === deal.id
                            ? "border-primary/40 bg-primary/5"
                            : "border-border bg-card hover:border-border/80 hover:bg-card/80"
                        }`}
                      >
                        <p className="text-xs font-medium text-foreground leading-tight mb-0.5">{deal.name}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-sm font-mono font-semibold text-foreground">{fmt(deal.amount)}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ color: conf.color, background: conf.bg }}>
                            {deal.probability}%
                          </span>
                        </div>
                        <div className="h-1 rounded-full bg-white/5 mt-2 overflow-hidden">
                          <div className="h-full rounded-full transition-all" style={{ width: `${deal.probability}%`, background: conf.color }} />
                        </div>
                        <div className="flex items-center justify-between mt-2.5">
                          <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground">
                            <Calendar size={9} />
                            {deal.close_date ? new Date(deal.close_date).toLocaleDateString() : "No date"}
                          </div>
                        </div>
                      </button>
                    ))}

                    {stageDeals.length === 0 && (
                      <div className="flex items-center justify-center h-20 border border-dashed border-border/40 rounded text-[11px] text-muted-foreground/40">
                        No deals
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Deal detail panel */}
      {selectedDeal && (
        <div className="border-t border-border bg-card px-6 py-4 shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h3 className="text-sm font-semibold text-foreground">{selectedDeal.name}</h3>
                <span className="text-xs font-mono font-bold text-foreground">{fmt(selectedDeal.amount)}</span>
                <span
                  className="text-[10px] font-mono px-2 py-0.5 rounded capitalize"
                  style={{ color: (stageConfig[selectedDeal.stage] || stageConfig["Prospecting"]).color, background: (stageConfig[selectedDeal.stage] || stageConfig["Prospecting"]).bg }}
                >
                  {selectedDeal.stage.replace("_", " ")}
                </span>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-muted-foreground font-mono mt-2">
                <span><Calendar size={10} className="inline mr-1" />Close: {selectedDeal.close_date ? new Date(selectedDeal.close_date).toLocaleDateString() : "—"}</span>
                <span><TrendingUp size={10} className="inline mr-1" />{selectedDeal.probability}% probability</span>
                <span>Weighted: <span className="text-primary">{fmt((selectedDeal.amount || 0) * (selectedDeal.probability || 0) / 100)}</span></span>
              </div>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <button className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-muted-foreground border border-border rounded hover:text-foreground transition-colors">
                <ArrowUpRight size={12} /> Open
              </button>
              <button onClick={() => setSelectedDeal(null)} className="text-xs text-muted-foreground hover:text-foreground px-2 py-1.5">✕</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
