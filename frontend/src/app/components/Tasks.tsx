import { useState, useEffect } from "react";
import {
  Plus, Search, CheckCircle2, Circle, Clock, Calendar,
  MoreHorizontal, AlertTriangle, FileText, ArrowRight,
  Mail, Phone, Video, ListTodo, MessageSquare, X, Briefcase, User
} from "lucide-react";
import { tasksAPI, accountsAPI, contactsAPI, usersAPI } from "../../lib/api";

type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";
type TaskPriority = "low" | "medium" | "high";
type TaskType = "email" | "task" | "meeting" | "follow_up" | "call";

type Task = {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  task_type: TaskType;
  due_date?: string;
  created_at: string;
  account_id?: string;
  contact_id?: string;
  assigned_to_id?: string;
};

const priorityConfig: Record<string, { color: string; bg: string; dot: string; label: string }> = {
  high:     { color: "#f59e0b", bg: "#f59e0b15", dot: "#f59e0b", label: "High" },
  medium:   { color: "#4f7eff", bg: "#4f7eff15", dot: "#4f7eff", label: "Medium" },
  low:      { color: "#6b7694", bg: "#6b769415", dot: "#6b7694", label: "Low" },
  critical: { color: "#f43f5e", bg: "#f43f5e15", dot: "#f43f5e", label: "Critical" }, // added critical just in case
};

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  "pending":     { color: "#6b7694", bg: "#6b769415", label: "Todo" },
  "in_progress": { color: "#4f7eff", bg: "#4f7eff15", label: "In Progress" },
  "completed":   { color: "#00d4aa", bg: "#00d4aa15", label: "Done" },
  "cancelled":   { color: "#f43f5e", bg: "#f43f5e15", label: "Cancelled" },
};

const typeConfig: Record<string, { icon: any; label: string }> = {
  "email":     { icon: Mail, label: "Email" },
  "task":      { icon: ListTodo, label: "Task" },
  "meeting":   { icon: Video, label: "Meeting" },
  "follow_up": { icon: ArrowRight, label: "Follow-Up" },
  "call":      { icon: Phone, label: "Call" },
};

type Tab = "All" | "Today" | "Upcoming" | "Done" | "Overdue";

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [accountsMap, setAccountsMap] = useState<Record<string, any>>({});
  const [contactsMap, setContactsMap] = useState<Record<string, any>>({});
  const [usersMap, setUsersMap] = useState<Record<string, any>>({});
  
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("All");
  const [search, setSearch] = useState("");
  const [checked, setChecked] = useState<Set<string>>(new Set());
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formData, setFormData] = useState<any>({});
  
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tasksRes, accountsRes, contactsRes, usersRes] = await Promise.all([
        tasksAPI.list(1, 100),
        accountsAPI.list(1, 100),
        contactsAPI.list(1, 100),
        usersAPI.list()
      ]);
      
      setTasks(tasksRes.data.items || []);
      
      const accMap: any = {};
      (accountsRes.data.items || []).forEach((a: any) => accMap[a.id] = a);
      setAccountsMap(accMap);
      
      const contMap: any = {};
      (contactsRes.data.items || []).forEach((c: any) => contMap[c.id] = c);
      setContactsMap(contMap);
      
      const usrMap: any = {};
      const usersList = Array.isArray(usersRes.data) ? usersRes.data : (usersRes.data.items || []);
      usersList.forEach((u: any) => usrMap[u.id] = u);
      setUsersMap(usrMap);
      
    } catch (err) {
      console.error("Failed to load task data:", err);
    } finally {
      setLoading(false);
    }
  };

  const tabs: Tab[] = ["All", "Today", "Upcoming", "Done", "Overdue"];
  const todayStr = new Date().toISOString().split("T")[0];

  const filtered = tasks.filter(t => {
    const q = search.toLowerCase();
    const matchSearch = !q || t.title.toLowerCase().includes(q) || (t.description || "").toLowerCase().includes(q);
    if (!matchSearch) return false;
    
    const due = t.due_date ? t.due_date.split("T")[0] : null;

    switch (tab) {
      case "Today": return due === todayStr;
      case "Upcoming": return due && due > todayStr && t.status !== "completed";
      case "Done": return t.status === "completed" || checked.has(t.id);
      case "Overdue": return due && due < todayStr && t.status !== "completed";
      default: return true;
    }
  });

  const countOf = (t: Tab) => {
    switch (t) {
      case "Today": return tasks.filter(x => x.due_date && x.due_date.split("T")[0] === todayStr).length;
      case "Upcoming": return tasks.filter(x => x.due_date && x.due_date.split("T")[0] > todayStr && x.status !== "completed").length;
      case "Overdue": return tasks.filter(x => x.due_date && x.due_date.split("T")[0] < todayStr && x.status !== "completed").length;
      case "Done": return tasks.filter(x => x.status === "completed").length;
      default: return tasks.length;
    }
  };

  const toggleCheck = async (id: string, currentStatus: string) => {
    const next = new Set(checked);
    next.has(id) ? next.delete(id) : next.add(id);
    setChecked(next);
    
    try {
      const newStatus = currentStatus === "completed" ? "pending" : "completed";
      await tasksAPI.update(id, { status: newStatus });
      setTasks(tasks.map(t => t.id === id ? { ...t, status: newStatus as TaskStatus } : t));
      if (next.has(id)) next.delete(id); // uncheck visually since status is now updated
      setChecked(new Set(next));
    } catch (e) {
      console.error(e);
    }
  };

  const openModal = (task?: Task) => {
    setSelectedTask(task || null);
    if (task) {
      setFormData({
        title: task.title,
        description: task.description || "",
        priority: task.priority,
        task_type: task.task_type || "task",
        status: task.status,
        due_date: task.due_date ? task.due_date.substring(0,16) : "",
        account_id: task.account_id || "",
        contact_id: task.contact_id || "",
        assigned_to_id: task.assigned_to_id || ""
      });
    } else {
      setFormData({
        title: "", description: "", priority: "medium", task_type: "task", status: "pending", due_date: "", account_id: "", contact_id: "", assigned_to_id: ""
      });
    }
    setIsModalOpen(true);
  };

  const saveTask = async () => {
    try {
      const payload = {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        account_id: formData.account_id || null,
        contact_id: formData.contact_id || null,
        assigned_to_id: formData.assigned_to_id || null,
      };
      
      if (selectedTask) {
        await tasksAPI.update(selectedTask.id, payload);
      } else {
        await tasksAPI.create(payload);
      }
      setIsModalOpen(false);
      loadData();
    } catch (e) {
      console.error("Failed to save task", e);
    }
  };
  
  const deleteTask = async (id: string) => {
    if (!confirm("Delete this task?")) return;
    try {
      await tasksAPI.delete(id);
      setIsModalOpen(false);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0e14] text-[#8e97a3]" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Top Header Stats */}
      <div className="flex items-center gap-6 px-6 py-4 border-b border-[#1f2937]">
        <div className="flex items-center gap-2">
          <span className="text-xl font-medium text-white">{tasks.length}</span>
          <span className="text-sm font-medium">Total</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-medium text-[#f43f5e]">{countOf("Overdue")}</span>
          <span className="text-sm font-medium text-[#f43f5e]">Overdue</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-medium text-[#f59e0b]">{countOf("Today")}</span>
          <span className="text-sm font-medium text-[#f59e0b]">Due today</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-medium text-[#4f7eff]">{tasks.filter(t => t.status === "in_progress").length}</span>
          <span className="text-sm font-medium text-[#4f7eff]">In progress</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-medium text-[#00d4aa]">{countOf("Done")}</span>
          <span className="text-sm font-medium text-[#00d4aa]">Completed</span>
        </div>
        
        <div className="ml-auto">
          <button onClick={() => openModal()} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-[#4f7eff] hover:bg-[#4f7eff]/90 text-white rounded transition-colors">
            <Plus size={14} /> New Task
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-[#1f2937] shrink-0">
        <div className="flex items-center gap-1">
          {tabs.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded transition-colors ${tab === t ? "bg-[#4f7eff] text-white" : "hover:text-white hover:bg-white/5"}`}
            >
              {t}
              {(t === "Today" || t === "Overdue" || t === "Upcoming") && (
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${tab === t ? "bg-white/20 text-white" : "bg-white/10 text-muted-foreground"}`}>
                  {countOf(t)}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="relative ml-2">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#6b7694]" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search tasks..."
            className="pl-8 pr-3 py-1.5 text-xs bg-[#1f2937]/50 border border-[#1f2937] rounded text-white placeholder:text-[#6b7694] focus:outline-none focus:border-[#4f7eff]/50 transition-colors w-64"
          />
        </div>
      </div>

      {/* Task List Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-[11px] border-collapse min-w-[1000px]">
            <thead className="sticky top-0 z-10 bg-[#0b0e14] border-b border-[#1f2937]">
              <tr>
                <th className="w-10 px-4 py-3" />
                <th className="w-24 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Priority</th>
                <th className="px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Task</th>
                <th className="w-32 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Type</th>
                <th className="w-48 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Contact</th>
                <th className="w-32 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Status</th>
                <th className="w-36 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Due</th>
                <th className="w-32 px-3 py-3 text-left font-semibold text-[#6b7694] uppercase tracking-wider">Assignee</th>
                <th className="w-10 px-3 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(task => {
                const pc = priorityConfig[task.priority] || priorityConfig["medium"];
                const sc = statusConfig[task.status] || statusConfig["pending"];
                const tc = typeConfig[task.task_type || "task"] || typeConfig["task"];
                const TypeIcon = tc.icon;
                
                const isDone = checked.has(task.id) || task.status === "completed";
                const isOverdue = task.due_date && task.due_date.split("T")[0] < todayStr && !isDone;
                
                const contact = contactsMap[task.contact_id || ""];
                const account = accountsMap[task.account_id || ""];
                const user = usersMap[task.assigned_to_id || ""];
                
                return (
                  <tr key={task.id} className={`border-b border-[#1f2937] transition-colors ${isDone ? "opacity-40" : "hover:bg-white/[0.02]"}`}>
                    <td className="px-4 py-3 align-top pt-4">
                      <button onClick={() => toggleCheck(task.id, task.status)} className="text-[#6b7694] hover:text-[#00d4aa] transition-colors">
                        {isDone ? <CheckCircle2 size={16} style={{ color: "#00d4aa" }} /> : <Circle size={16} />}
                      </button>
                    </td>
                    <td className="px-3 py-3 align-top pt-4">
                      <span className="flex items-center gap-1.5 font-medium" style={{ color: pc.color }}>
                        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: pc.dot }} />
                        {pc.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 align-top pt-3.5">
                      <p className={`font-medium text-white text-xs ${isDone ? "line-through" : ""}`}>{task.title}</p>
                      {task.description && (
                        <p className="text-[11px] text-[#6b7694] mt-1 line-clamp-1 flex items-center gap-1">
                          <span className="px-1.5 border border-[#1f2937] rounded text-[9px] uppercase bg-black/20">{task.task_type || "task"}</span>
                          {task.description}
                        </p>
                      )}
                    </td>
                    <td className="px-3 py-3 align-top pt-4">
                      <div className="flex items-center gap-1.5 text-[#8e97a3]">
                        <TypeIcon size={13} />
                        <span>{tc.label}</span>
                      </div>
                    </td>
                    <td className="px-3 py-3 align-top pt-3.5">
                      {(contact || account) ? (
                        <div className="flex flex-col">
                          {contact && <span className="font-medium text-white">{contact.first_name} {contact.last_name}</span>}
                          {account && <span className="text-[#6b7694] text-[10px]">{account.name}</span>}
                        </div>
                      ) : (
                        <span className="text-[#6b7694]">—</span>
                      )}
                    </td>
                    <td className="px-3 py-3 align-top pt-3.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ color: sc.color, border: `1px solid ${sc.color}40`, background: sc.bg }}>
                        {sc.label}
                      </span>
                    </td>
                    <td className="px-3 py-3 align-top pt-4">
                      <span className={`flex items-center gap-1 font-mono text-[11px] ${isOverdue ? "text-[#f43f5e]" : "text-[#8e97a3]"}`}>
                        {isOverdue && <AlertTriangle size={11} />}
                        {!isOverdue && <Calendar size={11} />}
                        {task.due_date ? (
                          <span>
                            {task.due_date.split("T")[0] === todayStr ? "Today " : 
                             task.due_date.split("T")[0] === new Date(Date.now() + 86400000).toISOString().split("T")[0] ? "Tomorrow " :
                             new Date(task.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) + " "}
                            {new Date(task.due_date).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
                          </span>
                        ) : "—"}
                      </span>
                    </td>
                    <td className="px-3 py-3 align-top pt-3.5">
                      {user ? (
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-[#4f7eff]/20 flex items-center justify-center text-[9px] font-mono font-semibold text-[#4f7eff]">
                            {user.first_name?.[0]}{user.last_name?.[0]}
                          </div>
                          <span className="text-[#8e97a3]">{user.first_name}</span>
                        </div>
                      ) : (
                        <span className="text-[#6b7694]">—</span>
                      )}
                    </td>
                    <td className="px-3 py-3 align-top pt-3.5 text-right">
                      <button onClick={() => openModal(task)} className="p-1 text-[#6b7694] hover:text-white transition-colors rounded hover:bg-white/5">
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
      
      {/* Edit/Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#0b0e14] border border-[#1f2937] rounded-lg shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
            <div className="px-5 py-4 border-b border-[#1f2937] flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">{selectedTask ? "Edit Task" : "New Task"}</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-[#6b7694] hover:text-white"><X size={16}/></button>
            </div>
            
            <div className="p-5 overflow-y-auto max-h-[70vh] flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="text-[#8e97a3] font-medium">Task Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({...formData, title: e.target.value})}
                  className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  placeholder="e.g. Call Client regarding proposal"
                />
              </div>
              
              <div className="flex flex-col gap-1.5">
                <label className="text-[#8e97a3] font-medium">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none h-20 resize-none"
                  placeholder="Additional notes..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Type</label>
                  <select
                    value={formData.task_type}
                    onChange={e => setFormData({...formData, task_type: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  >
                    <option value="task">Task</option>
                    <option value="email">Email</option>
                    <option value="call">Call</option>
                    <option value="meeting">Meeting</option>
                    <option value="follow_up">Follow-up</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Status</label>
                  <select
                    value={formData.status}
                    onChange={e => setFormData({...formData, status: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  >
                    <option value="pending">Todo</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Done</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={e => setFormData({...formData, priority: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Due Date & Time</label>
                  <input
                    type="datetime-local"
                    value={formData.due_date}
                    onChange={e => setFormData({...formData, due_date: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                    style={{ colorScheme: 'dark' }}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[#8e97a3] font-medium">Customer (Account)</label>
                <select
                  value={formData.account_id}
                  onChange={e => setFormData({...formData, account_id: e.target.value})}
                  className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                >
                  <option value="">-- None --</option>
                  {Object.values(accountsMap).map((a: any) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Contact Person</label>
                  <select
                    value={formData.contact_id}
                    onChange={e => setFormData({...formData, contact_id: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  >
                    <option value="">-- None --</option>
                    {Object.values(contactsMap).filter(c => !formData.account_id || c.account_id === formData.account_id).map((c: any) => (
                      <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[#8e97a3] font-medium">Assign To</label>
                  <select
                    value={formData.assigned_to_id}
                    onChange={e => setFormData({...formData, assigned_to_id: e.target.value})}
                    className="px-3 py-2 bg-[#1f2937]/50 border border-[#1f2937] rounded text-white focus:border-[#4f7eff]/50 outline-none"
                  >
                    <option value="">-- Unassigned --</option>
                    {Object.values(usersMap).map((u: any) => (
                      <option key={u.id} value={u.id}>{u.first_name} {u.last_name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="px-5 py-4 border-t border-[#1f2937] flex justify-between bg-[#1f2937]/20">
              {selectedTask ? (
                <button onClick={() => deleteTask(selectedTask.id)} className="px-4 py-2 text-xs font-medium text-[#f43f5e] hover:bg-[#f43f5e]/10 rounded transition-colors">
                  Delete
                </button>
              ) : <div></div>}
              <div className="flex gap-2">
                <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-xs font-medium text-[#8e97a3] hover:text-white transition-colors">
                  Cancel
                </button>
                <button onClick={saveTask} disabled={!formData.title} className="px-4 py-2 text-xs font-medium bg-[#4f7eff] text-white rounded hover:bg-[#4f7eff]/90 transition-colors disabled:opacity-50">
                  Save Task
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
