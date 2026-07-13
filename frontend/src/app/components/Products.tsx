import { useState, useEffect } from "react";
import { Search, Plus, Package, Edit, Trash, Upload, X, Check, FileIcon } from "lucide-react";
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
    currency: "INR",
    image_url: "",
    specifications: {} as Record<string, string>
  });

  const [formData, setFormData] = useState(getInitialFormState());
  const [specList, setSpecList] = useState<{key: string, value: string}[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);

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

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    const data = new FormData();
    data.append("file", file);
    data.append("title", file.name);
    try {
      setUploadingImage(true);
      const res = await productsAPI.uploadImage(data);
      // Assuming the backend returns the document info with a file_path or url
      const url = res.data.file_path || res.data.url || "";
      setFormData({ ...formData, image_url: url });
    } catch (err: any) {
      console.error(err);
      alert(`Image upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUploadingImage(false);
    }
  };

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Convert specList array back to object
      const specObj: Record<string, string> = {};
      specList.forEach(s => {
        if (s.key.trim() && s.value.trim()) {
          specObj[s.key.trim()] = s.value.trim();
        }
      });
      
      const payload = { ...formData, specifications: specObj };
      
      // Clean empty strings to null for optional enums
      if (!payload.category) delete payload.category;
      if (!payload.code) delete payload.code;
      if (!payload.description) delete payload.description;

      if (editingProduct) {
        await productsAPI.update(editingProduct.id, payload);
      } else {
        await productsAPI.create(payload);
      }
      setIsModalOpen(false);
      setEditingProduct(null);
      setFormData(getInitialFormState());
      setSpecList([]);
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
      currency: prod.currency || "INR",
      image_url: prod.image_url || "",
      specifications: prod.specifications || {}
    });
    
    // Convert object to array for the form
    const specs = prod.specifications || {};
    const specArray = Object.keys(specs).map(k => ({ key: k, value: specs[k] }));
    setSpecList(specArray.length > 0 ? specArray : [{ key: "", value: "" }]);
    
    setIsModalOpen(true);
  };

  const openAddModal = () => {
    setEditingProduct(null);
    setFormData(getInitialFormState());
    setSpecList([{ key: "", value: "" }]);
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
          <button onClick={openAddModal} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> Add Product
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-background">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filtered.map(p => (
              <div key={p.id} className="bg-card border border-border rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow flex flex-col group">
                <div className="h-48 bg-secondary/30 relative flex items-center justify-center border-b border-border overflow-hidden">
                  {p.image_url ? (
                     <img src={`http://localhost:8000${p.image_url}`} onError={(e) => (e.currentTarget.src = p.image_url)} alt={p.name} className="w-full h-full object-cover" />
                  ) : (
                    <Package size={48} className="text-muted-foreground/30" />
                  )}
                  <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEdit(p)} className="p-1.5 bg-background/90 backdrop-blur-sm rounded-full text-foreground hover:bg-primary hover:text-white transition-colors shadow-sm">
                      <Edit size={14} />
                    </button>
                    <button onClick={() => handleDelete(p.id)} className="p-1.5 bg-background/90 backdrop-blur-sm rounded-full text-rose-500 hover:bg-rose-500 hover:text-white transition-colors shadow-sm">
                      <Trash size={14} />
                    </button>
                  </div>
                </div>
                <div className="p-4 flex flex-col flex-1">
                  <div className="flex justify-between items-start gap-2 mb-2">
                    <h3 className="font-bold text-foreground text-sm line-clamp-2">{p.name}</h3>
                  </div>
                  <div className="flex gap-2 mb-4">
                    {p.code && <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-mono rounded font-bold">{p.code}</span>}
                    {p.category && <span className="px-2 py-0.5 bg-secondary text-muted-foreground text-[10px] rounded capitalize">{p.category}</span>}
                  </div>
                  
                  <div className="flex-1">
                    {p.specifications && Object.keys(p.specifications).length > 0 ? (
                      <div className="space-y-1.5">
                        {Object.entries(p.specifications).slice(0, 3).map(([k, v]) => (
                          <div key={k} className="flex justify-between text-xs">
                            <span className="text-muted-foreground">{k}:</span>
                            <span className="font-medium text-foreground text-right w-1/2 truncate" title={String(v)}>{String(v)}</span>
                          </div>
                        ))}
                        {Object.keys(p.specifications).length > 3 && (
                          <p className="text-[10px] text-primary/80 mt-1 cursor-pointer hover:underline" onClick={() => handleEdit(p)}>+{Object.keys(p.specifications).length - 3} more specs</p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground line-clamp-3">{p.description || "No description or specs available."}</p>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-border flex justify-between items-center shrink-0">
                    <div>
                      <p className="font-bold text-foreground capitalize">{p.category || "General"}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full py-24 text-center">
                <Package size={32} className="mx-auto text-muted-foreground/30 mb-3" />
                <p className="text-sm text-muted-foreground font-medium">No products found</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add / Edit Product Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/20">
              <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                <Package size={18} className="text-primary"/> 
                {editingProduct ? "Edit Product" : "Add Product to Catalog"}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="p-1.5 hover:bg-secondary rounded-full text-muted-foreground hover:text-foreground transition-colors"><X size={16}/></button>
            </div>
            
            <form onSubmit={handleCreateOrUpdate} className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column: Basic Info & Image */}
                <div className="space-y-5">
                  <div>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border pb-2">Basic Information</h4>
                    <div className="space-y-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-foreground">Product Name *</label>
                        <input required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" placeholder="e.g. Vacuum Packing Machine" />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1.5">
                          <label className="text-xs font-semibold text-foreground">Model / Code</label>
                          <input value={formData.code} onChange={e => setFormData({...formData, code: e.target.value})} className="px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground font-mono" placeholder="e.g. VPM-100" />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <label className="text-xs font-semibold text-foreground">Category</label>
                          <select 
                            value={formData.category} 
                            onChange={e => setFormData({...formData, category: e.target.value})} 
                            className="px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground"
                          >
                            <option value="">Select Category...</option>
                            <option value="hardware">Hardware</option>
                            <option value="software">Software</option>
                            <option value="service">Service</option>
                            <option value="subscription">Subscription</option>
                            <option value="consulting">Consulting</option>
                            <option value="support">Support</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 gap-4">
                        <div className="flex flex-col gap-1.5 hidden">
                          <label className="text-xs font-semibold text-foreground">List Price (₹)</label>
                          <input type="number" step="0.01" min="0" value={formData.list_price || 0} onChange={e => setFormData({...formData, list_price: Number(e.target.value)})} className="px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground font-mono" />
                        </div>
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-foreground">Description</label>
                        <textarea rows={3} value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground resize-none" placeholder="Short description of the product..." />
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border pb-2">Product Image</h4>
                    <div className="flex items-center gap-4">
                      <div className="w-24 h-24 rounded-lg bg-secondary/50 border border-border flex items-center justify-center overflow-hidden shrink-0">
                        {formData.image_url ? (
                          <img src={formData.image_url.startsWith('http') ? formData.image_url : `http://localhost:8000${formData.image_url}`} alt="Preview" className="w-full h-full object-cover" />
                        ) : (
                          <Package size={24} className="text-muted-foreground/30" />
                        )}
                      </div>
                      <div className="flex-1 space-y-2">
                        <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-md text-sm font-semibold hover:bg-primary/20 transition-colors">
                          {uploadingImage ? <span className="animate-spin border-2 border-primary/30 border-t-primary rounded-full w-4 h-4"/> : <Upload size={16} />}
                          Upload Photo
                          <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} disabled={uploadingImage} />
                        </label>
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-muted-foreground">Or paste image URL:</span>
                          <input value={formData.image_url} onChange={e => setFormData({...formData, image_url: e.target.value})} className="px-3 py-1.5 bg-secondary/30 border border-border rounded-md text-xs focus:outline-none focus:border-primary text-foreground w-full font-mono" placeholder="https://..." />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column: Specifications */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-2 mb-4">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Specifications</h4>
                    <button type="button" onClick={() => setSpecList([...specList, { key: "", value: "" }])} className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
                      <Plus size={12}/> Add Spec
                    </button>
                  </div>
                  
                  <div className="space-y-3 max-h-[450px] overflow-y-auto pr-2">
                    {specList.map((spec, i) => (
                      <div key={i} className="flex gap-2 items-start">
                        <div className="flex-1">
                          <input value={spec.key} onChange={e => { const n = [...specList]; n[i].key = e.target.value; setSpecList(n); }} className="w-full px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground mb-1" placeholder="e.g. Capacity" />
                        </div>
                        <div className="flex-1">
                          <input value={spec.value} onChange={e => { const n = [...specList]; n[i].value = e.target.value; setSpecList(n); }} className="w-full px-3 py-2 bg-secondary/30 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground mb-1" placeholder="e.g. 50 kg/hr" />
                        </div>
                        <button type="button" onClick={() => { const n = [...specList]; n.splice(i, 1); setSpecList(n); }} className="p-2 text-rose-500 hover:bg-rose-500/10 rounded-md transition-colors mt-0.5">
                          <Trash size={16} />
                        </button>
                      </div>
                    ))}
                    {specList.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed border-border rounded-lg">
                        No specifications added. Click "Add Spec" to start.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-border">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-sm font-semibold text-foreground hover:bg-secondary rounded-md transition-colors">Cancel</button>
                <button type="submit" className="px-5 py-2.5 text-sm font-semibold bg-primary text-white rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2">
                  <Check size={16} />
                  {editingProduct ? "Save Changes" : "Create Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
