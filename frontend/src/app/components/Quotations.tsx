import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, FileText, Send } from "lucide-react";
import { quotationsAPI, salesAPI } from "../../lib/api";

const statusConfig: Record<string, { color: string; bg: string }> = {
  draft:    { color: "#6b7694", bg: "#6b769418" },
  sent:     { color: "#4f7eff", bg: "#4f7eff18" },
  accepted: { color: "#00d4aa", bg: "#00d4aa18" },
  rejected: { color: "#f43f5e", bg: "#f43f5e18" },
};

export function Quotations() {
  const [quotations, setQuotations] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadQuotations();
  }, []);

  const loadQuotations = async () => {
    try {
      setLoading(true);
      const res = await quotationsAPI.list(1, 50);
      setQuotations(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load quotations:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToOrder = async (id: string) => {
    if (!window.confirm("Convert this quotation to a Sales Order?")) return;
    try {
      await salesAPI.convertToOrder(id);
      loadQuotations();
      alert("Converted successfully!");
    } catch (err) {
      console.error("Failed to convert to order:", err);
      alert("Failed to convert.");
    }
  };

  const filtered = quotations.filter(q => {
    const term = search.toLowerCase();
    return !term || q.quote_number?.toLowerCase().includes(term) || q.subject?.toLowerCase().includes(term);
  });

  const fmt = (v: number | null) => v != null ? `₹${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search quotations…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} quotations</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Quotation
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Quote #</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Subject</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Total</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-20 px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(q => {
                const st = statusConfig[q.status] || statusConfig.draft;
                return (
                  <tr key={q.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-blue-500/10 flex items-center justify-center shrink-0">
                          <FileText size={13} className="text-blue-500" />
                        </div>
                        <span className="font-mono font-medium text-foreground">{q.quote_number}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-foreground">{q.subject}</td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize"
                        style={{ color: st.color, background: st.bg }}>
                        {q.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{fmt(q.grand_total)}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {q.created_at ? new Date(q.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      {q.status === 'accepted' ? (
                        <button onClick={() => handleConvertToOrder(q.id)} title="Convert to Order" className="text-emerald-500 hover:text-emerald-400 mr-2">
                          <Send size={14} />
                        </button>
                      ) : null}
                      <button className="text-muted-foreground hover:text-foreground">
                        <MoreHorizontal size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
