import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, Package, Edit, Trash } from "lucide-react";
import { productsAPI } from "../../lib/api";

export function Products() {
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<any | null>(null);
  
  const getInitialFormState = () => ({
    name: "",
    code: "",
    description: "",
    category: "",
    status: "active",
    list_price: 0,
    cost_price: 0,
    currency: "INR"
  });

  const [formData, setFormData] = useState(getInitialFormState());

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const res = await productsAPI.list(1, 100);
      setProducts(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        await productsAPI.update(editingProduct.id, formData);
      } else {
        await productsAPI.create(formData);
      }
      setIsModalOpen(false);
      setEditingProduct(null);
      setFormData(getInitialFormState());
      loadProducts();
    } catch (err) {
      console.error("Failed to save product:", err);
      alert("Failed to save product details.");
    }
  };

  const handleEdit = (prod: any) => {
    setEditingProduct(prod);
    setFormData({
      name: prod.name || "",
      code: prod.code || "",
      description: prod.description || "",
      category: prod.category || "",
      status: prod.status || "active",
      list_price: prod.list_price || 0,
      cost_price: prod.cost_price || 0,
      currency: prod.currency || "INR"
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this product?")) return;
    try {
      await productsAPI.delete(id);
      loadProducts();
    } catch (err) {
      console.error("Failed to delete product:", err);
      alert("Failed to delete product.");
    }
  };

  const filtered = products.filter(p => {
    const term = search.toLowerCase();
    return !term || p.name?.toLowerCase().includes(term) || p.code?.toLowerCase().includes(term) || p.category?.toLowerCase().includes(term);
  });

  const fmt = (v: number | null) => v != null ? `₹${Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0 bg-card">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search product catalog…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} Products</span>
          <button onClick={() => { setEditingProduct(null); setFormData(getInitialFormState()); setIsModalOpen(true); }} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> Add Product
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Product Name / Code</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Category</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Description</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">List Price</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Cost Price</th>
                <th className="w-20 px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded bg-primary/10 flex items-center justify-center shrink-0">
                        <Package size={13} className="text-primary" />
                      </div>
                      <div>
                        <div className="font-semibold text-foreground">{p.name}</div>
                        {p.code && <div className="text-[10px] font-mono text-muted-foreground">{p.code}</div>}
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-foreground capitalize">{p.category || "—"}</td>
                  <td className="px-3 py-2.5 text-muted-foreground max-w-[200px] truncate" title={p.description}>{p.description || "—"}</td>
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-foreground">{fmt(p.list_price)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-muted-foreground">{fmt(p.cost_price)}</td>
                  <td className="px-3 py-2.5 text-right flex justify-end gap-1.5">
                    <button onClick={() => handleEdit(p)} title="Edit" className="p-1 hover:bg-secondary rounded text-muted-foreground hover:text-foreground transition-colors">
                      <Edit size={13} />
                    </button>
                    <button onClick={() => handleDelete(p.id)} title="Delete" className="p-1 hover:bg-secondary rounded text-rose-500 hover:text-rose-400 transition-colors">
                      <Trash size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add / Edit Product Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">{editingProduct ? "Edit Product" : "Add Product to Catalog"}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors">✕</button>
            </div>
            <form onSubmit={handleCreateOrUpdate} className="p-4 flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Product Name</label>
                <input required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="e.g. Vacuum Packing Machine" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">HSN / SAC Code</label>
                  <input value={formData.code} onChange={e => setFormData({...formData, code: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" placeholder="e.g. 84224000" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Category</label>
                  <input value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="e.g. Machinery" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">List Price (₹)</label>
                  <input type="number" step="0.01" min="0" required value={formData.list_price} onChange={e => setFormData({...formData, list_price: Number(e.target.value)})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono text-right" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Cost Price (₹)</label>
                  <input type="number" step="0.01" min="0" required value={formData.cost_price} onChange={e => setFormData({...formData, cost_price: Number(e.target.value)})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono text-right" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Description / Details</label>
                <textarea rows={3} value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground leading-normal" placeholder="e.g. Capacity: 1kg - 25kg, Vertical Chamber Type" />
              </div>
              <div className="flex justify-end gap-2 mt-2 pt-4 border-t border-border">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Cancel</button>
                <button type="submit" className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">{editingProduct ? "Save Changes" : "Add Product"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
