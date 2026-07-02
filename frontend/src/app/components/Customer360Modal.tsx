import React, { useState, useEffect } from "react";
import { X, Clock, FileText, Target, Calendar, Upload, File as FileIcon } from "lucide-react";
import { accountsAPI, opportunitiesAPI, quotationsAPI, tasksAPI, documentsAPI } from "../../lib/api";

interface Props {
  account: any;
  onClose: () => void;
  users: any[];
}

export function Customer360Modal({ account, onClose, users }: Props) {
  const [activeTab, setActiveTab] = useState<"overview" | "deals" | "tasks" | "docs">("overview");

  const [activities, setActivities] = useState<any[]>([]);
  const [deals, setDeals] = useState<any[]>([]);
  const [quotations, setQuotations] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [newNote, setNewNote] = useState("");
  const [newTask, setNewTask] = useState({ title: "", due_date: "", type: "follow_up" });

  useEffect(() => {
    loadAllData();
  }, [account.id]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [actRes, oppRes, quoteRes, taskRes, docRes] = await Promise.all([
        accountsAPI.activities(account.id).catch(() => ({ data: { items: [] } })),
        opportunitiesAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
        quotationsAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
        tasksAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
        documentsAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
      ]);

      setActivities(actRes.data.items || []);
      // Client side filtering for MVP
      setDeals((oppRes.data.items || []).filter((d: any) => d.account_id === account.id));
      setQuotations((quoteRes.data.items || []).filter((q: any) => q.account_id === account.id));
      // Assume tasks have related_account_id or similar, but for now we'll filter by title or if it has a way to link.
      // A proper CRM task has 'account_id', we will filter by it.
      setTasks((taskRes.data.items || []).filter((t: any) => t.account_id === account.id));
      setDocuments((docRes.data.items || []).filter((d: any) => d.account_id === account.id));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await accountsAPI.addActivity(account.id, { activity_type: "call", content: newNote });
      setNewNote("");
      loadAllData();
    } catch (e) {
      alert("Failed to save note");
    }
  };

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTask.title || !newTask.due_date) return;
    try {
      await tasksAPI.create({
        title: newTask.title,
        description: `Follow up for customer: ${account.name}`,
        due_date: new Date(newTask.due_date).toISOString(),
        status: "pending",
        priority: "high",
        account_id: account.id,
      });
      setNewTask({ title: "", due_date: "", type: "follow_up" });
      loadAllData();
      alert("Task scheduled in calendar!");
    } catch (e) {
      alert("Failed to schedule task");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", account.id);
    formData.append("title", file.name);
    try {
      await documentsAPI.upload(formData);
      loadAllData();
    } catch (err) {
      alert("Upload failed. Ensure backend supports document uploads for accounts.");
    }
  };

  return (
    <div className="fixed inset-0 bg-background/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/20 shrink-0">
          <div>
            <h2 className="text-xl font-bold text-foreground">{account.name}</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {account.contact_name} • {account.phone} • {account.email} • {account.billing_city}
            </p>
          </div>
          <button onClick={onClose} className="p-2 bg-secondary/50 hover:bg-secondary rounded-full transition-colors">
            <X size={16} className="text-muted-foreground" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-6 px-6 border-b border-border bg-card shrink-0">
          {[
            { id: "overview", label: "Overview & Notes", icon: Clock },
            { id: "deals", label: "Deals & Quotations", icon: Target },
            { id: "tasks", label: "Follow-ups & Calendar", icon: Calendar },
            { id: "docs", label: "Documents", icon: FileText },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-secondary/5">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <span className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Tab 1: Overview */}
              {activeTab === "overview" && (
                <div className="grid grid-cols-3 gap-6 h-full">
                  <div className="col-span-1 space-y-4">
                    <div className="p-4 bg-card border border-border rounded-lg">
                      <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Customer Details</h3>
                      <div className="space-y-2 text-sm">
                        <p className="flex justify-between"><span className="text-muted-foreground">Type:</span> <span className="capitalize">{account.type}</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">GST:</span> <span className="font-mono text-primary">{account.gst_number || "—"}</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">Product:</span> <span>{account.product_of_interest || "—"}</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">Assignee:</span> <span>{users.find(u => u.id === account.owner_id)?.first_name || "Unassigned"}</span></p>
                      </div>
                    </div>
                  </div>
                  <div className="col-span-2 flex flex-col h-full bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Conversation History</h3>
                    <form onSubmit={handleAddNote} className="mb-4 shrink-0">
                      <textarea value={newNote} onChange={e => setNewNote(e.target.value)} placeholder="Log a call or meeting..." className="w-full text-sm p-3 bg-secondary/30 border border-border rounded-md focus:outline-none focus:border-primary resize-none h-24" />
                      <div className="flex justify-end mt-2">
                        <button type="submit" disabled={!newNote.trim()} className="px-4 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50">Save Note</button>
                      </div>
                    </form>
                    <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                      {activities.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">No conversation history yet.</p>
                      ) : (
                        activities.map(act => (
                          <div key={act.id} className="text-sm p-3 rounded-md border border-border bg-secondary/20">
                            <div className="flex justify-between items-center mb-1.5">
                              <span className="font-semibold text-primary capitalize">{act.activity_type}</span>
                              <span className="text-[11px] text-muted-foreground">{new Date(act.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-foreground whitespace-pre-wrap">{act.content}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Deals & Quotes */}
              {activeTab === "deals" && (
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Linked Deals (Opportunities)</h3>
                    <div className="space-y-3">
                      {deals.length === 0 ? <p className="text-sm text-muted-foreground">No deals linked.</p> : deals.map(d => (
                        <div key={d.id} className="p-3 border border-border rounded bg-secondary/10 flex justify-between items-center">
                          <div>
                            <p className="text-sm font-semibold text-foreground">{d.name}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">₹{d.amount} • {d.stage.replace("_", " ")}</p>
                          </div>
                          <span className="px-2 py-1 bg-primary/10 text-primary text-[10px] rounded uppercase font-bold">{d.probability}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Linked Quotations</h3>
                    <div className="space-y-3">
                      {quotations.length === 0 ? <p className="text-sm text-muted-foreground">No quotations generated.</p> : quotations.map(q => (
                        <div key={q.id} className="p-3 border border-border rounded bg-secondary/10 flex justify-between items-center">
                          <div>
                            <p className="text-sm font-semibold text-foreground">{q.number}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">₹{q.total} • Valid until {new Date(q.valid_until).toLocaleDateString()}</p>
                          </div>
                          <span className={`px-2 py-1 text-[10px] rounded uppercase font-bold ${q.status === 'accepted' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'}`}>{q.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Tasks & Calendar */}
              {activeTab === "tasks" && (
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Schedule Follow-up</h3>
                    <form onSubmit={handleAddTask} className="space-y-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs text-muted-foreground">Task Title / What to discuss?</label>
                        <input required value={newTask.title} onChange={e => setNewTask({...newTask, title: e.target.value})} className="px-3 py-2 bg-secondary/30 border border-border rounded text-sm text-foreground focus:border-primary outline-none" placeholder="Call to discuss quotation" />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs text-muted-foreground">When did they ask to call? (Date & Time)</label>
                        <input required type="datetime-local" value={newTask.due_date} onChange={e => setNewTask({...newTask, due_date: e.target.value})} className="px-3 py-2 bg-secondary/30 border border-border rounded text-sm text-foreground focus:border-primary outline-none style-date-input" />
                      </div>
                      <button type="submit" className="w-full py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary/90">Add to Calendar & Tasks</button>
                    </form>
                  </div>
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Upcoming Follow-ups</h3>
                    <div className="space-y-3">
                      {tasks.length === 0 ? <p className="text-sm text-muted-foreground">No upcoming tasks.</p> : tasks.map(t => (
                        <div key={t.id} className="p-3 border border-border rounded flex flex-col gap-1">
                          <p className="text-sm font-semibold text-foreground">{t.title}</p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1"><Calendar size={12}/> {new Date(t.due_date).toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Documents */}
              {activeTab === "docs" && (
                <div className="bg-card border border-border rounded-lg p-4 h-full flex flex-col">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Customer Documents</h3>
                    <label className="cursor-pointer inline-flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary rounded text-xs font-medium hover:bg-primary/20">
                      <Upload size={14} /> Upload Document
                      <input type="file" className="hidden" onChange={handleFileUpload} />
                    </label>
                  </div>
                  <div className="grid grid-cols-4 gap-4">
                    {documents.length === 0 ? (
                      <div className="col-span-4 py-12 text-center border-2 border-dashed border-border rounded-lg">
                        <FileIcon size={32} className="mx-auto text-muted-foreground/30 mb-2" />
                        <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
                      </div>
                    ) : documents.map(doc => (
                      <div key={doc.id} className="p-4 border border-border rounded flex flex-col items-center justify-center text-center bg-secondary/10 hover:bg-secondary/20 cursor-pointer">
                        <FileIcon size={24} className="text-primary mb-2" />
                        <p className="text-xs font-medium text-foreground w-full truncate" title={doc.title || doc.filename}>{doc.title || doc.filename}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">{new Date(doc.created_at).toLocaleDateString()}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
