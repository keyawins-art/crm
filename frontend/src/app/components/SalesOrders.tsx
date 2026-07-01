import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, ShoppingCart, Send } from "lucide-react";
import { salesAPI } from "../../lib/api";

const statusConfig: Record<string, { color: string; bg: string }> = {
  draft:      { color: "#6b7694", bg: "#6b769418" },
  confirmed:  { color: "#4f7eff", bg: "#4f7eff18" },
  processing: { color: "#f59e0b", bg: "#f59e0b18" },
  shipped:    { color: "#00d4aa", bg: "#00d4aa18" },
  delivered:  { color: "#00d4aa", bg: "#00d4aa18" },
  cancelled:  { color: "#f43f5e", bg: "#f43f5e18" },
};

export function SalesOrders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const res = await salesAPI.salesOrders(1, 50);
      setOrders(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToInvoice = async (id: string) => {
    if (!window.confirm("Convert this Sales Order to an Invoice?")) return;
    try {
      await salesAPI.convertToInvoice(id);
      loadOrders();
      alert("Converted successfully!");
    } catch (err) {
      console.error("Failed to convert to invoice:", err);
      alert("Failed to convert.");
    }
  };

  const filtered = orders.filter(o => {
    const term = search.toLowerCase();
    return !term || o.order_number?.toLowerCase().includes(term);
  });

  const fmt = (v: number | null) => v != null ? `₹${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search sales orders…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} orders</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Order
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Order #</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Total</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-20 px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(o => {
                const st = statusConfig[o.status] || statusConfig.draft;
                return (
                  <tr key={o.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-indigo-500/10 flex items-center justify-center shrink-0">
                          <ShoppingCart size={13} className="text-indigo-500" />
                        </div>
                        <span className="font-mono font-medium text-foreground">{o.order_number}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize"
                        style={{ color: st.color, background: st.bg }}>
                        {o.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{fmt(o.grand_total)}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {o.created_at ? new Date(o.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      {o.status === 'confirmed' || o.status === 'delivered' ? (
                        <button onClick={() => handleConvertToInvoice(o.id)} title="Convert to Invoice" className="text-emerald-500 hover:text-emerald-400 mr-2">
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
