import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, FileText, IndianRupee } from "lucide-react";
import { salesAPI } from "../../lib/api";

const statusConfig: Record<string, { color: string; bg: string }> = {
  draft:          { color: "#6b7694", bg: "#6b769418" },
  sent:           { color: "#4f7eff", bg: "#4f7eff18" },
  partially_paid: { color: "#f59e0b", bg: "#f59e0b18" },
  paid:           { color: "#00d4aa", bg: "#00d4aa18" },
  overdue:        { color: "#f43f5e", bg: "#f43f5e18" },
  cancelled:      { color: "#6b7694", bg: "#6b769418" },
};

export function Invoices() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const res = await salesAPI.invoices(1, 50);
      setInvoices(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load invoices:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = invoices.filter(inv => {
    const q = search.toLowerCase();
    return !q || inv.invoice_number?.toLowerCase().includes(q);
  });

  const fmt = (v: number | null) => v != null ? `₹${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search invoices…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground">{total} invoices</span>
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Invoice #</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Total</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Paid</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Due Date</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(inv => {
                const st = statusConfig[inv.status] || statusConfig.draft;
                return (
                  <tr key={inv.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-chart-3/10 flex items-center justify-center shrink-0">
                          <FileText size={13} style={{ color: "#f59e0b" }} />
                        </div>
                        <span className="font-mono font-medium text-foreground">{inv.invoice_number}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize"
                        style={{ color: st.color, background: st.bg }}>
                        {inv.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{fmt(inv.total_amount)}</td>
                    <td className="px-3 py-2.5 font-mono text-muted-foreground">{fmt(inv.amount_paid)}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {inv.due_date ? new Date(inv.due_date).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-primary border border-primary/30 rounded hover:bg-primary/10 transition-colors">
                        <IndianRupee size={10} /> Pay
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <FileText size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No invoices found</p>
          </div>
        )}
      </div>
    </div>
  );
}
