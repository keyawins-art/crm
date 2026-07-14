import { useState, useEffect } from "react";
import { Search, Book, Plus, MoreHorizontal } from "lucide-react";
import { knowledgeBaseAPI } from "../../lib/api";

export function KnowledgeBase() {
  const [articles, setArticles] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      setLoading(true);
      const res = await knowledgeBaseAPI.list(1, 50);
      setArticles(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load articles:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = articles.filter(a => {
    const term = search.toLowerCase();
    return !term || a.title?.toLowerCase().includes(term) || a.category?.toLowerCase().includes(term);
  });

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search knowledge base…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} articles</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Article
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map(a => (
              <div key={a.id} className="flex flex-col p-4 rounded border border-border bg-card hover:border-primary/30 transition-colors cursor-pointer group">
                <div className="flex items-center justify-between mb-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary uppercase tracking-wider">
                    {a.category || "General"}
                  </span>
                  <button className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hover:text-foreground">
                    <MoreHorizontal size={14} />
                  </button>
                </div>
                <h3 className="text-sm font-semibold text-foreground mb-2 line-clamp-1">{a.title}</h3>
                <p className="text-xs text-muted-foreground line-clamp-2 flex-1 mb-4">
                  {a.content}
                </p>
                <div className="flex items-center justify-between mt-auto pt-3 border-t border-border">
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {a.updated_at ? new Date(a.updated_at).toLocaleDateString('en-GB') : '—'}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {a.status}
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
