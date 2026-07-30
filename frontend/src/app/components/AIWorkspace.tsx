import { FormEvent, useEffect, useRef, useState } from "react";
import { Bot, CheckCircle2, Database, LoaderCircle, RefreshCw, Send, Sparkles, UserRound } from "lucide-react";
import { aiAPI } from "../../lib/api";

type Message = { role: "user" | "assistant"; content: string; sources?: string[] };

const quickPrompts = [
  "Prioritize my most important follow-ups for today.",
  "Summarize my active sales pipeline and highlight risks.",
  "Draft a concise follow-up email for the lead that needs attention first.",
  "What customer-support issues should I address urgently?",
];

export function AIWorkspace() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ enabled: boolean; ready: boolean; model: string; detail: string } | null>(null);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const checkStatus = async () => {
    try {
      setError("");
      const response = await aiAPI.status();
      setStatus(response.data);
    } catch (err: any) {
      setStatus(null);
      setError(err.response?.data?.detail || "CRM Copilot could not be reached.");
    }
  };

  useEffect(() => { checkStatus(); }, []);
  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages, loading]);

  const send = async (text?: string) => {
    const message = (text ?? input).trim();
    if (!message || loading || !status?.ready) return;

    const nextMessages: Message[] = [...messages, { role: "user", content: message }];
    setMessages(nextMessages);
    setInput("");
    setError("");
    setLoading(true);
    try {
      const response = await aiAPI.chat({
        message,
        conversation: messages.slice(-8).map(({ role, content }) => ({ role, content })),
      });
      setMessages([...nextMessages, { role: "assistant", content: response.data.answer, sources: response.data.sources }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || "The Copilot could not complete that request.");
      await checkStatus();
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (event: FormEvent) => { event.preventDefault(); send(); };
  const ready = Boolean(status?.enabled && status?.ready);

  return (
    <div className="h-full p-4 md:p-6" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="h-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_260px] gap-4">
        <section className="min-h-[600px] flex flex-col rounded-xl border border-border bg-card overflow-hidden shadow-sm">
          <div className="px-5 py-4 border-b border-border flex items-center gap-3 bg-gradient-to-r from-primary/10 via-transparent to-transparent">
            <div className="w-9 h-9 rounded-lg bg-primary text-white grid place-items-center shadow-sm"><Sparkles size={17} /></div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-foreground">CRM Copilot</h2>
              <p className="text-[11px] text-muted-foreground truncate">{status?.detail || "Checking local AI service…"}</p>
            </div>
            {ready && <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 text-emerald-600 px-2.5 py-1 text-[10px] font-medium"><CheckCircle2 size={12} /> {status?.model}</span>}
          </div>

          <div ref={scrollRef} className="flex-1 overflow-auto p-5 space-y-5">
            {messages.length === 0 && (
              <div className="max-w-xl mx-auto py-10 text-center">
                <div className="mx-auto mb-4 w-12 h-12 rounded-2xl bg-primary/10 text-primary grid place-items-center"><Bot size={22} /></div>
                <h3 className="text-base font-semibold text-foreground">Your private sales workspace</h3>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">Ask for priorities, pipeline analysis, support triage, or a customer-ready draft. Copilot uses only CRM records you are allowed to view and never takes actions by itself.</p>
              </div>
            )}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                {message.role === "assistant" && <div className="w-7 h-7 rounded-full shrink-0 bg-primary/10 text-primary grid place-items-center"><Bot size={14} /></div>}
                <div className={`max-w-[85%] rounded-xl px-4 py-3 text-xs leading-5 whitespace-pre-wrap ${message.role === "user" ? "bg-primary text-white" : "bg-muted/60 text-foreground border border-border/70"}`}>
                  {message.content}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-border/60 text-[10px] text-muted-foreground flex flex-wrap gap-x-3 gap-y-1">
                      {message.sources.map(source => <span key={source} className="inline-flex items-center gap-1"><Database size={10} />{source}</span>)}
                    </div>
                  )}
                </div>
                {message.role === "user" && <div className="w-7 h-7 rounded-full shrink-0 bg-primary text-white grid place-items-center"><UserRound size={14} /></div>}
              </div>
            ))}
            {loading && <div className="flex gap-3"><div className="w-7 h-7 rounded-full bg-primary/10 text-primary grid place-items-center"><Bot size={14} /></div><div className="rounded-xl px-4 py-3 text-xs bg-muted/60 border border-border"><LoaderCircle size={14} className="inline mr-2 animate-spin text-primary" />Thinking with your CRM context…</div></div>}
          </div>

          {error && <div className="mx-5 mb-3 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-[11px] text-destructive">{error}</div>}
          <form onSubmit={onSubmit} className="p-4 border-t border-border bg-background/60">
            <div className="flex gap-2 rounded-xl border border-border bg-card p-1.5 focus-within:border-primary/50 transition-colors">
              <textarea value={input} onChange={event => setInput(event.target.value)} disabled={!ready || loading} rows={2} placeholder={ready ? "Ask about your leads, pipeline, tickets, or request a draft…" : "Copilot is unavailable until the local model is ready."} className="flex-1 resize-none bg-transparent px-2 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed" />
              <button type="submit" disabled={!ready || loading || !input.trim()} className="self-end grid place-items-center w-8 h-8 rounded-lg bg-primary text-white disabled:opacity-40 hover:bg-primary/90 transition-colors" title="Send message"><Send size={14} /></button>
            </div>
            <p className="px-2 pt-2 text-[10px] text-muted-foreground">Review all AI drafts before sending. Customer data stays on this server through local Ollama.</p>
          </form>
        </section>

        <aside className="rounded-xl border border-border bg-card p-4 h-fit">
          <div className="flex items-center justify-between mb-3"><h3 className="text-xs font-semibold text-foreground">Quick prompts</h3><button onClick={checkStatus} className="text-muted-foreground hover:text-primary transition-colors" title="Check model status"><RefreshCw size={13} /></button></div>
          <div className="space-y-2">{quickPrompts.map(prompt => <button key={prompt} onClick={() => send(prompt)} disabled={!ready || loading} className="w-full text-left rounded-lg border border-border p-3 text-[11px] leading-4 text-muted-foreground hover:border-primary/40 hover:text-foreground hover:bg-primary/5 disabled:opacity-50 transition-colors">{prompt}</button>)}</div>
          <div className="mt-4 pt-4 border-t border-border text-[10px] text-muted-foreground leading-4"><span className="font-medium text-foreground">Read-only by design.</span> Copilot can suggest and draft, but it cannot change a CRM record or send a message.</div>
        </aside>
      </div>
    </div>
  );
}
