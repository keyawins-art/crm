import { useState, useEffect } from "react";
import { Users, UserCog, Shield, Trash2, Edit2, CheckCircle2, XCircle, Plus, X, Building, Save } from "lucide-react";
import { usersAPI, rolesAPI, companySettingsAPI } from "../../lib/api";

export function Admin() {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<any>({});

  const [companySettings, setCompanySettings] = useState<any>({
    company_name: "",
    address: "",
    gst_number: "",
    phone: "",
    bank_name: "",
    bank_branch: "",
    bank_account_no: "",
    bank_ifsc: "",
  });
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addFormData, setAddFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    role_id: ""
  });

  useEffect(() => {
    fetchData();
    fetchCompanySettings();
  }, []);

  const fetchCompanySettings = async () => {
    try {
      const res = await companySettingsAPI.get();
      setCompanySettings(res.data);
    } catch (err) {
      console.error("Failed to load company settings:", err);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [usersRes, rolesRes] = await Promise.all([
        usersAPI.list(),
        rolesAPI.list()
      ]);
      setUsers(usersRes.data || []);
      setRoles(rolesRes.data || []);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user: any) => {
    setEditingUserId(user.id);
    setEditFormData({ role_id: user.role_id, status: user.status });
  };

  const handleSave = async (id: string) => {
    try {
      await usersAPI.update(id, editFormData);
      setEditingUserId(null);
      fetchData();
    } catch (err) {
      console.error("Failed to update user:", err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await usersAPI.delete(id);
      fetchData();
    } catch (err) {
      console.error("Failed to delete user:", err);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const dataToSend = { ...addFormData };
      if (!dataToSend.role_id) {
        delete (dataToSend as any).role_id;
      }
      await usersAPI.create(dataToSend);
      setIsAddModalOpen(false);
      setAddFormData({ email: "", first_name: "", last_name: "", password: "", role_id: "" });
      fetchData();
    } catch (err) {
      console.error("Failed to create user:", err);
      alert("Failed to create user. Please try again.");
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSavingSettings(true);
      const res = await companySettingsAPI.update(companySettings);
      setCompanySettings(res.data);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save company settings:", err);
      alert("Failed to save settings.");
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setIsSavingSettings(true);
      const res = await companySettingsAPI.uploadLogo(file);
      setCompanySettings(res.data);
      alert("Logo uploaded successfully!");
    } catch (err) {
      console.error("Logo upload failed:", err);
      alert("Failed to upload logo.");
    } finally {
      setIsSavingSettings(false);
    }
  };

  const getLogoUrl = (url: string) => {
    if (!url) return "";
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    return `http://${host}:8000/${url}`;
  };

  return (
    <div className="flex flex-col h-full bg-background" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0 bg-card">
        <Shield size={16} className="text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Admin Control Panel</h2>
        
        {/* Tab Switchers */}
        <div className="flex gap-1 ml-6 border border-border rounded p-0.5 bg-secondary/30">
          <button onClick={() => setActiveTab("users")} className={`px-3 py-1 rounded text-xs font-medium transition-colors ${activeTab === "users" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"}`}>Employees</button>
          <button onClick={() => setActiveTab("company")} className={`px-3 py-1 rounded text-xs font-medium transition-colors ${activeTab === "company" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"}`}>Company Profile</button>
        </div>

        <div className="ml-auto">
          {activeTab === "users" && (
            <button onClick={() => setIsAddModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors">
              <Plus size={14} /> Add Employee
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {activeTab === "users" ? (
          <div className="rounded border border-border bg-card animate-in fade-in duration-200">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="text-xs font-semibold text-foreground">User Management</h3>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center py-24">
                <span className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
              </div>
            ) : (
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-secondary/30">
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">User</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Email</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Role</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id} className="border-b border-border last:border-0 hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center text-[10px] font-semibold text-primary">
                            {user.first_name[0]}{user.last_name[0]}
                          </div>
                          <span className="font-medium text-foreground">{user.first_name} {user.last_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground font-mono">{user.email}</td>
                      <td className="px-4 py-3">
                        {editingUserId === user.id ? (
                          <select
                            className="bg-secondary/50 border border-border rounded text-xs px-2 py-1 focus:outline-none focus:border-primary"
                            value={editFormData.role_id || ""}
                            onChange={e => setEditFormData({ ...editFormData, role_id: e.target.value })}
                          >
                            <option value="">No Role</option>
                            {roles.map(r => (
                              <option key={r.id} value={r.id}>{r.name}</option>
                            ))}
                          </select>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary">
                            {roles.find(r => r.id === user.role_id)?.name || "No Role"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editingUserId === user.id ? (
                          <select
                            className="bg-secondary/50 border border-border rounded text-xs px-2 py-1 focus:outline-none focus:border-primary"
                            value={editFormData.status || ""}
                            onChange={e => setEditFormData({ ...editFormData, status: e.target.value })}
                          >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                        ) : (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium capitalize ${
                            user.status === 'active' ? "bg-emerald-500/10 text-emerald-500" : "bg-rose-500/10 text-rose-500"
                          }`}>
                            {user.status || "Unknown"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {editingUserId === user.id ? (
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => handleSave(user.id)} className="text-emerald-500 hover:text-emerald-400 transition-colors">
                              <CheckCircle2 size={14} />
                            </button>
                            <button onClick={() => setEditingUserId(null)} className="text-muted-foreground hover:text-foreground transition-colors">
                              <XCircle size={14} />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => handleEdit(user)} className="text-muted-foreground hover:text-primary transition-colors">
                              <Edit2 size={14} />
                            </button>
                            <button onClick={() => handleDelete(user.id)} className="text-muted-foreground hover:text-rose-500 transition-colors">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className="rounded border border-border bg-card p-6 max-w-2xl animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-border pb-3 mb-5">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Company Settings</h3>
                <p className="text-xs text-muted-foreground">Manage details displayed on quotation headers and performa invoices.</p>
              </div>
              {showSuccess && (
                <span className="flex items-center gap-1 text-xs text-emerald-500 font-semibold animate-bounce">
                  <CheckCircle2 size={13} /> Settings Saved
                </span>
              )}
            </div>

            <form onSubmit={handleSaveSettings} className="flex flex-col gap-4">
              {/* Logo Section */}
              <div className="flex items-center gap-6 pb-4 border-b border-border">
                {companySettings.logo_url ? (
                  <img src={getLogoUrl(companySettings.logo_url)} alt="Company Logo" className="w-16 h-16 object-contain rounded border border-border bg-white" />
                ) : (
                  <div className="w-16 h-16 rounded border border-dashed border-border flex items-center justify-center text-muted-foreground text-[10px]">No Logo</div>
                )}
                <div>
                  <h4 className="text-xs font-semibold text-foreground">Company Logo</h4>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Upload a square or wide brand logo image (PNG, JPG).</p>
                  <label className="mt-2 inline-block px-2.5 py-1 bg-secondary text-foreground rounded text-[10px] font-medium hover:bg-secondary/80 cursor-pointer transition-colors border border-border">
                    Choose Logo
                    <input type="file" onChange={handleLogoUpload} className="hidden" accept="image/*" />
                  </label>
                </div>
              </div>

              <div className="flex flex-col gap-1.5 col-span-2">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Company Name</label>
                <input required value={companySettings.company_name} onChange={e => setCompanySettings({...companySettings, company_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">GSTIN / Tax No</label>
                  <input value={companySettings.gst_number || ""} onChange={e => setCompanySettings({...companySettings, gst_number: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Phone Number</label>
                  <input value={companySettings.phone || ""} onChange={e => setCompanySettings({...companySettings, phone: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Address</label>
                <textarea rows={3} value={companySettings.address || ""} onChange={e => setCompanySettings({...companySettings, address: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground leading-normal" />
              </div>

              <div className="border-t border-border pt-4 mt-2">
                <h4 className="text-xs font-semibold text-foreground mb-3">Bank Details (Performa Invoice Footer)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Bank Name</label>
                    <input value={companySettings.bank_name || ""} onChange={e => setCompanySettings({...companySettings, bank_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Branch</label>
                    <input value={companySettings.bank_branch || ""} onChange={e => setCompanySettings({...companySettings, bank_branch: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Account Number</label>
                    <input value={companySettings.bank_account_no || ""} onChange={e => setCompanySettings({...companySettings, bank_account_no: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">IFSC Code</label>
                    <input value={companySettings.bank_ifsc || ""} onChange={e => setCompanySettings({...companySettings, bank_ifsc: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground font-mono" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-border">
                <button type="submit" disabled={isSavingSettings} className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90 transition-colors disabled:opacity-75">
                  <Save size={13} /> {isSavingSettings ? "Saving..." : "Save Company Settings"}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-card border border-border rounded-lg shadow-lg flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-sm font-semibold text-foreground">Add New Employee</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleAddUser} className="p-5 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">First Name</label>
                  <input required value={addFormData.first_name} onChange={e => setAddFormData({...addFormData, first_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Last Name</label>
                  <input required value={addFormData.last_name} onChange={e => setAddFormData({...addFormData, last_name: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
                <input required type="email" value={addFormData.email} onChange={e => setAddFormData({...addFormData, email: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Temporary Password</label>
                <input required type="password" value={addFormData.password} onChange={e => setAddFormData({...addFormData, password: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground" />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Role</label>
                <select value={addFormData.role_id} onChange={e => setAddFormData({...addFormData, role_id: e.target.value})} className="px-3 py-2 bg-secondary/50 border border-border rounded text-xs focus:outline-none focus:border-primary text-foreground">
                  <option value="">Select a Role (Optional)</option>
                  {roles.map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-3 mt-2">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-primary text-white rounded text-xs font-medium hover:bg-primary/90">Create Employee</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
