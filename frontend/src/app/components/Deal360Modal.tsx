import React, { useState, useEffect } from "react";
import { X, Clock, FileText, Target, Calendar } from "lucide-react";
import { opportunitiesAPI, quotationsAPI, tasksAPI, authAPI } from "../../lib/api";

interface Props {
  deal: any;
  onClose: () => void;
}

export function Deal360Modal({ deal, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<"overview" | "quotes" | "tasks">("overview");

  const [activities, setActivities] = useState<any[]>([]);
  const [quotations, setQuotations] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<any[]>([]);

  const [newNote, setNewNote] = useState("");
  const [activityDate, setActivityDate] = useState(new Date().toISOString().slice(0, 16));
  const [nextFollowUp, setNextFollowUp] = useState("");
  const [newTask, setNewTask] = useState({ title: "", due_date: "", type: "follow_up" });

  useEffect(() => {
    loadAllData();
  }, [deal.id]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [actRes, quoteRes, taskRes, userRes] = await Promise.all([
        opportunitiesAPI.activities(deal.id).catch(() => ({ data: { items: [] } })),
        quotationsAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
        tasksAPI.list(1, 100).catch(() => ({ data: { items: [] } })),
        authAPI.me().catch(() => ({ data: null })), // This only gets current user. To get all users we need users API.
      ]);

      setActivities(actRes.data.items || []);
      setQuotations((quoteRes.data.items || []).filter((q: any) => q.opportunity_id === deal.id));
      setTasks((taskRes.data.items || []).filter((t: any) => t.opportunity_id === deal.id));
      
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
      await opportunitiesAPI.addActivity(deal.id, { 
        activity_type: "call", 
        content: newNote,
        activity_date: new Date(activityDate).toISOString()
      });
      
      if (nextFollowUp) {
        await tasksAPI.create({
          title: "Follow-up Call / Meeting",
          description: newNote.substring(0, 50) + "...", 
          due_date: new Date(nextFollowUp).toISOString(),
          status: "pending",
          priority: "high",
          opportunity_id: deal.id,
        });
      }
      
      setNewNote("");
      setNextFollowUp("");
      setActivityDate(new Date().toISOString().slice(0, 16));
      loadAllData();
      alert(nextFollowUp ? "Note saved and follow-up scheduled!" : "Note saved!");
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
        description: `Follow up for Deal: ${deal.name}`,
        due_date: new Date(newTask.due_date).toISOString(),
        status: "pending",
        priority: "high",
        opportunity_id: deal.id,
      });
      setNewTask({ title: "", due_date: "", type: "follow_up" });
      loadAllData();
      alert("Task scheduled in calendar!");
    } catch (e) {
      alert("Failed to schedule task");
    }
  };

  const fmt = (val: number) => {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(val || 0);
  };

  return (
    <div className="fixed inset-0 bg-background/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/20 shrink-0">
          <div>
            <h2 className="text-xl font-bold text-foreground">{deal.name}</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {fmt(deal.amount)} • Stage: {deal.stage.replace("_", " ")} • Close Date: {new Date(deal.close_date).toLocaleDateString()}
            </p>
          </div>
          <button onClick={onClose} className="p-2 bg-secondary/50 hover:bg-secondary rounded-full transition-colors">
            <X size={16} className="text-muted-foreground" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-6 px-6 border-b border-border bg-card shrink-0">
          {[
            { id: "overview", label: "Overview & Discussion", icon: Clock },
            { id: "quotes", label: "Quotations", icon: FileText },
            { id: "tasks", label: "Follow-ups & Calendar", icon: Calendar },
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
                      <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Deal Details</h3>
                      <div className="space-y-2 text-sm">
                        <p className="flex justify-between"><span className="text-muted-foreground">Type:</span> <span className="capitalize">{deal.type?.replace("_", " ") || "—"}</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">Probability:</span> <span className="font-mono text-primary">{deal.probability || 0}%</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">Lead Source:</span> <span className="capitalize">{deal.lead_source?.replace("_", " ") || "—"}</span></p>
                        <p className="flex justify-between"><span className="text-muted-foreground">Assignee:</span> <span>{users.find(u => u.id === deal.assigned_to_id)?.first_name || users.find(u => u.id === deal.owner_id)?.first_name || "Unassigned"}</span></p>
                      </div>
                    </div>
                  </div>
                  <div className="col-span-2 flex flex-col h-full bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Discussion / Notes</h3>
                    <form onSubmit={handleAddNote} className="mb-4 shrink-0 bg-secondary/10 border border-border rounded-lg p-3">
                      <textarea value={newNote} onChange={e => setNewNote(e.target.value)} placeholder="Log a call, meeting, or general note for this deal..." className="w-full text-sm p-3 bg-card border border-border rounded-md focus:outline-none focus:border-primary resize-none h-20 mb-3" />
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <div className="flex flex-col gap-1.5">
                          <label className="text-[10px] font-semibold text-muted-foreground uppercase">When did this happen?</label>
                          <input type="datetime-local" value={activityDate} onChange={e => setActivityDate(e.target.value)} onClick={e => (e.target as any).showPicker?.()} className="px-2 py-1.5 bg-card border border-border rounded text-[11px] text-foreground focus:border-primary outline-none cursor-pointer" required />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <div className="flex justify-between items-center">
                            <label className="text-[10px] font-semibold text-muted-foreground uppercase text-primary">Next Follow-up (Optional)</label>
                            {nextFollowUp && (
                              <button type="button" onClick={() => setNextFollowUp("")} className="text-[9px] text-muted-foreground hover:text-foreground">Clear</button>
                            )}
                          </div>
                          <input type="datetime-local" value={nextFollowUp} onChange={e => setNextFollowUp(e.target.value)} onClick={e => (e.target as any).showPicker?.()} className="px-2 py-1.5 bg-card border border-border rounded text-[11px] text-foreground focus:border-primary outline-none cursor-pointer" />
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <button type="submit" disabled={!newNote.trim()} className="px-4 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50">Save & Log Activity</button>
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

              {/* Tab 2: Quotes */}
              {activeTab === "quotes" && (
                <div className="grid grid-cols-1 gap-6 max-w-3xl mx-auto w-full">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Quotations Linked to Deal</h3>
                    <div className="space-y-3">
                      {quotations.length === 0 ? <p className="text-sm text-muted-foreground">No quotations generated for this deal yet.</p> : quotations.map(q => (
                        <div key={q.id} className="p-3 border border-border rounded bg-secondary/10 flex justify-between items-center">
                          <div>
                            <p className="text-sm font-semibold text-foreground">{q.quote_number}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">₹{q.grand_total} • Valid until {q.valid_until ? new Date(q.valid_until).toLocaleDateString() : 'N/A'}</p>
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
                <div className="grid grid-cols-1 gap-6 max-w-3xl mx-auto w-full">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Upcoming Follow-ups for this Deal</h3>
                    <div className="space-y-3">
                      {tasks.length === 0 ? <p className="text-sm text-muted-foreground">No upcoming tasks.</p> : tasks.map(t => (
                        <div key={t.id} className="p-3 border border-border rounded flex flex-col gap-1">
                          <div className="flex justify-between items-start">
                            <p className="text-sm font-semibold text-foreground">{t.title}</p>
                            <span className={`px-2 py-0.5 text-[10px] rounded uppercase font-bold ${t.status === 'completed' ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'}`}>{t.status}</span>
                          </div>
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1"><Calendar size={12}/> {new Date(t.due_date).toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
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
