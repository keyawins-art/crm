import { useState, useEffect } from "react";
import { Link, Zap, Settings2 } from "lucide-react";
import { integrationsAPI } from "../../lib/api";

export function Integrations() {
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      const res = await integrationsAPI.list();
      setIntegrations(res.data || []);
    } catch (err) {
      console.error("Failed to load integrations:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (provider: string, isConnected: boolean) => {
    try {
      if (isConnected) {
        if (!window.confirm(`Disconnect ${provider}?`)) return;
        await integrationsAPI.disconnect(provider);
      } else {
        await integrationsAPI.connect(provider, {});
      }
      loadIntegrations();
    } catch (err) {
      console.error(`Failed to toggle ${provider}:`, err);
    }
  };

  // Pre-defined available integrations since backend might just return connected ones
  const available = [
    { provider: "slack", name: "Slack", description: "Send CRM notifications to Slack channels", icon: "S" },
    { provider: "google_calendar", name: "Google Calendar", description: "Sync meetings and events with Google Calendar", icon: "G" },
    { provider: "stripe", name: "Stripe", description: "Process payments for invoices automatically", icon: "$" }
  ];

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0 bg-card">
        <Settings2 size={16} className="text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">Integrations</h2>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="max-w-3xl space-y-4">
            {available.map(app => {
              const connectedInfo = integrations.find(i => i.provider_name === app.provider);
              const isConnected = !!connectedInfo?.is_active;

              return (
                <div key={app.provider} className="flex items-center justify-between p-5 rounded-lg border border-border bg-card">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded bg-secondary flex items-center justify-center text-lg font-bold text-foreground">
                      {app.icon}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">{app.name}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">{app.description}</p>
                    </div>
                  </div>
                  <div>
                    <button 
                      onClick={() => handleToggle(app.provider, isConnected)}
                      className={`flex items-center gap-2 px-4 py-1.5 rounded text-xs font-medium transition-colors ${
                        isConnected 
                          ? 'bg-rose-500/10 text-rose-500 hover:bg-rose-500/20'
                          : 'bg-primary text-white hover:bg-primary/90'
                      }`}
                    >
                      {isConnected ? 'Disconnect' : 'Connect'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
