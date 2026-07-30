import { useState, useEffect } from "react";
import { Search, Plus, Phone, MoreHorizontal, Sparkles, X, Mic } from "lucide-react";
import { callsAPI, aiAPI, leadsAPI, accountsAPI } from "../../lib/api";

export function Calls() {
  const [calls, setCalls] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [showAIModal, setShowAIModal] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [entityType, setEntityType] = useState("leads");
  const [entityId, setEntityId] = useState("");
  const [entities, setEntities] = useState<any[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  useEffect(() => {
    loadCalls();
  }, []);

  useEffect(() => {
    if (showAIModal) {
      loadEntities(entityType);
    }
  }, [showAIModal, entityType]);

  const loadEntities = async (type: string) => {
    try {
      if (type === "leads") {
        const res = await leadsAPI.list(1, 100);
        setEntities(res.data.items || []);
      } else if (type === "accounts") {
        const res = await accountsAPI.list(1, 100);
        setEntities(res.data.items || []);
      }
      setEntityId("");
    } catch (err) {
      console.error("Failed to load entities:", err);
    }
  };

  const handleAutoLog = async () => {
    if (!transcript.trim() && !audioFile) {
      alert("Please provide a transcript or upload an audio file, and select an entity.");
      return;
    }
    if (!entityId) {
      alert("Please select an entity.");
      return;
    }
    try {
      setAiLoading(true);
      if (audioFile) {
        const formData = new FormData();
        formData.append("file", audioFile);
        formData.append("entity_type", entityType);
        formData.append("entity_id", entityId);
        await aiAPI.uploadCallAudio(formData);
      } else {
        await aiAPI.autoLogCall({ transcript, entity_type: entityType, entity_id: entityId });
      }
      alert("AI Call Logged Successfully!");
      setShowAIModal(false);
      setTranscript("");
      setAudioFile(null);
      loadCalls();
    } catch (e: any) {
      alert("Error: " + (e.response?.data?.detail || e.message));
    } finally {
      setAiLoading(false);
    }
  };

  const loadCalls = async () => {
    try {
      setLoading(true);
      const res = await callsAPI.list(1, 50);
      setCalls(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load calls:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = calls.filter(c => {
    const term = search.toLowerCase();
    return !term || c.phone_number?.toLowerCase().includes(term) || c.notes?.toLowerCase().includes(term);
  });

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search calls…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} calls</span>
          <button onClick={() => setShowAIModal(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/20 text-primary border border-primary/30 rounded text-xs font-medium hover:bg-primary/30 transition-colors">
            <Sparkles size={14} /> AI Auto-Log
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> Log Call
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Number</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Type</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Outcome</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Date</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Duration</th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded bg-blue-500/10 flex items-center justify-center shrink-0">
                        <Phone size={13} className="text-blue-500" />
                      </div>
                      <span className="font-mono font-medium text-foreground">{c.phone_number}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 capitalize">{c.call_type}</td>
                  <td className="px-3 py-2.5">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize ${
                      c.outcome === 'interested' ? 'bg-emerald-500/10 text-emerald-500' :
                      c.outcome === 'not_interested' ? 'bg-rose-500/10 text-rose-500' :
                      'bg-secondary text-muted-foreground'
                    }`}>
                      {c.outcome || "Unknown"}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                    {c.start_time ? new Date(c.start_time).toLocaleString() : "—"}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                    {c.duration_seconds ? `${Math.floor(c.duration_seconds / 60)}m ${c.duration_seconds % 60}s` : "—"}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <button className="text-muted-foreground hover:text-foreground">
                      <MoreHorizontal size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* AI Auto-Log Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-card border border-border shadow-2xl rounded-xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Sparkles className="text-primary" size={18} /> AI Auto-Log Call
              </h2>
              <button onClick={() => setShowAIModal(false)} className="text-muted-foreground hover:text-foreground">
                <X size={18} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <p className="text-xs text-muted-foreground">
                Paste the call transcript or raw notes below. Nexus AI will automatically analyze it, extract the outcome, summarize it, and attach it to the selected customer record.
              </p>
              
              <div className="flex gap-4">
                <div className="w-1/3">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Record Type</label>
                  <select 
                    value={entityType} 
                    onChange={e => setEntityType(e.target.value)}
                    className="w-full bg-secondary/50 border border-border rounded px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary"
                  >
                    <option value="leads">Lead</option>
                    <option value="accounts">Account</option>
                  </select>
                </div>
                <div className="w-2/3">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Select Record</label>
                  <select 
                    value={entityId} 
                    onChange={e => setEntityId(e.target.value)}
                    className="w-full bg-secondary/50 border border-border rounded px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary"
                  >
                    <option value="">Select a {entityType.slice(0, -1)}...</option>
                    {entities.map(ent => (
                      <option key={ent.id} value={ent.id}>
                        {ent.name || `${ent.first_name || ''} ${ent.last_name || ''}`.trim() || ent.company}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">Call Recording / Transcript</label>
                
                <div className="flex gap-4 items-center">
                  <label className="flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed border-primary/40 bg-primary/5 text-primary rounded-lg cursor-pointer hover:bg-primary/10 transition-colors w-1/3">
                    <Mic size={16} />
                    <span className="text-xs font-semibold">{audioFile ? audioFile.name : "Upload Audio File"}</span>
                    <input type="file" accept="audio/*" className="hidden" onChange={e => {
                      if(e.target.files?.[0]) {
                        setAudioFile(e.target.files[0]);
                        setTranscript("");
                      }
                    }} />
                  </label>
                  <span className="text-xs text-muted-foreground font-semibold">OR</span>
                  <textarea 
                    value={transcript}
                    disabled={!!audioFile}
                    onChange={e => setTranscript(e.target.value)}
                    placeholder={audioFile ? "Audio selected..." : "[Speaker 1]: Hello, am I speaking with..."}
                    className="flex-1 h-24 bg-secondary/30 border border-border rounded-lg p-3 text-xs text-foreground font-mono resize-none focus:outline-none focus:border-primary disabled:opacity-50"
                  />
                </div>
              </div>
            </div>

            <div className="px-6 py-4 bg-muted/20 border-t border-border flex justify-end gap-3">
              <button 
                onClick={() => { setShowAIModal(false); setAudioFile(null); setTranscript(""); }}
                className="px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleAutoLog}
                disabled={aiLoading || (!transcript.trim() && !audioFile) || !entityId}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {aiLoading ? (
                  <><span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Processing...</>
                ) : (
                  <><Sparkles size={14} /> Process & Log Note</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
