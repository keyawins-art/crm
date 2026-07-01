import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, Building2 } from "lucide-react";
import { accountsAPI } from "../../lib/api";

const industryColors: Record<string, string> = {
  technology: "#4f7eff",
  finance: "#00d4aa",
  healthcare: "#a78bfa",
  education: "#f59e0b",
  manufacturing: "#f43f5e",
  retail: "#10b981",
  real_estate: "#6366f1",
  other: "#6b7694",
};

export function Accounts() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [selectedAccount, setSelectedAccount] = useState<any | null>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [newNote, setNewNote] = useState("");
  const [loadingActivities, setLoadingActivities] = useState(false);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addFormData, setAddFormData] = useState({
    name: "",
    industry: "technology",
    type: "prospect",
    phone: "",
    email: "",
    gst_number: "",
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const res = await accountsAPI.list(1, 50);
      setAccounts(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load accounts:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = accounts.filter(a => {
    const q = search.toLowerCase();
    return !q || a.name?.toLowerCase().includes(q) || a.industry?.toLowerCase().includes(q);
  });

  const loadActivities = async (accountId: string) => {
    try {
      setLoadingActivities(true);
      const res = await accountsAPI.activities(accountId);
      setActivities(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingActivities(false);
    }
  };

  const handleSelectAccount = (acc: any) => {
    setSelectedAccount(acc);
    loadActivities(acc.id);
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim() || !selectedAccount) return;
    try {
      await accountsAPI.addActivity(selectedAccount.id, {
        activity_type: "call",
        content: newNote,
      });
      setNewNote("");
      loadActivities(selectedAccount.id);
    } catch (err) {
      console.error(err);
      alert("Failed to add note");
    }
  };

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await accountsAPI.create(addFormData);
      setIsAddModalOpen(false);
      setAddFormData({ name: "", industry: "technology", type: "prospect", phone: "", email: "", gst_number: "" });
      loadAccounts();
    } catch (err) {
      console.error(err);
      alert("Failed to add account");
    }
  };

  const fmt = (v: number | null) => v ? (v >= 1000000 ? `₹${(v / 1000000).toFixed(1)}M` : `₹${(v / 1000).toFixed(0)}k`) : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search accounts…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground">{total} accounts</span>
          <button onClick={() => setIsAddModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> Add Account
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Account</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Industry</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Type</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Revenue</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Website</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(acc => {
                const indColor = industryColors[acc.industry] || "#6b7694";
                return (
                  <tr key={acc.id} onClick={() => handleSelectAccount(acc)} className="cursor-pointer border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-primary/10 flex items-center justify-center shrink-0">
                          <Building2 size={13} className="text-primary" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{acc.name}</p>
                          {acc.email && <p className="text-[10px] text-muted-foreground">{acc.email}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      {acc.industry ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium"
                          style={{ color: indColor, background: indColor + "18" }}>
                          {acc.industry}
                        </span>
                      ) : <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-muted-foreground capitalize">{acc.type || "—"}</td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{fmt(acc.annual_revenue)}</td>
                    <td className="px-3 py-2.5 text-muted-foreground">{acc.website || "—"}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {acc.created_at ? new Date(acc.created_at).toLocaleDateString() : "—"}
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
            <Building2 size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No accounts found</p>
          </div>
        )}
      </div>

      {/* Detail Sidebar */}
      {selectedAccount && (
        <div className="w-80 border-l border-border bg-card flex flex-col shrink-0 animate-in slide-in-from-right-8 duration-200">
          <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
            <h3 className="font-semibold text-foreground text-sm">Account Details</h3>
            <button onClick={() => setSelectedAccount(null)} className="text-muted-foreground hover:text-foreground">✕</button>
          </div>
          <div className="p-4 flex flex-col gap-4 overflow-y-auto flex-1">
            <div className="flex flex-col gap-2">
              <h2 className="text-lg font-bold text-foreground">{selectedAccount.name}</h2>
              <div className="text-xs text-muted-foreground space-y-1">
                <p><span className="font-semibold text-foreground">Type:</span> <span className="capitalize">{selectedAccount.type}</span></p>
                <p><span className="font-semibold text-foreground">Industry:</span> <span className="capitalize">{selectedAccount.industry || "—"}</span></p>
                <p><span className="font-semibold text-foreground">Phone:</span> {selectedAccount.phone || "—"}</p>
                <p><span className="font-semibold text-foreground">Email:</span> {selectedAccount.email || "—"}</p>
                <p><span className="font-semibold text-foreground">GST No:</span> <span className="font-mono text-primary">{selectedAccount.gst_number || "—"}</span></p>
              </div>
            </div>

            <hr className="border-border" />
            
            <div className="flex-1 flex flex-col min-h-[300px]">
              <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-3">Activity & Notes</h4>
              
              <form onSubmit={handleAddNote} className="mb-4">
                <textarea 
                  value={newNote} 
                  onChange={e => setNewNote(e.target.value)} 
                  placeholder="Log a call or meeting..."
                  className="w-full text-xs p-2 bg-secondary/30 border border-border rounded focus:outline-none focus:border-primary resize-none h-20 text-foreground"
                />
                <button type="submit" disabled={!newNote.trim()} className="mt-2 w-full py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50 transition-colors">
                  Save Note
                </button>
              </form>

              <div className="flex-1 overflow-y-auto pr-1 space-y-3">
                {loadingActivities ? (
                  <p className="text-xs text-muted-foreground text-center py-4">Loading...</p>
                ) : activities.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">No activities yet.</p>
                ) : (
                  activities.map(act => (
                    <div key={act.id} className="text-xs p-3 rounded border border-border bg-secondary/10">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-primary capitalize">{act.activity_type}</span>
                        <span className="text-[10px] text-muted-foreground">{new Date(act.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-muted-foreground whitespace-pre-wrap">{act.content}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      </div>

      {/* Add Account Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">New Account</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors">✕</button>
            </div>
            <form onSubmit={handleAddAccount} className="p-4 flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Account Name</label>
                <input required value={addFormData.name} onChange={e => setAddFormData({...addFormData, name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Acme Corp" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Email</label>
                  <input type="email" value={addFormData.email} onChange={e => setAddFormData({...addFormData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="hello@acme.com" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Phone</label>
                  <input value={addFormData.phone} onChange={e => setAddFormData({...addFormData, phone: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="+91 9876543210" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">GST Number</label>
                <input value={addFormData.gst_number} onChange={e => setAddFormData({...addFormData, gst_number: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" placeholder="22AAAAA0000A1Z5" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Industry</label>
                  <select value={addFormData.industry} onChange={e => setAddFormData({...addFormData, industry: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {Object.keys(industryColors).map(i => <option key={i} value={i}>{i.replace("_", " ")}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Type</label>
                  <select value={addFormData.type} onChange={e => setAddFormData({...addFormData, type: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {["prospect", "customer", "partner", "vendor"].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end gap-2 mt-2 pt-4 border-t border-border">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Cancel</button>
                <button type="submit" className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">Create Account</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
