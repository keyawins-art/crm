import { useState, useEffect } from "react";
import { Bell, Check, MoreHorizontal } from "lucide-react";
import { notificationsAPI } from "../../lib/api";

export function Notifications() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const res = await notificationsAPI.list(1, 50);
      setNotifications(res.data.items || []);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReadAll = async () => {
    try {
      await notificationsAPI.readAll();
      loadNotifications();
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const handleRead = async (id: string) => {
    try {
      await notificationsAPI.read(id);
      loadNotifications();
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0 bg-card">
        <Bell size={16} className="text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">Notifications</h2>
        <div className="ml-auto">
          <button onClick={handleReadAll} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary rounded text-xs font-medium hover:bg-primary/20 transition-colors">
            <Check size={14} /> Mark all as read
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-12 text-sm text-muted-foreground">You have no notifications.</div>
        ) : (
          <div className="max-w-2xl space-y-2">
            {notifications.map(n => (
              <div key={n.id} className={`flex items-start gap-4 p-4 rounded border ${n.is_read ? 'border-transparent bg-white/[0.02]' : 'border-primary/20 bg-primary/5'}`}>
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${n.is_read ? 'bg-transparent' : 'bg-primary'}`} />
                <div className="flex-1 min-w-0">
                  <h3 className={`text-sm ${n.is_read ? 'text-muted-foreground font-medium' : 'text-foreground font-semibold'}`}>{n.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                  <p className="text-[10px] font-mono text-muted-foreground mt-2">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.is_read && (
                  <button onClick={() => handleRead(n.id)} className="text-primary hover:text-primary/80 transition-colors p-1" title="Mark as read">
                    <Check size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
