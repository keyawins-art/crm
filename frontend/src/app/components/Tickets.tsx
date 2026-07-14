import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, LifeBuoy, MessageSquare } from "lucide-react";
import { ticketsAPI } from "../../lib/api";

const statusConfig: Record<string, { color: string; bg: string }> = {
  open:        { color: "#4f7eff", bg: "#4f7eff18" },
  in_progress: { color: "#f59e0b", bg: "#f59e0b18" },
  resolved:    { color: "#00d4aa", bg: "#00d4aa18" },
  closed:      { color: "#6b7694", bg: "#6b769418" },
};

const priorityConfig: Record<string, { color: string }> = {
  low:      { color: "#6b7694" },
  medium:   { color: "#4f7eff" },
  high:     { color: "#f59e0b" },
  critical: { color: "#f43f5e" },
};

export function Tickets() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      setLoading(true);
      const res = await ticketsAPI.list(1, 50);
      setTickets(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load tickets:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = tickets.filter(t => {
    const q = search.toLowerCase();
    return !q || t.subject?.toLowerCase().includes(q) || t.ticket_number?.toLowerCase().includes(q);
  });

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search tickets…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground">{total} tickets</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> New Ticket
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Ticket</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Subject</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Priority</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Category</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(ticket => {
                const st = statusConfig[ticket.status] || statusConfig.open;
                const pr = priorityConfig[ticket.priority] || priorityConfig.medium;
                return (
                  <tr key={ticket.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-primary/10 flex items-center justify-center shrink-0">
                          <LifeBuoy size={13} className="text-primary" />
                        </div>
                        <span className="font-mono font-medium text-foreground">{ticket.ticket_number}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-foreground font-medium max-w-xs truncate">{ticket.subject}</td>
                    <td className="px-3 py-2.5">
                      <span className="flex items-center gap-1.5 text-[11px] font-medium capitalize" style={{ color: pr.color }}>
                        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: pr.color }} />
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize"
                        style={{ color: st.color, background: st.bg }}>
                        {ticket.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-muted-foreground capitalize">{ticket.category || "—"}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString('en-GB') : "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      <button className="text-muted-foreground hover:text-foreground transition-colors">
                        <MoreHorizontal size={14} />
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
            <LifeBuoy size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No tickets found</p>
          </div>
        )}
      </div>
    </div>
  );
}
