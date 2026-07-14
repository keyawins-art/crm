import { useState, useEffect } from "react";
import {
  Search, Plus, Filter, MoreHorizontal, Download,
  Package, Truck, CheckCircle2, XCircle, Clock, AlertCircle,
  ChevronDown, ChevronRight, X, FileText, ArrowRight,
  MapPin, Calendar, DollarSign, Hash, User2, Building2,
  Printer, RefreshCw, TrendingUp, ShoppingCart, Star
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { salesAPI } from "../../lib/api";
import { getUser } from "../../lib/auth";

// ── Types ────────────────────────────────────────────────────────
type OrderStatus = "draft" | "confirmed" | "processing" | "shipped" | "delivered" | "cancelled";

type LineItem = {
  product_id?: string;
  sku: string;
  product: string;
  category: string;
  qty: number;
  unitPrice: number;
  discount: number;
};

type Order = {
  id: string;
  number: string;
  customer: string;
  customerInitials: string;
  customerColor: string;
  company: string;
  email: string;
  phone: string;
  status: OrderStatus;
  priority: "Standard" | "Express" | "Urgent";
  orderDate: string;
  shipDate: string;
  deliveryDate: string;
  shipTo: string;
  items: LineItem[];
  notes?: string;
  rawOrderDate?: string;
  rawShipDate?: string;
  rawDeliveryDate?: string;
  assignee: string;
  assigneeInitials: string;
  paymentStatus: "Pending" | "Paid" | "Overdue";
  paymentMethod: string;
  tags?: string[];
  assignee_id?: string;
};

// ── Config ───────────────────────────────────────────────────────
const statusConfig: Record<OrderStatus, { color: string; bg: string; icon: React.ComponentType<{ size?: number }> }> = {
  draft:      { color: "#6b7694", bg: "#6b769418", icon: FileText     },
  confirmed:  { color: "#4f7eff", bg: "#4f7eff18", icon: CheckCircle2 },
  processing: { color: "#a78bfa", bg: "#a78bfa18", icon: RefreshCw    },
  shipped:    { color: "#f59e0b", bg: "#f59e0b18", icon: Truck        },
  delivered:  { color: "#00d4aa", bg: "#00d4aa18", icon: Package      },
  cancelled:  { color: "#f43f5e", bg: "#f43f5e18", icon: XCircle      },
};

const priorityConfig: Record<string, { color: string; bg: string }> = {
  Standard: { color: "#6b7694", bg: "#6b769415" },
  Express:  { color: "#f59e0b", bg: "#f59e0b15" },
  Urgent:   { color: "#f43f5e", bg: "#f43f5e15" },
};

const paymentConfig: Record<string, { color: string; bg: string }> = {
  Paid:    { color: "#00d4aa", bg: "#00d4aa15" },
  Pending: { color: "#f59e0b", bg: "#f59e0b15" },
  Overdue: { color: "#f43f5e", bg: "#f43f5e15" },
};

const statusFlow: OrderStatus[] = ["draft", "confirmed", "processing", "shipped", "delivered"];

// ── Helpers ──────────────────────────────────────────────────────
const calcOrderTotal = (items: LineItem[]) =>
  items.reduce((s, i) => s + i.qty * i.unitPrice * (1 - i.discount / 100), 0);

const fmt = (n: number) =>
  n >= 1000 ? `$${n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : `$${n}`;

const monthlyData = [
  { month: "Jan", orders: 18, revenue: 312 },
  { month: "Feb", orders: 22, revenue: 428 },
  { month: "Mar", orders: 19, revenue: 381 },
  { month: "Apr", orders: 31, revenue: 594 },
  { month: "May", orders: 27, revenue: 512 },
  { month: "Jun", orders: 24, revenue: 488 },
];

const ChartTip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-card px-3 py-2 text-xs shadow-xl">
      <p className="text-muted-foreground mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.stroke || p.fill }} className="font-semibold">
          {p.name}: {p.dataKey === "revenue" ? `$${p.value}k` : p.value}
        </p>
      ))}
    </div>
  );
};

// ── Component ────────────────────────────────────────────────────
type StatusFilter = OrderStatus | "All";

export function SalesOrders() {
  const [search, setSearch]           = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("All");
  const [orders, setOrders]           = useState<Order[]>([]);
  const [selected, setSelected]       = useState<Order | null>(null);
  const [showCharts, setShowCharts]   = useState(true);
  const [loading, setLoading]         = useState(true);
  const [isEditing, setIsEditing]     = useState(false);
  const [editForm, setEditForm]       = useState<Partial<Order>>({});
  const [isDownloading, setIsDownloading] = useState(false);

  const currentUser = getUser();
  const canEditOrder = (order: Order) => {
    if (!currentUser) return false;
    if (currentUser.role === 'admin' || currentUser.role === 'support') return true;
    return order.assignee_id === currentUser.id;
  };

  const statuses: StatusFilter[] = ["All", "draft", "confirmed", "processing", "shipped", "delivered", "cancelled"];

  const loadOrders = async () => {
    try {
      setLoading(true);
      const res = await salesAPI.salesOrders(1, 100);
      const items = res.data.items || [];
      
      const mappedOrders: Order[] = items.map((o: any) => {
        // Safe mapping
        const acct = o.account || {};
        const opp = o.opportunity || {};
        const q = o.quotation || {};
        const first = acct.name ? acct.name[0].toUpperCase() : (opp.name ? opp.name[0].toUpperCase() : "U");
        
        return {
          id: o.id,
          number: o.order_number,
          customer: acct.name || "Unknown Account",
          customerInitials: first,
          customerColor: "#4f7eff", // We could generate a dynamic color based on string
          company: acct.industry || "Unknown",
          email: acct.email || "—",
          phone: acct.phone || "—",
          status: (o.status || "draft").toLowerCase() as OrderStatus,
          priority: o.priority || "Standard",
          orderDate: o.order_date ? new Date(o.order_date).toLocaleDateString('en-GB') : (o.created_at ? new Date(o.created_at).toLocaleDateString('en-GB') : "—"),
          shipDate: o.ship_date ? new Date(o.ship_date).toLocaleDateString('en-GB') : "—",
          deliveryDate: o.delivery_date ? new Date(o.delivery_date).toLocaleDateString('en-GB') : "—",
          rawOrderDate: o.order_date || o.created_at,
          rawShipDate: o.ship_date,
          rawDeliveryDate: o.delivery_date,
          shipTo: o.ship_to || acct.billing_city || "—",
          notes: o.notes || "",
          assignee: o.assignee ? `${o.assignee.first_name} ${o.assignee.last_name}` : "Unassigned",
          assigneeInitials: o.assignee ? o.assignee.first_name[0] : "U",
          assignee_id: o.assignee_id,
          paymentStatus: o.payment_status || "Pending",
          paymentMethod: o.payment_method || "—",
          tags: o.tags || [],
          items: (o.items || []).map((i: any) => ({
            product_id: i.product_id,
            sku: i.sku || "N/A",
            product: i.product_name,
            category: i.category || "General",
            qty: parseFloat(i.quantity) || 0,
            unitPrice: parseFloat(i.unit_price) || 0,
            discount: parseFloat(i.discount_percent) || 0
          }))
        };
      });
      
      setOrders(mappedOrders);
      if (mappedOrders.length > 0 && !selected) {
        setSelected(mappedOrders[0]);
      }
    } catch (err) {
      console.error("Failed to load orders", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleUpdateStatus = async (status: OrderStatus) => {
    if (!selected) return;
    try {
      await salesAPI.updateSalesOrder(selected.id, { status });
      // update local
      const updated = { ...selected, status };
      setSelected(updated);
      setOrders(orders.map(o => o.id === updated.id ? updated : o));
    } catch (e) {
      console.error(e);
      alert("Failed to update status");
    }
  };

  const handleDownloadPdf = async (id: string) => {
    try {
      setIsDownloading(true);
      const res = await salesAPI.downloadPdf(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `SalesOrder_${id.substring(0,8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (error) {
      console.error("Error downloading PDF", error);
      alert("Failed to download PDF");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleEditOrder = () => {
    if (!selected) return;
    setEditForm({
      priority: selected.priority,
      rawOrderDate: selected.rawOrderDate,
      rawShipDate: selected.rawShipDate,
      rawDeliveryDate: selected.rawDeliveryDate,
      shipTo: selected.shipTo,
      notes: selected.notes,
      paymentMethod: selected.paymentMethod,
      items: selected.items.map(i => ({ ...i }))
    });
    setIsEditing(true);
  };
  
  const handleItemChange = (index: number, field: keyof LineItem, value: any) => {
    setEditForm(prev => {
      const items = [...(prev.items || [])];
      items[index] = { ...items[index], [field]: value };
      return { ...prev, items };
    });
  };

  const addItem = () => {
    setEditForm(prev => ({
      ...prev,
      items: [...(prev.items || []), { product_id: "", sku: "", product: "", category: "General", qty: 1, unitPrice: 0, discount: 0 }]
    }));
  };

  const removeItem = (index: number) => {
    setEditForm(prev => ({
      ...prev,
      items: (prev.items || []).filter((_, i) => i !== index)
    }));
  };

  const handleSaveOrder = async () => {
    if (!selected) return;
    try {
      const payload: any = {
        priority: editForm.priority,
        ship_to: editForm.shipTo,
        notes: editForm.notes,
        payment_method: editForm.paymentMethod,
        items: (editForm.items || []).map(i => ({
          product_id: i.product_id || null,
          sku: i.sku,
          product_name: i.product,
          category: i.category,
          quantity: i.qty,
          unit_price: i.unitPrice,
          discount_percent: i.discount
        }))
      };
      
      if (editForm.rawOrderDate) payload.order_date = new Date(editForm.rawOrderDate).toISOString().split('T')[0];
      if (editForm.rawShipDate) payload.ship_date = new Date(editForm.rawShipDate).toISOString().split('T')[0];
      if (editForm.rawDeliveryDate) payload.delivery_date = new Date(editForm.rawDeliveryDate).toISOString().split('T')[0];
      
      await salesAPI.updateSalesOrder(selected.id, payload);
      setIsEditing(false);
      loadOrders();
    } catch(err) {
      console.error(err);
      alert("Failed to update order");
    }
  };

  const filtered = orders.filter(o => {
    const q = search.toLowerCase();
    const matchQ = !q || o.number.toLowerCase().includes(q) || o.customer.toLowerCase().includes(q) || o.company.toLowerCase().includes(q);
    const matchS = statusFilter === "All" || o.status === statusFilter;
    return matchQ && matchS;
  });

  const totalRevenue = orders.filter(o => o.status !== "cancelled").reduce((s, o) => s + calcOrderTotal(o.items), 0);
  
  // Build dynamic status breakdown
  const statusCounts = orders.reduce((acc, o) => {
    acc[o.status] = (acc[o.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const statusBreakdown = Object.keys(statusConfig).map(st => ({
    status: st as OrderStatus,
    count: statusCounts[st] || 0,
    color: statusConfig[st as OrderStatus].color
  })).filter(s => s.count > 0);

  return (
    <div className="flex h-full" style={{ fontFamily: "var(--font-sans)" }}>

      {/* ── Left panel: list ── */}
      <div className="flex flex-col w-[420px] border-r border-border shrink-0 bg-background">

        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-border">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-sm font-semibold text-foreground">Sales Orders</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCharts(s => !s)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
                title="Toggle charts"
              >
                <TrendingUp size={14} />
              </button>
              <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-lg hover:bg-primary/90 transition-colors">
                <Plus size={12} /> New Order
              </button>
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">{orders.length} orders · {fmt(totalRevenue)} total</p>
        </div>

        {/* Mini charts */}
        {showCharts && (
          <div className="px-4 py-3 border-b border-border bg-card/30 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              {/* Revenue sparkline */}
              <div className="rounded-lg border border-border bg-card p-2.5">
                <p className="text-[10px] text-muted-foreground mb-1">Revenue (MTD)</p>
                <p className="text-sm font-semibold text-foreground">{fmt(totalRevenue)}</p>
                <ResponsiveContainer width="100%" height={28}>
                  <AreaChart data={monthlyData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="soRev" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f7eff" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#4f7eff" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="revenue" stroke="#4f7eff" strokeWidth={1.5} fill="url(#soRev)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              {/* Orders sparkline */}
              <div className="rounded-lg border border-border bg-card p-2.5">
                <p className="text-[10px] text-muted-foreground mb-1">Orders (MTD)</p>
                <p className="text-sm font-semibold text-foreground">{orders.length}</p>
                <ResponsiveContainer width="100%" height={28}>
                  <AreaChart data={monthlyData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="soOrd" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="orders" stroke="#00d4aa" strokeWidth={1.5} fill="url(#soOrd)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Status breakdown */}
            <div>
              <p className="text-[10px] text-muted-foreground mb-1.5">Orders by Status</p>
              <div className="flex gap-0.5 h-1.5 rounded-full overflow-hidden">
                {statusBreakdown.map(s => (
                  <div
                    key={s.status}
                    title={`${s.status}: ${s.count}`}
                    style={{ flex: s.count, background: s.color }}
                  />
                ))}
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
                {statusBreakdown.map(s => (
                  <span key={s.status} className="flex items-center gap-1 text-[10px] text-muted-foreground capitalize">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color }} />
                    {s.status} ({s.count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Search + filter */}
        <div className="px-4 pt-3 pb-2 border-b border-border space-y-2">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search orders, customers…"
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white/5 border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>
          <div className="flex gap-1 overflow-x-auto">
            {statuses.map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-2 py-1 text-[10px] font-medium rounded-md whitespace-nowrap transition-colors shrink-0 capitalize ${statusFilter === s ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground hover:bg-white/5"}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Order list */}
        <div className="flex-1 overflow-y-auto divide-y divide-border">
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            </div>
          ) : filtered.map(order => {
            const { color, bg, icon: StatusIcon } = statusConfig[order.status];
            const total = calcOrderTotal(order.items);
            const isSelected = selected?.id === order.id;
            return (
              <button
                key={order.id}
                onClick={() => setSelected(order)}
                className={`w-full flex items-start gap-3 px-4 py-3.5 text-left transition-colors ${isSelected ? "bg-primary/8 border-r-2 border-primary" : "hover:bg-white/[0.025]"}`}
                style={isSelected ? { borderRightColor: "#4f7eff" } : {}}
              >
                {/* Avatar */}
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-[11px] font-bold shrink-0"
                  style={{ background: order.customerColor }}
                >
                  {order.customerInitials}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-foreground">{order.number}</span>
                      {order.priority !== "Standard" && priorityConfig[order.priority] && (
                        <span
                          className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full"
                          style={{ color: priorityConfig[order.priority].color, background: priorityConfig[order.priority].bg }}
                        >
                          {order.priority}
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-[11px] text-muted-foreground truncate">{order.customer} · {order.company}</p>

                  <div className="flex items-center justify-between mt-1.5">
                    <span
                      className="flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full capitalize"
                      style={{ color, background: bg }}
                    >
                      <StatusIcon size={9} />
                      {order.status}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground">{order.orderDate}</span>
                  </div>
                </div>
              </button>
            );
          })}

          {!loading && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <ShoppingCart size={28} className="opacity-20 mb-2" />
              <p className="text-xs">No orders match your search</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Right panel: detail ── */}
      {selected ? (
        <div className="flex-1 overflow-auto bg-background">
          <div className="max-w-3xl mx-auto p-6 space-y-5">

            {/* Order header */}
            <div className="bg-card rounded-2xl border border-border overflow-hidden">
              {/* Accent stripe */}
              <div
                className="h-1"
                style={{
                  background: `linear-gradient(to right, ${statusConfig[selected.status].color}, ${selected.customerColor})`,
                }}
              />

              <div className="p-6">
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-base shrink-0"
                      style={{ background: selected.customerColor }}
                    >
                      {selected.customerInitials}
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h2 className="text-lg font-semibold text-foreground">{selected.number}</h2>
                        {(() => {
                          const { color, bg, icon: StatusIcon } = statusConfig[selected.status];
                          return (
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold capitalize" style={{ color, background: bg }}>
                              <StatusIcon size={11} />{selected.status}
                            </span>
                          );
                        })()}
                        {selected.priority !== "Standard" && priorityConfig[selected.priority] && (
                          <span
                            className="px-2.5 py-1 rounded-full text-[11px] font-semibold"
                            style={{ color: priorityConfig[selected.priority].color, background: priorityConfig[selected.priority].bg }}
                          >
                            {selected.priority} Priority
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{selected.customer} · {selected.company}</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button className="p-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors">
                      <Printer size={14} />
                    </button>
                    <button 
                      onClick={() => handleDownloadPdf(selected.id)}
                      className="p-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors">
                      <Download size={14} />
                    </button>
                    {canEditOrder(selected) && (
                      <button 
                        onClick={handleEditOrder}
                        className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary/80 hover:bg-secondary text-foreground text-xs font-medium rounded-lg transition-colors border border-border">
                        <FileText size={13} /> Edit Order
                      </button>
                    )}
                    <button className="p-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors">
                      <MoreHorizontal size={14} />
                    </button>
                  </div>
                </div>

                {/* Status timeline */}
                <div className="flex items-center gap-0 mb-5">
                  {statusFlow.map((s, i) => {
                    const stages = statusFlow;
                    const currentIdx = stages.indexOf(selected.status);
                    const isCompleted = currentIdx > i || selected.status === s;
                    const isCurrent = selected.status === s;
                    const { color } = statusConfig[s];
                    const isLast = i === stages.length - 1;
                    return (
                      <div key={s} className="flex items-center flex-1">
                        <div className="flex flex-col items-center">
                          <div
                            className="w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all"
                            style={{
                              borderColor: isCompleted ? color : "#6b769430",
                              background: isCompleted ? color : "transparent",
                            }}
                          >
                            {isCompleted && <CheckCircle2 size={12} className="text-white" strokeWidth={3} />}
                          </div>
                          <p className={`text-[9px] mt-1 font-medium capitalize ${isCurrent ? "text-foreground" : "text-muted-foreground"}`}>{s}</p>
                        </div>
                        {!isLast && (
                          <div
                            className="flex-1 h-0.5 mx-1 mt-[-12px]"
                            style={{ background: currentIdx > i ? "#4f7eff40" : "#6b769420" }}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Key info grid */}
                <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                  {[
                    { icon: Hash,     label: "Order No.",      value: selected.number },
                    { icon: Calendar, label: "Order Date",     value: selected.orderDate },
                    { icon: Truck,    label: "Ship Date",       value: selected.shipDate },
                    { icon: Package,  label: "Delivery Date",  value: selected.deliveryDate },
                  ].map(({ icon: Icon, label, value }) => (
                    <div key={label} className="flex items-center gap-2.5 p-3 rounded-xl bg-secondary/50 border border-border">
                      <Icon size={13} className="text-muted-foreground shrink-0" />
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</p>
                        <p className="text-xs font-semibold text-foreground mt-0.5">{value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Customer + Shipping */}
            <div className="grid grid-cols-2 gap-4">
              {/* Customer */}
              <div className="bg-card rounded-2xl border border-border p-5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Customer</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <User2 size={12} className="text-muted-foreground shrink-0" />
                    <span className="text-xs font-semibold text-foreground">{selected.customer}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Building2 size={12} className="text-muted-foreground shrink-0" />
                    <span className="text-xs text-muted-foreground">{selected.company}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Hash size={12} className="text-muted-foreground shrink-0" />
                    <span className="text-xs text-muted-foreground">{selected.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Hash size={12} className="text-muted-foreground shrink-0" />
                    <span className="text-xs text-muted-foreground">{selected.phone}</span>
                  </div>
                </div>
              </div>

              {/* Shipping + Payment */}
              <div className="bg-card rounded-2xl border border-border p-5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Shipping & Payment</p>
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <MapPin size={12} className="text-muted-foreground shrink-0 mt-0.5" />
                    <span className="text-xs text-muted-foreground leading-relaxed">{selected.shipTo}</span>
                  </div>
                  <div className="flex items-center gap-2 pt-1 border-t border-border mt-2">
                    <DollarSign size={12} className="text-muted-foreground shrink-0" />
                    <span className="text-xs text-muted-foreground">{selected.paymentMethod}</span>
                    {paymentConfig[selected.paymentStatus] && (
                      <span
                        className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ color: paymentConfig[selected.paymentStatus].color, background: paymentConfig[selected.paymentStatus].bg }}
                      >
                        {selected.paymentStatus}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Line items */}
            <div className="bg-card rounded-2xl border border-border overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <p className="text-xs font-semibold text-foreground">Line Items</p>
                <span className="text-[11px] text-muted-foreground">{selected.items.length} items</span>
              </div>

              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-secondary/30 border-b border-border">
                    {["SKU", "Product", "Category", "Qty"].map(h => (
                      <th key={h} className="px-5 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {selected.items.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-5 py-8 text-center text-muted-foreground text-xs">No line items</td>
                    </tr>
                  ) : selected.items.map((item, i) => {
                    const lineTotal = item.qty * item.unitPrice * (1 - item.discount / 100);
                    return (
                      <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-[10px] text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                            {item.sku}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <p className="font-medium text-foreground">{item.product}</p>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground border border-border">
                            {item.category}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 font-mono text-muted-foreground">{item.qty}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Totals removed */}
            </div>

            {/* Notes + Tags + Assignee */}
            <div className="grid grid-cols-2 gap-4">
              {selected.notes && (
                <div className="bg-card rounded-2xl border border-border p-5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Notes</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{selected.notes}</p>
                </div>
              )}
              <div className="bg-card rounded-2xl border border-border p-5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Order Info</p>
                <div className="space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Assigned to</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-[9px] font-bold text-primary">
                        {selected.assigneeInitials}
                      </div>
                      <span className="text-foreground font-medium">{selected.assignee}</span>
                    </div>
                  </div>
                  {selected.tags && selected.tags.length > 0 && (
                    <div className="flex items-start justify-between">
                      <span className="text-muted-foreground">Tags</span>
                      <div className="flex flex-wrap gap-1 justify-end">
                        {selected.tags.map(t => (
                          <span key={t} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground border border-border">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Items</span>
                    <span className="font-mono text-foreground">{selected.items.length} line items</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-3 pt-1">
              {canEditOrder(selected) && selected.status === "draft" && (
                <button 
                  onClick={() => handleUpdateStatus('confirmed')}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl hover:bg-primary/90 transition-colors">
                  <CheckCircle2 size={13} /> Confirm Order
                </button>
              )}
              {canEditOrder(selected) && selected.status === "confirmed" && (
                <button 
                  onClick={() => handleUpdateStatus('processing')}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl hover:bg-primary/90 transition-colors">
                  <RefreshCw size={13} /> Mark Processing
                </button>
              )}
              {canEditOrder(selected) && selected.status === "processing" && (
                <button 
                  onClick={() => handleUpdateStatus('shipped')}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl hover:opacity-90 transition-colors" style={{ background: "#f59e0b", color: "#fff" }}>
                  <Truck size={13} /> Mark as Shipped
                </button>
              )}
              {canEditOrder(selected) && selected.status === "shipped" && (
                <button 
                  onClick={() => handleUpdateStatus('delivered')}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl hover:opacity-90 transition-colors" style={{ background: "#00d4aa", color: "#07090f" }}>
                  <Package size={13} /> Mark Delivered
                </button>
              )}
              <button 
                onClick={() => handleDownloadPdf(selected.id)}
                disabled={isDownloading}
                className="flex items-center gap-2 px-4 py-2 border border-border text-muted-foreground text-xs font-semibold rounded-xl hover:text-foreground hover:border-border/80 transition-colors">
                <Download size={13} /> {isDownloading ? "Exporting..." : "Export PDF"}
              </button>
              {canEditOrder(selected) && selected.status !== "cancelled" && selected.status !== "delivered" && (
                <button 
                  onClick={() => handleUpdateStatus('cancelled')}
                  className="flex items-center gap-2 px-4 py-2 border border-destructive/30 text-destructive text-xs font-semibold rounded-xl hover:bg-destructive/10 transition-colors ml-auto">
                  <XCircle size={13} /> Cancel Order
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <ShoppingCart size={40} className="text-muted-foreground/20 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">Select an order to view details</p>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-md rounded-2xl border border-border shadow-2xl flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between p-5 border-b border-border">
              <h2 className="text-lg font-semibold text-foreground">Edit Sales Order</h2>
              <button 
                onClick={() => setIsEditing(false)}
                className="p-1.5 rounded-full hover:bg-white/5 text-muted-foreground transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            <div className="p-5 overflow-y-auto flex-1 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Priority</label>
                <select 
                  value={editForm.priority || "Standard"} 
                  onChange={(e) => setEditForm({...editForm, priority: e.target.value as any})}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50"
                >
                  <option value="Standard">Standard</option>
                  <option value="Express">Express</option>
                  <option value="Urgent">Urgent</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Order Date</label>
                  <input 
                    type="date"
                    value={editForm.rawOrderDate ? new Date(editForm.rawOrderDate).toISOString().split('T')[0] : ""}
                    onChange={(e) => setEditForm({...editForm, rawOrderDate: e.target.value})}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 [color-scheme:dark]"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Ship Date</label>
                  <input 
                    type="date"
                    value={editForm.rawShipDate ? new Date(editForm.rawShipDate).toISOString().split('T')[0] : ""}
                    onChange={(e) => setEditForm({...editForm, rawShipDate: e.target.value})}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 [color-scheme:dark]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Delivery Date</label>
                  <input 
                    type="date"
                    value={editForm.rawDeliveryDate ? new Date(editForm.rawDeliveryDate).toISOString().split('T')[0] : ""}
                    onChange={(e) => setEditForm({...editForm, rawDeliveryDate: e.target.value})}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 [color-scheme:dark]"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Payment Method</label>
                  <select 
                    value={editForm.paymentMethod || ""} 
                    onChange={(e) => setEditForm({...editForm, paymentMethod: e.target.value})}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50"
                  >
                    <option value="">Select Method</option>
                    <option value="Credit Card">Credit Card</option>
                    <option value="Bank Transfer">Bank Transfer</option>
                    <option value="PayPal">PayPal</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Shipping Address</label>
                <textarea 
                  value={editForm.shipTo || ""}
                  onChange={(e) => setEditForm({...editForm, shipTo: e.target.value})}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 resize-none h-20"
                  placeholder="Enter full shipping address..."
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-muted-foreground">Order Items</label>
                  <button onClick={addItem} className="text-xs text-primary hover:text-primary/80 font-medium flex items-center gap-1">
                    <Plus size={12} /> Add Item
                  </button>
                </div>
                <div className="border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-secondary/50 text-muted-foreground">
                      <tr>
                        <th className="p-2 font-medium">Product</th>
                        <th className="p-2 font-medium w-20">Qty</th>
                        <th className="p-2 font-medium w-24">Price</th>
                        <th className="p-2 font-medium w-20">Disc (%)</th>
                        <th className="p-2 font-medium w-10"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {(editForm.items || []).map((item, idx) => (
                        <tr key={idx} className="bg-card">
                          <td className="p-2">
                            <input value={item.product} onChange={e => handleItemChange(idx, 'product', e.target.value)} className="w-full bg-transparent focus:outline-none" placeholder="Item name" />
                          </td>
                          <td className="p-2">
                            <input type="number" min="1" value={item.qty} onChange={e => handleItemChange(idx, 'qty', parseFloat(e.target.value) || 0)} className="w-full bg-transparent focus:outline-none" />
                          </td>
                          <td className="p-2">
                            <input type="number" min="0" value={item.unitPrice} onChange={e => handleItemChange(idx, 'unitPrice', parseFloat(e.target.value) || 0)} className="w-full bg-transparent focus:outline-none" />
                          </td>
                          <td className="p-2">
                            <input type="number" min="0" max="100" value={item.discount} onChange={e => handleItemChange(idx, 'discount', parseFloat(e.target.value) || 0)} className="w-full bg-transparent focus:outline-none" />
                          </td>
                          <td className="p-2 text-center">
                            <button onClick={() => removeItem(idx)} className="text-muted-foreground hover:text-destructive transition-colors">
                              <X size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                      {(editForm.items || []).length === 0 && (
                        <tr>
                          <td colSpan={5} className="p-4 text-center text-muted-foreground">No items added.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Order Notes</label>
                <textarea 
                  value={editForm.notes || ""}
                  onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 resize-none h-20"
                  placeholder="Additional instructions or notes..."
                />
              </div>
            </div>
            <div className="p-5 border-t border-border flex justify-end gap-3 bg-white/[0.02]">
              <button 
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-xl text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleSaveOrder}
                className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
