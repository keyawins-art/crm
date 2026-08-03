import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, Building2, Edit2 } from "lucide-react";
import { accountsAPI, usersAPI, productsAPI } from "../../lib/api";
import { Customer360Modal } from "./Customer360Modal";

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
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  
  const getInitialFormState = () => ({
    name: "",
    contact_name: "",
    type: "prospect",
    industry: "manufacturing",
    phone: "",
    email: "",
    gst_number: "",
    billing_city: "",
    billing_state: "",
    source: "exhibition",
    product_of_interest: "",
    owner_id: "",
  });

  const [addFormData, setAddFormData] = useState(getInitialFormState());
  const [editFormData, setEditFormData] = useState<any>(null);

  const handleEditClick = (e: React.MouseEvent, acc: any) => {
    e.stopPropagation();
    setEditFormData({ ...acc });
    setIsEditModalOpen(true);
  };

  const handleEditAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFormData) return;
    try {
      const payload = { ...editFormData };
      delete payload.id;
      delete payload.created_at;
      delete payload.updated_at;
      delete payload.owner;
      if (!payload.owner_id) delete payload.owner_id;
      if (!payload.email) delete payload.email;
      
      await accountsAPI.update(editFormData.id, payload);
      setIsEditModalOpen(false);
      setEditFormData(null);
      loadAccounts();
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Failed to update customer";
      alert(errMsg);
    }
  };

  useEffect(() => {
    loadAccounts();
    loadUsers();
    loadProducts();
  }, []);

  const loadUsers = async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data || []);
    } catch (err) {
      console.error("Failed to load users:", err);
    }
  };

  const loadProducts = async () => {
    try {
      const res = await productsAPI.list(1, 100);
      setProducts(res.data.items || []);
    } catch (err) {
      console.error("Failed to load products:", err);
    }
  };

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
    const q = search.trim().toLowerCase();
    if (!q) return true;
    const cleanQ = q.replace(/\D/g, "");
    const cleanPhone = (a.phone || "").replace(/\D/g, "");

    return (
      a.name?.toLowerCase().includes(q) ||
      a.contact_name?.toLowerCase().includes(q) ||
      a.email?.toLowerCase().includes(q) ||
      a.phone?.toLowerCase().includes(q) ||
      (cleanQ.length > 2 && cleanPhone.includes(cleanQ)) ||
      a.gst_number?.toLowerCase().includes(q) ||
      a.pan_number?.toLowerCase().includes(q) ||
      a.billing_city?.toLowerCase().includes(q) ||
      a.billing_state?.toLowerCase().includes(q) ||
      a.billing_street?.toLowerCase().includes(q) ||
      a.billing_pincode?.toLowerCase().includes(q) ||
      a.product_of_interest?.toLowerCase().includes(q) ||
      a.source?.toLowerCase().includes(q) ||
      a.type?.toLowerCase().includes(q)
    );
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
      const payload = { ...addFormData };
      if (!payload.owner_id) delete (payload as any).owner_id;
      if (!payload.email) delete (payload as any).email;
      await accountsAPI.create(payload);
      setIsAddModalOpen(false);
      setAddFormData(getInitialFormState());
      loadAccounts();
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Failed to add customer";
      alert(errMsg);
    }
  };

  const fmt = (v: number | null) => v ? (v >= 1000000 ? `₹${(v / 1000000).toFixed(1)}M` : `₹${(v / 1000).toFixed(0)}k`) : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search customers…"
            className="pl-8 pr-3 py-1.5 text-xs bg-secondary/40 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground">{total} customers</span>
          <button onClick={() => setIsAddModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> Add Customer
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Company Name</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Contact Person</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Type</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Location</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Phone / Email</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">GST No.</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Source</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Assignee</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Product of Interest</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(acc => {
                const assignedUser = users.find(u => u.id === acc.owner_id);
                const assigneeName = assignedUser ? `${assignedUser.first_name} ${assignedUser.last_name || ""}` : "Unassigned";
                return (
                  <tr key={acc.id} onClick={() => handleSelectAccount(acc)} className="cursor-pointer border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-primary/10 flex items-center justify-center shrink-0">
                          <Building2 size={13} className="text-primary" />
                        </div>
                        <span className="font-semibold text-foreground">{acc.name}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-foreground">{acc.contact_name || "—"}</td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary capitalize">
                        {acc.type || "prospect"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-muted-foreground">
                      {acc.billing_city ? `${acc.billing_city}${acc.billing_state ? ", " + acc.billing_state : ""}` : "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex flex-col">
                        {acc.phone ? (
                          <a href={`tel:${acc.phone}`} className="text-foreground hover:text-primary transition-colors cursor-pointer" onClick={(e) => e.stopPropagation()}>{acc.phone}</a>
                        ) : (
                          <span className="text-foreground">—</span>
                        )}
                        {acc.email && <span className="text-[10px] text-muted-foreground">{acc.email}</span>}
                      </div>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-primary font-semibold">{acc.gst_number || "—"}</td>
                    <td className="px-3 py-2.5 text-muted-foreground capitalize">{acc.source || "—"}</td>
                    <td className="px-3 py-2.5 text-muted-foreground">{assigneeName}</td>
                    <td className="px-3 py-2.5 text-foreground font-medium">{acc.product_of_interest || "—"}</td>
                    <td className="px-3 py-2.5 flex items-center gap-2">
                      <button onClick={(e) => handleEditClick(e, acc)} className="text-muted-foreground hover:text-primary transition-colors" title="Edit Customer">
                        <Edit2 size={14} />
                      </button>
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
            <p className="text-sm font-medium text-muted-foreground">No customers found</p>
          </div>
        )}
      </div>

      {/* Detail Sidebar replaced by Customer 360 Modal */}
      {selectedAccount && (
        <Customer360Modal 
          account={selectedAccount} 
          users={users} 
          onClose={() => setSelectedAccount(null)} 
        />
      )}
      </div>

      {/* Add Customer Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">New Customer</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors">✕</button>
            </div>
            <form onSubmit={handleAddAccount} className="p-6 flex-1 overflow-y-auto flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Company Name</label>
                  <input required value={addFormData.name} onChange={e => setAddFormData({...addFormData, name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Keya Industries" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Customer Name (Contact Person)</label>
                  <input required value={addFormData.contact_name} onChange={e => setAddFormData({...addFormData, contact_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Rakesh Patel" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Company Type</label>
                  <select value={addFormData.type} onChange={e => setAddFormData({...addFormData, type: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {["prospect", "customer", "partner", "vendor"].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">GST Number</label>
                  <input value={addFormData.gst_number} onChange={e => setAddFormData({...addFormData, gst_number: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" placeholder="24AAECK0154G1ZZ" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Phone</label>
                  <input value={addFormData.phone} onChange={e => setAddFormData({...addFormData, phone: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="+91 9876543210" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Email</label>
                  <input type="email" value={addFormData.email} onChange={e => setAddFormData({...addFormData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="client@company.com" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Location (City)</label>
                  <input value={addFormData.billing_city} onChange={e => setAddFormData({...addFormData, billing_city: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Vadodara" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Location (State)</label>
                  <input value={addFormData.billing_state} onChange={e => setAddFormData({...addFormData, billing_state: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Gujarat" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Source</label>
                  <select value={addFormData.source} onChange={e => setAddFormData({...addFormData, source: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {["exhibition", "website", "cold_call", "referral", "other"].map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Customer Assignee (Assigned To)</label>
                  <select value={addFormData.owner_id} onChange={e => setAddFormData({...addFormData, owner_id: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                    <option value="">Select Assignee</option>
                    {users.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name || ""}</option>)}
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Product of Interest</label>
                <select value={addFormData.product_of_interest} onChange={e => setAddFormData({...addFormData, product_of_interest: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                  <option value="">Select Product Model</option>
                  {products.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
                </select>
              </div>
              
              <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-border shrink-0">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">Create Customer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {isEditModalOpen && editFormData && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">Edit Customer</h3>
              <button onClick={() => { setIsEditModalOpen(false); setEditFormData(null); }} className="text-muted-foreground hover:text-foreground transition-colors">✕</button>
            </div>
            <form onSubmit={handleEditAccount} className="p-6 flex-1 overflow-y-auto flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Company Name</label>
                  <input required value={editFormData.name} onChange={e => setEditFormData({...editFormData, name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Keya Industries" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Customer Name (Contact Person)</label>
                  <input required value={editFormData.contact_name || ""} onChange={e => setEditFormData({...editFormData, contact_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Rakesh Patel" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Company Type</label>
                  <select value={editFormData.type || "prospect"} onChange={e => setEditFormData({...editFormData, type: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {["prospect", "customer", "partner", "vendor"].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">GST Number</label>
                  <input value={editFormData.gst_number || ""} onChange={e => setEditFormData({...editFormData, gst_number: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" placeholder="24AAECK0154G1ZZ" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Phone</label>
                  <input value={editFormData.phone || ""} onChange={e => setEditFormData({...editFormData, phone: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="+91 9876543210" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Email</label>
                  <input type="email" value={editFormData.email || ""} onChange={e => setEditFormData({...editFormData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="client@company.com" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Location (City)</label>
                  <input value={editFormData.billing_city || ""} onChange={e => setEditFormData({...editFormData, billing_city: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Vadodara" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Location (State)</label>
                  <input value={editFormData.billing_state || ""} onChange={e => setEditFormData({...editFormData, billing_state: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Gujarat" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Source</label>
                  <select value={editFormData.source || "exhibition"} onChange={e => setEditFormData({...editFormData, source: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {["exhibition", "website", "cold_call", "referral", "other"].map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Customer Assignee (Assigned To)</label>
                  <select value={editFormData.owner_id || ""} onChange={e => setEditFormData({...editFormData, owner_id: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                    <option value="">Select Assignee</option>
                    {users.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name || ""}</option>)}
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Product of Interest</label>
                <select value={editFormData.product_of_interest || ""} onChange={e => setEditFormData({...editFormData, product_of_interest: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                  <option value="">Select Product Model</option>
                  {products.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
                </select>
              </div>
              
              <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-border shrink-0">
                <button type="button" onClick={() => { setIsEditModalOpen(false); setEditFormData(null); }} className="px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
