import { useState, useEffect } from "react";
import {
  Search, Plus, MoreHorizontal, TrendingUp,
  ChevronUp, ChevronDown, ArrowRight, Filter, UserPlus
} from "lucide-react";
import { leadsAPI, usersAPI } from "../../lib/api";

type LeadStatus = "new" | "assigned" | "in_process" | "converted" | "recycled" | "dead";

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  new:        { color: "#4f7eff", bg: "#4f7eff18", label: "New" },
  assigned:   { color: "#a78bfa", bg: "#a78bfa18", label: "Assigned" },
  in_process: { color: "#f59e0b", bg: "#f59e0b18", label: "In Process" },
  converted:  { color: "#10b981", bg: "#10b98118", label: "Converted" },
  recycled:   { color: "#6b7694", bg: "#6b769418", label: "Recycled" },
  dead:       { color: "#f43f5e", bg: "#f43f5e18", label: "Dead" },
};

export function Leads() {
  const [leads, setLeads] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState("All");
  const [users, setUsers] = useState<any[]>([]);

  const statuses = ["All", "new", "assigned", "in_process", "converted", "recycled", "dead"];

  // Add Lead Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addFormData, setAddFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    company: "",
    status: "new",
    assigned_to_id: "",
  });

  useEffect(() => {
    loadLeads();
    loadUsers();
  }, [page]);

  const loadUsers = async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data.items || res.data || []);
    } catch (err) {
      console.error("Failed to load users", err);
    }
  };

  const loadLeads = async () => {
    try {
      setLoading(true);
      const res = await leadsAPI.list(page, 20);
      setLeads(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load leads:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = { ...addFormData };
      if (!payload.assigned_to_id) {
        delete (payload as any).assigned_to_id;
      }
      await leadsAPI.create(payload);
      setIsAddModalOpen(false);
      setAddFormData({ first_name: "", last_name: "", email: "", company: "", status: "new", assigned_to_id: "" });
      loadLeads();
    } catch (err) {
      console.error("Failed to create lead:", err);
      alert("Failed to create lead. Please try again.");
    }
  };

  const filtered = leads.filter(l => {
    const q = search.toLowerCase();
    const name = `${l.first_name || ""} ${l.last_name || ""}`.toLowerCase();
    const matchSearch = !q || name.includes(q) || (l.email || "").toLowerCase().includes(q) || (l.company || "").toLowerCase().includes(q);
    const matchStatus = statusFilter === "All" || l.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search leads…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64"
          />
        </div>

        <div className="flex items-center gap-1 border border-border rounded overflow-hidden">
          {statuses.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-2.5 py-1.5 text-[11px] font-medium transition-colors ${statusFilter === s ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground hover:bg-white/5"}`}
            >
              {s === "All" ? "All" : statusConfig[s]?.label || s}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => setIsAddModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> Add Lead
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6 px-6 py-2.5 border-b border-border bg-secondary/30 text-[11px] font-mono text-muted-foreground">
        <span>{total} total</span>
        <span className="ml-auto text-muted-foreground/50">{filtered.length} shown</span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Name</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Email</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Company</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Assigned To</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(lead => {
                const st = statusConfig[lead.status] || statusConfig.new;
                const initials = `${(lead.first_name || "?")[0]}${(lead.last_name || "?")[0]}`.toUpperCase();
                const assignedUser = users.find(u => u.id === lead.assigned_to_id);
                return (
                  <tr key={lead.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-mono font-semibold text-primary shrink-0">
                          {initials}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{lead.first_name} {lead.last_name}</p>
                          {lead.title && <p className="text-[10px] text-muted-foreground">{lead.title}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-muted-foreground">{lead.email || "—"}</td>
                    <td className="px-3 py-2.5 text-muted-foreground">{lead.company || "—"}</td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ color: st.color, background: st.bg }}>
                        {st.label}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-muted-foreground">
                      {assignedUser ? (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-secondary/50 text-[10px] font-medium text-foreground">
                          <span className="w-3 h-3 rounded-full bg-primary/20 flex items-center justify-center text-[7px] text-primary">{assignedUser.first_name[0]}{assignedUser.last_name[0]}</span>
                          {assignedUser.first_name}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : "—"}
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
            <UserPlus size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No leads found</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Try adjusting your search or create a new lead</p>
          </div>
        )}
      </div>

      {/* Add Lead Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">New Lead</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors">
                ✕
              </button>
            </div>
            <form onSubmit={handleAddLead} className="p-4 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">First Name</label>
                  <input required value={addFormData.first_name} onChange={e => setAddFormData({...addFormData, first_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="John" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Last Name</label>
                  <input required value={addFormData.last_name} onChange={e => setAddFormData({...addFormData, last_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Doe" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
                <input required type="email" value={addFormData.email} onChange={e => setAddFormData({...addFormData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="john@example.com" />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Company</label>
                <input required value={addFormData.company} onChange={e => setAddFormData({...addFormData, company: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Acme Corp" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Status</label>
                  <select value={addFormData.status} onChange={e => setAddFormData({...addFormData, status: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {statuses.filter(s => s !== "All").map(s => <option key={s} value={s}>{statusConfig[s]?.label || s}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Assigned To</label>
                  <select value={addFormData.assigned_to_id} onChange={e => setAddFormData({...addFormData, assigned_to_id: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    <option value="">Unassigned</option>
                    {users.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name}</option>)}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-2 pt-4 border-t border-border">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
                  Create Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
