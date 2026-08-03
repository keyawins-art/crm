import React, { useState, useEffect, useRef } from "react";
import { Sparkles, Bot, X, Send, RefreshCw, Minimize2, ChevronDown, MessageSquare, Zap } from "lucide-react";
import { aiAPI } from "../../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  time?: string;
}

export function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "👋 Hi! I'm your CRM Copilot. How can I help you manage your leads, deals, or tasks today?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState("qwen3:1.7b");
  const [ready, setReady] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    aiAPI
      .status()
      .then((res) => {
        setReady(res.data.ready);
        if (res.data.model) setModel(res.data.model);
      })
      .catch(() => setReady(false));

    const handleOpenEvent = () => setIsOpen(true);
    window.addEventListener("open-ai-chat", handleOpenEvent);
    return () => window.removeEventListener("open-ai-chat", handleOpenEvent);
  }, []);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      role: "user",
      content: query,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const history = messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await aiAPI.chat({
        message: query,
        conversation: history,
      });

      const botMsg: Message = {
        role: "assistant",
        content: res.data.answer || "I'm ready to help! What would you like to check in your CRM?",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        role: "assistant",
        content: err.response?.data?.detail || "Sorry, I had trouble reaching the CRM AI service. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    { label: "🚀 Top Leads", query: "Show my top leads today" },
    { label: "💰 Active Deals", query: "What deals are close to closing?" },
    { label: "📝 Draft Email", query: "Draft a follow-up email for my latest lead" },
    { label: "⚡ Pending Tasks", query: "What tasks do I need to finish today?" },
  ];

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Floating Animated Mascot Button (When Closed) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 animate-pulse"
          title="Open AI Chatbot"
        >
          {/* Animated Glow Ring */}
          <span className="absolute -inset-1 rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 opacity-75 blur transition duration-500 group-hover:opacity-100 animate-tilt"></span>
          
          {/* Cartoon Robot Mascot Icon */}
          <div className="relative flex items-center justify-center w-full h-full rounded-full bg-slate-900 border border-white/20">
            <Bot size={26} className="text-indigo-400 group-hover:rotate-12 transition-transform duration-300" />
            <span className="absolute top-1 right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border border-slate-900"></span>
            </span>
          </div>

          {/* Floating Speech Badge */}
          <div className="absolute -top-9 right-0 bg-slate-900 border border-indigo-500/30 text-white text-[11px] font-medium px-2.5 py-1 rounded-full shadow-lg whitespace-nowrap flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
            <Sparkles size={12} className="text-amber-400 animate-spin" />
            <span>AI Copilot</span>
          </div>
        </button>
      )}

      {/* Floating Chat Popup Window */}
      {isOpen && (
        <div className="flex flex-col w-[350px] sm:w-[390px] h-[520px] rounded-2xl bg-slate-950/95 backdrop-blur-xl border border-indigo-500/30 shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-300">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/80 border-b border-indigo-500/20">
            <div className="flex items-center gap-3">
              {/* Cartoon Mascot Avatar */}
              <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md">
                <Bot size={20} className="text-white animate-bounce" />
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 border-2 border-slate-900 rounded-full"></span>
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-xs font-bold text-white tracking-tight">Nexus AI Copilot</h3>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {model}
                  </span>
                </div>
                <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Online • Smart CRM Assistant
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setMessages([messages[0]])}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                title="Clear Chat"
              >
                <RefreshCw size={14} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Quick Prompts Carousel */}
          <div className="flex items-center gap-1.5 px-3 py-2 bg-slate-900/40 overflow-x-auto border-b border-indigo-500/10 no-scrollbar">
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p.query)}
                disabled={loading}
                className="text-[11px] font-medium whitespace-nowrap px-2.5 py-1 rounded-full bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 transition-all active:scale-95 disabled:opacity-50 shrink-0"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Messages Area */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={15} className="text-indigo-400" />
                  </div>
                )}

                <div
                  className={`max-w-[82%] px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed ${
                    m.role === "user"
                      ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-none shadow-md"
                      : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.time && (
                    <span
                      className={`block text-[9px] mt-1 ${
                        m.role === "user" ? "text-indigo-200/70 text-right" : "text-slate-500"
                      }`}
                    >
                      {m.time}
                    </span>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Loader */}
            {loading && (
              <div className="flex gap-2.5 justify-start items-center">
                <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center shrink-0">
                  <Bot size={15} className="text-indigo-400 animate-spin" />
                </div>
                <div className="bg-slate-900 border border-slate-800 px-3.5 py-2 rounded-2xl rounded-bl-none flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  <span className="text-[10px] ml-1 text-indigo-300">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Footer */}
          <div className="p-3 bg-slate-900/90 border-t border-indigo-500/20">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2 bg-slate-950 border border-indigo-500/30 rounded-xl px-3 py-1.5 focus-within:border-indigo-500 transition-colors"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={ready ? "Ask chatbot anything..." : "Copilot is offline..."}
                disabled={!ready || loading}
                className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="p-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-colors active:scale-95"
              >
                <Send size={13} />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
