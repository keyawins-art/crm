import { useState, useEffect } from "react";
import { Search, Plus, MoreHorizontal, FileText, Send, Download, Eye } from "lucide-react";
import { quotationsAPI, salesAPI, accountsAPI, productsAPI } from "../../lib/api";

const statusConfig: Record<string, { color: string; bg: string }> = {
  draft:    { color: "#6b7694", bg: "#6b769418" },
  sent:     { color: "#4f7eff", bg: "#4f7eff18" },
  accepted: { color: "#00d4aa", bg: "#00d4aa18" },
  rejected: { color: "#f43f5e", bg: "#f43f5e18" },
};

export function Quotations() {
  const [quotations, setQuotations] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [accounts, setAccounts] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [pdfViewUrl, setPdfViewUrl] = useState<string | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  const getInitialFormState = () => ({
    quote_number: `QT-${new Date().getFullYear()}-${Math.floor(Math.random() * 10000)}`,
    subject: "",
    status: "draft",
    account_id: "",
    billing_address: "",
    shipping_address: "",
    terms_and_conditions: `* 1 Year Warranty
* 50% advance payment for order conformation & 50% before Dispatch
* Delivery Charges at actual
* Onsite Installation, Demo and Training (India) - Ensuring you fully understand the machine's capabilities
* Please note that the machine will be supplied with 2 Nos. of 20 kg moulds and 2 Nos. of 25 kg moulds included in our offer`,
    items: [
      { product_id: "", description: "", quantity: 1, unit_price: 0, tax_percent: 18 }
    ]
  });

  const [addFormData, setAddFormData] = useState(getInitialFormState());

  const handleAccountChange = (accountId: string) => {
    const selectedAcc = accounts.find(a => a.id === accountId);
    let addr = "";
    if (selectedAcc) {
      const parts = [];
      if (selectedAcc.billing_street) parts.push(selectedAcc.billing_street);
      if (selectedAcc.billing_city) parts.push(selectedAcc.billing_city);
      if (selectedAcc.billing_state) parts.push(selectedAcc.billing_state);
      if (selectedAcc.billing_postal_code) parts.push(selectedAcc.billing_postal_code);
      addr = parts.join(", ");
    }
    setAddFormData({
      ...addFormData,
      account_id: accountId,
      billing_address: addr,
      shipping_address: addr,
    });
  };

  useEffect(() => {
    loadQuotations();
    loadAccounts();
    loadProducts();
  }, []);

  const loadAccounts = async () => {
    try {
      const res = await accountsAPI.list(1, 100);
      setAccounts(res.data.items || []);
    } catch (err) {
      console.error("Failed to load accounts", err);
    }
  };

  const loadProducts = async () => {
    try {
      const res = await productsAPI.list(1, 100);
      setProducts(res.data.items || []);
    } catch (err) {
      console.error("Failed to load products", err);
    }
  };

  const loadQuotations = async () => {
    try {
      setLoading(true);
      const res = await quotationsAPI.list(1, 50);
      setQuotations(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load quotations:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToOrder = async (id: string) => {
    if (!window.confirm("Convert this quotation to a Sales Order?")) return;
    try {
      await salesAPI.convertToOrder(id);
      loadQuotations();
      alert("Converted successfully!");
    } catch (err) {
      console.error("Failed to convert to order:", err);
      alert("Failed to convert.");
    }
  };

  const handleAddQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = { ...addFormData };
      if (!payload.account_id) delete (payload as any).account_id;
      // Filter out invalid items
      payload.items = payload.items.filter(item => item.product_id !== "");
      
      await quotationsAPI.create(payload);
      setIsAddModalOpen(false);
      setAddFormData(getInitialFormState());
      loadQuotations();
    } catch (err) {
      console.error("Failed to create quotation:", err);
      alert("Failed to create quotation");
    }
  };

  const handleAddRow = () => {
    setAddFormData({
      ...addFormData,
      items: [...addFormData.items, { product_id: "", description: "", quantity: 1, unit_price: 0, tax_percent: 18 }]
    });
  };

  const handleRemoveRow = (index: number) => {
    const newItems = [...addFormData.items];
    newItems.splice(index, 1);
    setAddFormData({ ...addFormData, items: newItems });
  };

  const handleItemChange = (index: number, field: string, value: any) => {
    const newItems = [...addFormData.items];
    
    if (field === "product_id") {
      const selectedProd = products.find(p => p.id === value);
      newItems[index] = {
        ...newItems[index],
        product_id: value,
        unit_price: selectedProd ? (selectedProd.list_price || 0) : 0,
        description: selectedProd ? (selectedProd.description || "") : ""
      };
    } else {
      newItems[index] = {
        ...newItems[index],
        [field]: value
      };
    }
    
    setAddFormData({ ...addFormData, items: newItems });
  };

  // Calculate live totals for the invoice preview
  const calculateTotals = () => {
    let subtotal = 0;
    let tax = 0;
    addFormData.items.forEach(item => {
      if (!item.product_id) return;
      const amount = (item.quantity || 0) * (item.unit_price || 0);
      subtotal += amount;
      tax += amount * ((item.tax_percent || 0) / 100);
    });
    return { subtotal, tax, grandTotal: subtotal + tax };
  };

  const { subtotal: liveSubtotal, tax: liveTax, grandTotal: liveGrandTotal } = calculateTotals();

  const handleDownloadPDF = async (id: string, quoteNumber: string) => {
    try {
      const res = await quotationsAPI.downloadPdf(id);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${quoteNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("PDF download failed:", err);
      alert("Failed to download PDF");
    }
  };

  const handleViewQuotation = async (id: string) => {
    try {
      setLoadingDetails(true);
      const res = await quotationsAPI.downloadPdf(id);
      const fileURL = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      setPdfViewUrl(fileURL);
    } catch (err) {
      console.error("Failed to load PDF preview:", err);
      alert("Failed to load PDF preview.");
    } finally {
      setLoadingDetails(false);
    }
  };

  const filtered = quotations.filter(q => {
    const term = search.toLowerCase();
    return !term || 
           q.quote_number?.toLowerCase().includes(term) || 
           q.subject?.toLowerCase().includes(term) ||
           q.account?.name?.toLowerCase().includes(term);
  });

  const fmt = (v: number | null) => v != null ? `₹${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="flex flex-col h-full" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search quotations…"
            className="pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors w-64" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground mr-3">{total} quotations</span>
          <button onClick={() => setIsAddModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Quotation
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
                <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Quote #</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Customer</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Subject</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Total</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-20 px-3 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(q => {
                const st = statusConfig[q.status] || statusConfig.draft;
                return (
                  <tr key={q.id} className="border-b border-border hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-blue-500/10 flex items-center justify-center shrink-0">
                          <FileText size={13} className="text-blue-500" />
                        </div>
                        <span className="font-mono font-medium text-foreground">{q.quote_number}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-foreground font-medium">{q.account ? q.account.name : "—"}</td>
                    <td className="px-3 py-2.5 text-foreground">{q.subject}</td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize"
                        style={{ color: st.color, background: st.bg }}>
                        {q.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{fmt(q.grand_total)}</td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                      {q.created_at ? new Date(q.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <button onClick={() => handleViewQuotation(q.id)} title="View Details" className="text-primary hover:text-primary/80 mr-2 transition-colors">
                        <Eye size={14} />
                      </button>
                      <button onClick={() => handleDownloadPDF(q.id, q.quote_number)} title="Download PDF" className="text-blue-500 hover:text-blue-400 mr-2 transition-colors">
                        <Download size={14} />
                      </button>
                      {q.status === 'accepted' ? (
                        <button onClick={() => handleConvertToOrder(q.id)} title="Convert to Order" className="text-emerald-500 hover:text-emerald-400 mr-2">
                          <Send size={14} />
                        </button>
                      ) : null}
                      <button className="text-muted-foreground hover:text-foreground">
                        <MoreHorizontal size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Quotation / Invoice Builder Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-5xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <div>
                <h3 className="text-base font-semibold text-foreground">Create Quotation</h3>
                <p className="text-xs text-muted-foreground">Fill in all details to generate a formatted PDF Quotation matching Keya Fusion standards.</p>
              </div>
              <button onClick={() => setIsAddModalOpen(false)} className="text-muted-foreground hover:text-foreground text-sm transition-colors">✕</button>
            </div>
            
            <form onSubmit={handleAddQuotation} className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
              {/* Top Meta info */}
              <div className="grid grid-cols-4 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Quote Number</label>
                  <input required value={addFormData.quote_number} onChange={e => setAddFormData({...addFormData, quote_number: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" />
                </div>
                <div className="flex flex-col gap-1.5 col-span-2">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Subject / Machine Model Name</label>
                  <input required value={addFormData.subject} onChange={e => setAddFormData({...addFormData, subject: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" placeholder="e.g. Vertical Chamber Vacuum Packing Machine" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</label>
                  <select value={addFormData.status} onChange={e => setAddFormData({...addFormData, status: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground capitalize">
                    {Object.keys(statusConfig).map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Customer / Account</label>
                  <select required value={addFormData.account_id} onChange={e => handleAccountChange(e.target.value)} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                    <option value="">Select Customer</option>
                    {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                </div>
              </div>

              {/* Billing and Shipping Address Overrides */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Billing Address</label>
                  <textarea rows={2} value={addFormData.billing_address} onChange={e => setAddFormData({...addFormData, billing_address: e.target.value})} className="px-3 py-1.5 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground leading-normal" placeholder="Customer billing address details..." />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Shipping Address</label>
                  <textarea rows={2} value={addFormData.shipping_address} onChange={e => setAddFormData({...addFormData, shipping_address: e.target.value})} className="px-3 py-1.5 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground leading-normal" placeholder="Customer shipping address details..." />
                </div>
              </div>

              {/* Dynamic Items Builder */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Line Items</label>
                  <button type="button" onClick={handleAddRow} className="flex items-center gap-1 px-2.5 py-1 bg-primary/10 text-primary hover:bg-primary/20 rounded text-[11px] font-medium transition-colors">
                    <Plus size={12} /> Add Item Row
                  </button>
                </div>

                <div className="border border-border rounded overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-muted/40 border-b border-border text-[10px] uppercase font-semibold text-muted-foreground">
                        <th className="px-3 py-2 text-left w-[30%]">Product</th>
                        <th className="px-3 py-2 text-left w-[30%]">Description / Details</th>
                        <th className="px-3 py-2 text-right w-[10%]">Qty</th>
                        <th className="px-3 py-2 text-right w-[12%]">Rate (₹)</th>
                        <th className="px-3 py-2 text-right w-[8%]">IGST (%)</th>
                        <th className="px-3 py-2 text-right w-[12%]">Amount (₹)</th>
                        <th className="px-2 py-2 text-center w-[5%]"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {addFormData.items.map((item, index) => {
                        const amount = (item.quantity || 0) * (item.unit_price || 0);
                        const tax = amount * ((item.tax_percent || 0) / 100);
                        const totalLine = amount + tax;
                        return (
                          <tr key={index} className="border-b border-border last:border-0">
                            <td className="px-3 py-2">
                              <select required value={item.product_id} onChange={e => handleItemChange(index, "product_id", e.target.value)} className="w-full px-2 py-1 bg-secondary/30 border border-border rounded text-xs text-foreground focus:outline-none focus:border-primary">
                                <option value="">Select Product</option>
                                {products.map(p => <option key={p.id} value={p.id}>{p.name} {p.code ? `(${p.code})` : ""}</option>)}
                              </select>
                            </td>
                            <td className="px-3 py-2">
                              <input value={item.description} onChange={e => handleItemChange(index, "description", e.target.value)} className="w-full px-2 py-1 bg-secondary/30 border border-border rounded text-xs text-foreground focus:outline-none focus:border-primary" placeholder="e.g. Capacity: 1kg - 25kg" />
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" required min="1" value={item.quantity} onChange={e => handleItemChange(index, "quantity", Number(e.target.value))} className="w-full px-2 py-1 bg-secondary/30 border border-border rounded text-xs text-right text-foreground focus:outline-none focus:border-primary" />
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" required min="0" step="0.01" value={item.unit_price} onChange={e => handleItemChange(index, "unit_price", Number(e.target.value))} className="w-full px-2 py-1 bg-secondary/30 border border-border rounded text-xs text-right text-foreground focus:outline-none focus:border-primary" />
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" required min="0" value={item.tax_percent} onChange={e => handleItemChange(index, "tax_percent", Number(e.target.value))} className="w-full px-2 py-1 bg-secondary/30 border border-border rounded text-xs text-right text-foreground focus:outline-none focus:border-primary" />
                            </td>
                            <td className="px-3 py-2 text-right font-mono font-semibold text-foreground">
                              ₹{totalLine.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td className="px-2 py-2 text-center">
                              {addFormData.items.length > 1 && (
                                <button type="button" onClick={() => handleRemoveRow(index)} className="text-rose-500 hover:text-rose-400">✕</button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Terms and Live calculation totals */}
              <div className="grid grid-cols-3 gap-6 border-t border-border pt-4">
                <div className="col-span-2 flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Terms &amp; Conditions</label>
                  <textarea rows={5} value={addFormData.terms_and_conditions} onChange={e => setAddFormData({...addFormData, terms_and_conditions: e.target.value})} className="w-full px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono leading-relaxed" />
                </div>
                
                <div className="bg-muted/10 border border-border rounded p-4 flex flex-col gap-3 justify-center">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Subtotal:</span>
                    <span className="font-mono">₹{liveSubtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Add IGST:</span>
                    <span className="font-mono">₹{liveTax.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold text-foreground border-t border-border pt-2 mt-1">
                    <span>Grand Total:</span>
                    <span className="font-mono text-primary">₹{liveGrandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-border">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors">Create &amp; Save Quotation</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loading Details Spinner Overlay */}
      {loadingDetails && (
        <div className="fixed inset-0 bg-background/50 backdrop-blur-xs z-50 flex items-center justify-center">
          <span className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>
      )}

      {/* View Quotation Details Modal (PDF preview) */}
      {pdfViewUrl && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-5xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[95vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <div>
                <h3 className="text-base font-semibold text-foreground">Quotation PDF Preview</h3>
                <p className="text-xs text-muted-foreground">Print or download the quotation document directly using the PDF toolbar.</p>
              </div>
              <button onClick={() => { URL.revokeObjectURL(pdfViewUrl); setPdfViewUrl(null); }} className="text-muted-foreground hover:text-foreground text-sm transition-colors">✕</button>
            </div>

            <div className="flex-1 p-2 bg-secondary/20">
              <iframe src={pdfViewUrl} className="w-full h-[78vh] rounded border border-border bg-muted" />
            </div>
            
            <div className="flex justify-end gap-2 px-6 py-4 border-t border-border bg-muted/10">
              <button onClick={() => { URL.revokeObjectURL(pdfViewUrl); setPdfViewUrl(null); }} className="px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary rounded transition-colors">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
