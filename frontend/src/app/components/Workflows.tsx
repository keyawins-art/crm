import { useState, useEffect } from "react";
import { Search, GitMerge, Plus, MoreHorizontal, Trash2 } from "lucide-react";
import { workflowsAPI } from "../../lib/api";

export function Workflows() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const res = await workflowsAPI.list(1, 50);
      setWorkflows(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load workflows:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this workflow?")) return;
    try {
      await workflowsAPI.delete(id);
      loadWorkflows();
    } catch (err) {
      console.error("Failed to delete workflow:", err);
    }
  };

  const filtered = workflows.filter(w => {
    const term = search.toLowerCase();
    return !term || w.name?.toLowerCase().includes(term);
  });

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search workflows…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} rules</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Rule
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filtered.map(w => (
              <div key={w.id} className="flex flex-col p-4 rounded border border-border bg-card">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded bg-fuchsia-500/10 flex items-center justify-center">
                      <GitMerge size={16} className="text-fuchsia-500" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">{w.name}</h3>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{w.entity_type} • {w.trigger_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      w.is_active ? 'bg-emerald-500/10 text-emerald-500' : 'bg-secondary text-muted-foreground'
                    }`}>
                      {w.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <button onClick={() => handleDelete(w.id)} className="text-muted-foreground hover:text-rose-500 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <div className="bg-secondary/20 rounded p-3 text-xs font-mono text-muted-foreground">
                  <div className="mb-2"><strong>IF:</strong> {w.conditions ? JSON.stringify(w.conditions) : "Always"}</div>
                  <div><strong>THEN:</strong> {w.actions ? JSON.stringify(w.actions) : "None"}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
