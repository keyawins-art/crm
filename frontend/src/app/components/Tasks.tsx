import { useState, useEffect } from "react";
import {
  Plus, Search, CheckCircle2, Circle, Clock, Calendar,
  MoreHorizontal, AlertTriangle, FileText, ArrowRight
} from "lucide-react";
import { tasksAPI } from "../../lib/api";

type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";
type TaskPriority = "low" | "medium" | "high";

type Task = {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string;
  created_at: string;
};

const priorityConfig: Record<string, { color: string; bg: string; dot: string }> = {
  high:     { color: "#f59e0b", bg: "#f59e0b15", dot: "#f59e0b" },
  medium:   { color: "#4f7eff", bg: "#4f7eff15", dot: "#4f7eff" },
  low:      { color: "#6b7694", bg: "#6b769415", dot: "#6b7694" },
};

const statusConfig: Record<string, { color: string; bg: string }> = {
  "pending":        { color: "#6b7694", bg: "#6b769415" },
  "in_progress": { color: "#4f7eff", bg: "#4f7eff15" },
  "completed":        { color: "#00d4aa", bg: "#00d4aa15" },
  "cancelled":     { color: "#f43f5e", bg: "#f43f5e15" },
};

type Tab = "All" | "Today" | "Done" | "Overdue";

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("All");
  const [search, setSearch] = useState("");
  const [checked, setChecked] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const res = await tasksAPI.list(1, 100);
      setTasks(res.data.items || []);
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  const tabs: Tab[] = ["All", "Today", "Done", "Overdue"];

  const filtered = tasks.filter(t => {
    const q = search.toLowerCase();
    const matchSearch = !q || t.title.toLowerCase().includes(q);
    if (!matchSearch) return false;
    
    const today = new Date().toISOString().split("T")[0];
    const due = t.due_date ? t.due_date.split("T")[0] : null;

    switch (tab) {
      case "Today": return due === today;
      case "Done": return t.status === "completed" || checked.has(t.id);
      case "Overdue": return due && due < today && t.status !== "completed";
      default: return true;
    }
  });

  const countOf = (t: Tab) => {
    const today = new Date().toISOString().split("T")[0];
    switch (t) {
      case "Today": return tasks.filter(x => x.due_date && x.due_date.split("T")[0] === today).length;
      case "Overdue": return tasks.filter(x => x.due_date && x.due_date.split("T")[0] < today && x.status !== "completed").length;
      case "Done": return tasks.filter(x => x.status === "completed").length;
      default: return tasks.length;
    }
  };

  const toggleCheck = (id: string) => {
    const next = new Set(checked);
    next.has(id) ? next.delete(id) : next.add(id);
    setChecked(next);
  };

  const summaryStats = [
    { label: "Total", value: tasks.length, color: "#dde1ee" },
    { label: "Completed", value: tasks.filter(t => t.status === "completed").length, color: "#00d4aa" },
  ];

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Stats bar */}
      <div className="flex items-center gap-8 px-6 py-3 border-b border-border bg-card/30 shrink-0">
        {summaryStats.map(({ label, value, color }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="text-xl font-mono font-semibold" style={{ color }}>{value}</span>
            <span className="text-[11px] text-muted-foreground">{label}</span>
          </div>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> New Task
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border shrink-0">
        {/* Tabs */}
        <div className="flex items-center gap-0 border border-border rounded overflow-hidden">
          {tabs.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium transition-colors ${tab === t ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground hover:bg-white/5"}`}
            >
              {t}
              {(t === "Today" || t === "Overdue") && (
                <span className={`text-[9px] font-mono px-1 py-0.5 rounded-full ${tab === t ? "bg-white/20" : "bg-white/10"}`}>
                  {countOf(t)}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search tasks…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-56"
          />
        </div>
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="w-10 px-4 py-2.5" />
                <th className="w-24 px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Priority</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Task</th>
                <th className="w-28 px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="w-32 px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Due</th>
                <th className="w-8 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(task => {
                const pc = priorityConfig[task.priority] || priorityConfig["medium"];
                const sc = statusConfig[task.status] || statusConfig["pending"];
                const isDone = checked.has(task.id) || task.status === "completed";
                const isOverdue = task.due_date && task.due_date.split("T")[0] < new Date().toISOString().split("T")[0] && !isDone;
                
                return (
                  <tr key={task.id} className={`border-b border-border transition-colors ${isDone ? "opacity-50" : "hover:bg-white/[0.02]"}`}>
                    <td className="px-4 py-3">
                      <button onClick={() => toggleCheck(task.id)} className="text-muted-foreground hover:text-primary transition-colors">
                        {isDone
                          ? <CheckCircle2 size={14} style={{ color: "#00d4aa" }} />
                          : <Circle size={14} />}
                      </button>
                    </td>
                    <td className="px-3 py-3">
                      <span className="flex items-center gap-1.5 text-[11px] font-medium capitalize" style={{ color: pc.color }}>
                        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: pc.dot }} />
                        {task.priority}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <p className={`font-medium text-foreground ${isDone ? "line-through" : ""}`}>{task.title}</p>
                      {task.description && <p className="text-[11px] text-muted-foreground mt-0.5 truncate max-w-xs">{task.description}</p>}
                    </td>
                    <td className="px-3 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize" style={{ color: sc.color, background: sc.bg }}>
                        {isDone ? "completed" : task.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <span className={`flex items-center gap-1 font-mono text-[11px] ${isOverdue ? "text-destructive" : "text-muted-foreground"}`}>
                        {isOverdue && <AlertTriangle size={10} />}
                        <Calendar size={10} />
                        {task.due_date ? new Date(task.due_date).toLocaleDateString() : "—"}
                      </span>
                    </td>
                    <td className="px-3 py-3">
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
            <CheckCircle2 size={32} className="text-muted-foreground/20 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No tasks found</p>
          </div>
        )}
      </div>
    </div>
  );
}
