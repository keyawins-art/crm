import { useState, useEffect } from "react";
import {
  Search, Plus, CheckCircle2,
  Calendar, Edit2, UserPlus, MapPin, Phone, Mail, FileCheck, Sparkles, TrendingUp
} from "lucide-react";
import { leadsAPI, usersAPI, aiAPI } from "../../lib/api";

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
  const [sortByPriority, setSortByPriority] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [scoringId, setScoringId] = useState<string | null>(null);

  const statuses = ["All", "new", "assigned", "in_process", "converted", "recycled", "dead"];

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLeadId, setEditingLeadId] = useState<string | null>(null);
  
  const defaultFormData = {
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    address: "",
    status: "new",
    assigned_to_id: "",
    next_followup_date: "",
    requirements: "",
    remarks: "",
    source: ""
  };
  
  const [formData, setFormData] = useState(defaultFormData);

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

  const handleOpenAdd = () => {
    setEditingLeadId(null);
    setFormData(defaultFormData);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (lead: any) => {
    setEditingLeadId(lead.id);
    setFormData({
      first_name: lead.first_name || "",
      last_name: lead.last_name || "",
      email: lead.email || "",
      phone: lead.phone || "",
      company: lead.company || "",
      address: lead.address || "",
      status: lead.status || "new",
      assigned_to_id: lead.assigned_to_id || "",
      next_followup_date: lead.next_followup_date ? new Date(lead.next_followup_date).toISOString().split('T')[0] : "",
      requirements: lead.requirements || "",
      remarks: lead.remarks || "",
      source: lead.source || "",
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.assigned_to_id) delete (payload as any).assigned_to_id;
      if (!payload.email) delete (payload as any).email;
      if (!payload.next_followup_date) delete (payload as any).next_followup_date;
      else payload.next_followup_date = new Date(payload.next_followup_date).toISOString();

      if (editingLeadId) {
        await leadsAPI.update(editingLeadId, payload);
      } else {
        await leadsAPI.create(payload);
      }
      setIsModalOpen(false);
      setFormData(defaultFormData);
      loadLeads();
    } catch (err: any) {
      console.error("Failed to save lead:", err);
      alert(err.response?.data?.detail || "Failed to save lead. Please try again.");
    }
  };

  const filtered = [...leads].filter(l => {
    const q = search.trim().toLowerCase();
    const matchStatus = statusFilter === "All" || l.status === statusFilter;
    if (!q) return matchStatus;

    const name = `${l.first_name || ""} ${l.last_name || ""}`.toLowerCase();
    const cleanQ = q.replace(/\D/g, "");
    const cleanPhone = (l.phone || "").replace(/\D/g, "");
    const cleanMobile = (l.mobile || "").replace(/\D/g, "");

    const matchSearch = (
      name.includes(q) ||
      (l.company || "").toLowerCase().includes(q) ||
      (l.email || "").toLowerCase().includes(q) ||
      (l.phone || "").toLowerCase().includes(q) ||
      (l.mobile || "").toLowerCase().includes(q) ||
      (cleanQ.length > 2 && cleanPhone.includes(cleanQ)) ||
      (cleanQ.length > 2 && cleanMobile.includes(cleanQ)) ||
      (l.address || "").toLowerCase().includes(q) ||
      (l.requirements || "").toLowerCase().includes(q) ||
      (l.remarks || "").toLowerCase().includes(q) ||
      (l.source || "").toLowerCase().includes(q)
    );
    return matchSearch && matchStatus;
  }).sort((a, b) => {
    if (sortByPriority) {
      return (b.ai_score || 0) - (a.ai_score || 0);
    }
    return 0; // Default order from API
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
          <button 
            onClick={() => setSortByPriority(!sortByPriority)} 
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border rounded transition-colors ${sortByPriority ? "bg-primary/20 border-primary text-primary" : "bg-white/5 border-border text-foreground hover:bg-white/10"}`}
            title="Sort by AI Conversion Score"
          >
            <TrendingUp size={12} /> Priority Sort
          </button>
          <button onClick={handleOpenAdd} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> Add Lead
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6 px-6 py-2.5 border-b border-border bg-secondary/30 text-[11px] font-mono text-muted-foreground">
        <span>{total} total leads</span>
        <span className="ml-auto text-muted-foreground/50">{filtered.length} shown</span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="min-w-max">
            <table className="w-full text-xs border-collapse">
              <thead className="sticky top-0 z-10">
                <tr className="bg-card border-b border-border">
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Company & Person</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Contact Info</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Address</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Source</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status & Assignee</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Followup Date</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">AI Score</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider w-48">Requirements / Remarks</th>
                  <th className="px-4 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(lead => {
                  const st = statusConfig[lead.status] || statusConfig.new;
                  const initials = `${(lead.company || "?")[0]}`.toUpperCase();
                  const assignedUser = users.find(u => u.id === lead.assigned_to_id);
                  return (
                    <tr key={lead.id} className="border-b border-border hover:bg-white/[0.02] transition-colors align-top">
                      <td className="px-4 py-3">
                        <div className="flex items-start gap-2.5">
                          <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-[11px] font-mono font-bold text-primary shrink-0 mt-0.5">
                            {initials}
                          </div>
                          <div>
                            <p className="font-semibold text-foreground text-sm">{lead.company || "—"}</p>
                            <p className="text-[11px] text-muted-foreground mt-0.5">{lead.first_name} {lead.last_name}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex flex-col gap-1.5">
                          <div className="flex items-center gap-1.5 text-muted-foreground">
                            <Mail size={11} className="shrink-0" />
                            <span className="truncate max-w-[140px]" title={lead.email}>{lead.email || "—"}</span>
                          </div>
                          {lead.phone && (
                            <a href={`tel:${lead.phone}`} className="flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors cursor-pointer" title="Call Number">
                              <Phone size={10} />
                              <span className="text-[11px] font-mono truncate max-w-[120px]">{lead.phone}</span>
                            </a>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-start gap-1.5 text-muted-foreground">
                          <MapPin size={11} className="shrink-0 mt-0.5" />
                          <span className="line-clamp-2 max-w-[150px]" title={lead.address}>{lead.address || "—"}</span>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <span className="text-[11px] text-muted-foreground capitalize">{lead.source || "—"}</span>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex flex-col gap-2 items-start">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ color: st.color, background: st.bg }}>
                            {st.label}
                          </span>
                          {assignedUser ? (
                            <span className="inline-flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground">
                              <span className="w-3.5 h-3.5 rounded-full bg-secondary flex items-center justify-center text-[7px] text-foreground shrink-0">{assignedUser.first_name[0]}{assignedUser.last_name[0]}</span>
                              {assignedUser.first_name}
                            </span>
                          ) : (
                            <span className="text-[10px] text-muted-foreground/50">Unassigned</span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-1.5 font-mono text-[11px] text-muted-foreground">
                          <Calendar size={11} />
                          {lead.next_followup_date ? new Date(lead.next_followup_date).toLocaleDateString('en-GB') : "—"}
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex flex-col gap-1">
                          {lead.ai_score !== null && lead.ai_score !== undefined ? (
                            <div className="flex items-center gap-1.5 group relative" title={lead.ai_priority_explanation}>
                              <div className="w-full bg-secondary rounded-full h-1.5 max-w-[50px]">
                                <div className={`h-1.5 rounded-full ${lead.ai_score > 70 ? 'bg-red-500' : lead.ai_score > 30 ? 'bg-yellow-500' : 'bg-blue-500'}`} style={{ width: `${lead.ai_score}%` }}></div>
                              </div>
                              <span className="font-mono text-[10px] font-bold text-foreground">{lead.ai_score}%</span>
                              <span className="text-[10px] uppercase font-bold text-muted-foreground">
                                {lead.rating === 'hot' ? '🔥 HOT' : lead.rating === 'warm' ? '☀️ WARM' : lead.rating === 'cold' ? '❄️ COLD' : ''}
                              </span>
                            </div>
                          ) : (
                            <span className="text-[10px] text-muted-foreground/50 italic">Unscored</span>
                          )}
                          <button 
                            disabled={scoringId === lead.id}
                            onClick={async () => {
                              setScoringId(lead.id);
                              try {
                                await aiAPI.scoreLead(lead.id);
                                await loadLeads();
                              } catch(e: any) {
                                alert(e.response?.data?.detail || "Failed to score lead");
                              } finally {
                                setScoringId(null);
                              }
                            }}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 mt-1 bg-primary/10 text-primary hover:bg-primary/20 rounded text-[9px] font-bold w-fit transition-colors disabled:opacity-50"
                          >
                            <Sparkles size={10} /> {scoringId === lead.id ? "Scoring..." : "AI Score"}
                          </button>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex flex-col gap-1.5">
                          <p className="text-[10px] text-muted-foreground line-clamp-2" title={lead.requirements}>
                            <span className="font-semibold text-foreground">Needs:</span> {lead.requirements || "—"}
                          </p>
                          <p className="text-[10px] text-muted-foreground/70 line-clamp-1" title={lead.remarks}>
                            <span className="font-semibold text-muted-foreground">Remark:</span> {lead.remarks || "—"}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {!lead.is_converted && (
                            <button 
                              onClick={async () => {
                                if (window.confirm("Convert this lead to a Customer (Account & Contact) and create a Deal?")) {
                                  try {
                                    await leadsAPI.convert(lead.id, { create_opportunity: true });
                                    loadLeads();
                                    alert("Lead converted to Customer and Deal created successfully!");
                                  } catch (e: any) {
                                    alert(e.response?.data?.detail || "Failed to convert lead.");
                                  }
                                }
                              }}
                              className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 text-green-500 rounded text-[10px] font-medium transition-colors"
                            >
                              <UserPlus size={10} /> Convert
                            </button>
                          )}
                          <button 
                            onClick={() => handleOpenEdit(lead)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-white/5 hover:bg-white/10 border border-border rounded text-[10px] font-medium text-foreground transition-colors"
                          >
                            <Edit2 size={10} /> Edit
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <UserPlus size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No leads found</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Try adjusting your search or create a new lead</p>
          </div>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileCheck size={16} className="text-primary" />
                {editingLeadId ? "Edit Lead" : "New Lead"}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors">
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-5 max-h-[75vh] overflow-y-auto custom-scrollbar">
              
              {/* Primary Info */}
              <div className="space-y-4">
                <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-2">Primary Info</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Company Name</label>
                    <input required value={formData.company} onChange={e => setFormData({...formData, company: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Acme Corp" />
                  </div>
                  <div className="flex gap-4">
                    <div className="flex-1 flex flex-col gap-1.5">
                      <label className="text-[11px] font-semibold text-muted-foreground">First Name</label>
                      <input required value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="John" />
                    </div>
                    <div className="flex-1 flex flex-col gap-1.5">
                      <label className="text-[11px] font-semibold text-muted-foreground">Last Name</label>
                      <input required value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="Doe" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Contact & Address */}
              <div className="space-y-4">
                <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-2">Contact Details</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Email Address</label>
                    <input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="john@example.com" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Contact / Phone</label>
                    <input value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="+1 234 567 890" />
                  </div>
                  <div className="col-span-2 flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Address</label>
                    <textarea value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground min-h-[60px]" placeholder="Full address..." />
                  </div>
                </div>
              </div>

              {/* Status & Assignment */}
              <div className="space-y-4">
                <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-2">Tracking & Requirements</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Status</label>
                    <select value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                      {statuses.filter(s => s !== "All").map(s => <option key={s} value={s}>{statusConfig[s]?.label || s}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Lead Source</label>
                    <select value={formData.source} onChange={e => setFormData({...formData, source: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                      <option value="">Unknown Source</option>
                      <option value="whatsapp">WhatsApp</option>
                      <option value="website">Website</option>
                      <option value="referral">Referral</option>
                      <option value="direct_call">Direct Call</option>
                      <option value="instagram">Instagram</option>
                      <option value="call_inquiry">Call Inquiry</option>
                      <option value="indiamart">India Mart</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Lead Assign (Owner)</label>
                    <select value={formData.assigned_to_id} onChange={e => setFormData({...formData, assigned_to_id: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                      <option value="">Unassigned</option>
                      {users.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Follow-up Date</label>
                    <input type="date" value={formData.next_followup_date} onChange={e => setFormData({...formData, next_followup_date: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground style-date-input" />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">What its need (Requirements)</label>
                    <textarea value={formData.requirements} onChange={e => setFormData({...formData, requirements: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground min-h-[80px]" placeholder="Describe what the lead needs..." />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold text-muted-foreground">Remarks</label>
                    <textarea value={formData.remarks} onChange={e => setFormData({...formData, remarks: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground min-h-[80px]" placeholder="Any additional notes or remarks..." />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-4 pt-5 border-t border-border sticky bottom-0 bg-card">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors shadow-sm shadow-primary/20 flex items-center gap-2">
                  <CheckCircle2 size={14} />
                  {editingLeadId ? "Save Changes" : "Create Lead"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
