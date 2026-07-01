import { useState, useEffect } from "react";
import { Calendar as CalendarIcon, CheckSquare, Phone, Users, Clock } from "lucide-react";
import { calendarAPI } from "../../lib/api";

export function Calendar() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const res = await calendarAPI.getEvents();
      setEvents(res.data || []);
    } catch (err) {
      console.error("Failed to load events:", err);
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "task": return <CheckSquare size={14} className="text-emerald-500" />;
      case "call": return <Phone size={14} className="text-blue-500" />;
      case "meeting": return <Users size={14} className="text-purple-500" />;
      default: return <CalendarIcon size={14} className="text-gray-500" />;
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <CalendarIcon size={16} className="text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">Agenda</h2>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12 text-sm text-muted-foreground">No upcoming events.</div>
        ) : (
          <div className="space-y-4 max-w-2xl">
            {events.map((e, idx) => (
              <div key={`${e.id}-${idx}`} className="flex items-start gap-4 p-4 rounded border border-border bg-card">
                <div className="flex items-center justify-center w-8 h-8 rounded bg-secondary/50 shrink-0">
                  {getIcon(e.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-xs font-semibold text-foreground truncate">{e.title}</h3>
                  <div className="flex items-center gap-4 mt-1 text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1.5 capitalize"><span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/50" /> {e.type}</span>
                    <span className="flex items-center gap-1.5"><Clock size={12} /> {new Date(e.start_time).toLocaleString()}</span>
                  </div>
                </div>
                <div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium capitalize ${
                    e.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' :
                    e.status === 'overdue' ? 'bg-rose-500/10 text-rose-500' :
                    'bg-primary/10 text-primary'
                  }`}>
                    {e.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
