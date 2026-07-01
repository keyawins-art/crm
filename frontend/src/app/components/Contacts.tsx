import { useState, useEffect } from "react";
import {
  Search, Filter, Plus, MoreHorizontal, Mail, Phone,
  MapPin, Tag, ChevronUp, ChevronDown, Star, StarOff,
  Upload, Download, Users
} from "lucide-react";
import { contactsAPI } from "../../lib/api";

type Contact = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  title: string;
  department: string;
  is_primary: boolean;
  account_id: string;
  created_at: string;
};

const statusConfig: Record<string, { color: string; bg: string }> = {
  Active: { color: "#00d4aa", bg: "#00d4aa18" },
  Inactive: { color: "#6b7694", bg: "#6b769418" },
};

type SortKey = "first_name" | "company" | "created_at";

export function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortKey>("first_name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [starred, setStarred] = useState<Set<string>>(new Set());
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      setLoading(true);
      const res = await contactsAPI.list(1, 50);
      setContacts(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load contacts:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSort = (key: SortKey) => {
    if (sort === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSort(key); setSortDir("asc"); }
  };

  const filtered = contacts
    .filter(c => {
      const q = search.toLowerCase();
      const name = `${c.first_name} ${c.last_name}`.toLowerCase();
      const matchSearch = !q || name.includes(q) || (c.email || "").toLowerCase().includes(q);
      return matchSearch;
    })
    .sort((a, b) => {
      let va = a[sort] || "";
      let vb = b[sort] || "";
      return (sortDir === "asc" ? 1 : -1) * String(va).localeCompare(String(vb));
    });

  const allSelected = filtered.length > 0 && filtered.every(c => selected.has(c.id));
  const toggleAll = () => {
    if (allSelected) setSelected(new Set());
    else setSelected(new Set(filtered.map(c => c.id)));
  };
  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };
  const toggleStar = (id: string) => {
    const next = new Set(starred);
    next.has(id) ? next.delete(id) : next.add(id);
    setStarred(next);
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sort === k ? (sortDir === "asc" ? <ChevronUp size={11} /> : <ChevronDown size={11} />) : null;

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search contacts…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64"
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          {selected.size > 0 && (
            <span className="text-xs font-mono text-primary mr-1">{selected.size} selected</span>
          )}
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">
            <Plus size={12} /> Add Contact
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-6 px-6 py-2.5 border-b border-border bg-secondary/30 text-[11px] font-mono text-muted-foreground">
        <span>{total} total</span>
        <span className="ml-auto text-muted-foreground/50">{filtered.length} shown</span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-card border-b border-border">
                <th className="w-10 px-4 py-2.5 text-left">
                  <input type="checkbox" checked={allSelected} onChange={toggleAll} className="accent-primary" />
                </th>
                <th className="w-8 px-1 py-2.5" />
                <th
                  className="px-3 py-2.5 text-left font-semibold text-muted-foreground uppercase tracking-wider text-[10px] cursor-pointer hover:text-foreground transition-colors"
                  onClick={() => toggleSort("first_name")}
                >
                  <div className="flex items-center gap-1">Name <SortIcon k="first_name" /></div>
                </th>
                <th className="px-3 py-2.5 text-left font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">Contact</th>
                <th className="px-3 py-2.5 text-left font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">Title</th>
                <th
                  className="px-3 py-2.5 text-left font-semibold text-muted-foreground uppercase tracking-wider text-[10px] cursor-pointer hover:text-foreground transition-colors"
                  onClick={() => toggleSort("created_at")}
                >
                  <div className="flex items-center gap-1">Added <SortIcon k="created_at" /></div>
                </th>
                <th className="w-10 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => {
                const isSel = selected.has(c.id);
                const isStar = starred.has(c.id);
                const initials = `${(c.first_name || "?")[0]}${(c.last_name || "")[0]}`.toUpperCase();
                return (
                  <tr
                    key={c.id}
                    className={`border-b border-border transition-colors cursor-pointer ${isSel ? "bg-primary/5" : "hover:bg-white/[0.02]"}`}
                  >
                    <td className="px-4 py-2.5">
                      <input type="checkbox" checked={isSel} onChange={() => toggleSelect(c.id)} className="accent-primary" />
                    </td>
                    <td className="px-1 py-2.5">
                      <button onClick={() => toggleStar(c.id)} className="text-muted-foreground/40 hover:text-chart-3 transition-colors">
                        {isStar ? <Star size={11} fill="#f59e0b" className="text-chart-3" /> : <StarOff size={11} />}
                      </button>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-mono font-semibold text-primary shrink-0">
                          {initials}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{c.first_name} {c.last_name}</p>
                          {c.is_primary && <span className="inline-flex px-1.5 py-0.5 rounded-sm bg-primary/20 text-primary text-[9px] mt-0.5">Primary</span>}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-3">
                        {c.email && (
                          <a href={`mailto:${c.email}`} className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1" title={c.email}>
                            <Mail size={12} /> <span className="truncate max-w-[120px]">{c.email}</span>
                          </a>
                        )}
                        {c.phone && (
                          <a href={`tel:${c.phone}`} className="text-muted-foreground hover:text-accent transition-colors flex items-center gap-1" title={c.phone}>
                            <Phone size={12} /> <span>{c.phone}</span>
                          </a>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <p className="text-foreground">{c.title || "—"}</p>
                      <p className="text-[10px] text-muted-foreground">{c.department}</p>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5">
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
            <Users size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No contacts match your search</p>
          </div>
        )}
      </div>
    </div>
  );
}
