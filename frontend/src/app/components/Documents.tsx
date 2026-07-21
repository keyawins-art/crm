import { useState, useEffect } from "react";
import { Search, File, UploadCloud, MoreHorizontal, Download } from "lucide-react";
import { documentsAPI } from "../../lib/api";
import api from "../../lib/api";

type CrmDocument = {
  id: string;
  entity_type: string;
  entity_id: string;
  filename: string;
  file_size: number;
  category?: string;
};

export function Documents() {
  const [documents, setDocuments] = useState<CrmDocument[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const res = await documentsAPI.list(1, 50);
      setDocuments(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = documents.filter((doc: CrmDocument) => {
    const term = search.toLowerCase();
    return !term || doc.filename.toLowerCase().includes(term);
  });

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const downloadDocument = async (doc: CrmDocument) => {
    try {
      const response = await api.get(
        `/crm/documents/${doc.id}/download`,
        { responseType: "blob" }
      );

      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = doc.filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search documents…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} documents</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <UploadCloud size={14} /> Upload
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {filtered.map(doc => (
              <div key={doc.id} className="flex flex-col p-4 rounded border border-border bg-card hover:border-primary/30 transition-colors group">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded bg-indigo-500/10 flex items-center justify-center">
                    <File size={20} className="text-indigo-500" />
                  </div>
                  <button className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hover:text-foreground">
                    <MoreHorizontal size={14} />
                  </button>
                </div>
                <h3 className="text-xs font-semibold text-foreground truncate mb-1" title={doc.filename}>{doc.filename}</h3>
                <div className="flex items-center justify-between mt-auto pt-2">
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {doc.file_size ? formatSize(doc.file_size) : "—"}
                  </span>
                  <button onClick={() => downloadDocument(doc)} className="text-primary hover:text-primary/80 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Download size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
