import { useState, useEffect } from "react";
import { User, Bell, Shield, Palette, Save, CheckCircle2, Globe, Mail, Smartphone, Lock, Moon, Sun } from "lucide-react";
import { getUser } from "../../lib/auth";

export function Settings() {
  const [activeTab, setActiveTab] = useState("profile");
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [user, setUser] = useState<any>(null);

  // Form states
  const [theme, setTheme] = useState(() => localStorage.getItem("crm_theme") || "dark");
  const [language, setLanguage] = useState("English (US)");
  const [timezone, setTimezone] = useState("Pacific Time (PT)");
  const [currency, setCurrency] = useState("INR (₹)");

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
    localStorage.setItem("crm_theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  useEffect(() => {
    setUser(getUser());
  }, []);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }, 800);
  };

  const tabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "preferences", label: "Preferences", icon: Palette },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
  ];

  return (
    <div className="flex flex-col h-full bg-background" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6 border-b border-border shrink-0 bg-card">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your account settings and preferences.</p>
        </div>
        <div className="flex items-center gap-3">
          {showSuccess && (
            <span className="flex items-center gap-1.5 text-sm text-emerald-500 font-medium animate-in fade-in slide-in-from-right-4">
              <CheckCircle2 size={16} /> Saved
            </span>
          )}
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/90 transition-all disabled:opacity-70"
          >
            {isSaving ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Save size={16} />
            )}
            Save Changes
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 border-r border-border bg-card/50 p-4 shrink-0 overflow-y-auto">
          <div className="flex flex-col gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                }`}
              >
                <tab.icon size={16} className={activeTab === tab.id ? "text-primary" : "text-muted-foreground"} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 bg-background/50">
          <div className="max-w-3xl">
            {/* Profile Tab */}
            {activeTab === "profile" && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-6 pb-6 border-b border-border">
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-primary text-2xl font-bold">
                    {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-foreground">Profile Picture</h3>
                    <p className="text-sm text-muted-foreground mt-1">Upload a new avatar. Larger image will be resized automatically.</p>
                    <div className="mt-3 flex gap-3">
                      <button className="px-3 py-1.5 bg-secondary text-foreground text-xs font-medium rounded hover:bg-secondary/80 transition-colors">
                        Change
                      </button>
                      <button className="px-3 py-1.5 text-destructive text-xs font-medium hover:bg-destructive/10 rounded transition-colors">
                        Remove
                      </button>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">First Name</label>
                    <input defaultValue={user?.first_name} className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Last Name</label>
                    <input defaultValue={user?.last_name} className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
                    <input defaultValue={user?.email} className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground text-muted-foreground" readOnly />
                    <span className="text-[10px] text-muted-foreground mt-0.5">Contact IT to change your email address.</span>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Phone Number</label>
                    <input defaultValue={user?.phone || ""} placeholder="+1 (555) 000-0000" className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                  </div>
                  <div className="flex flex-col gap-1.5 col-span-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Role</label>
                    <input defaultValue={user?.role} className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-muted-foreground" readOnly />
                  </div>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === "preferences" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div>
                  <h3 className="text-lg font-medium text-foreground border-b border-border pb-2 mb-4">Appearance</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div 
                      onClick={() => handleThemeChange("dark")}
                      className={`border ${theme === 'dark' ? 'border-primary bg-primary/5' : 'border-border bg-secondary/30'} rounded-lg p-4 cursor-pointer flex flex-col items-center gap-3 hover:border-primary/50 transition-colors`}>
                      <div className="w-10 h-10 rounded-full bg-background border border-border flex items-center justify-center">
                        <Moon size={18} className="text-foreground" />
                      </div>
                      <span className="text-sm font-medium text-foreground">Dark Theme</span>
                    </div>
                    <div 
                      onClick={() => handleThemeChange("light")}
                      className={`border ${theme === 'light' ? 'border-primary bg-primary/5' : 'border-border bg-secondary/30'} rounded-lg p-4 cursor-pointer flex flex-col items-center gap-3 hover:border-primary/50 transition-colors`}>
                      <div className="w-10 h-10 rounded-full bg-background border border-border flex items-center justify-center">
                        <Sun size={18} className="text-foreground" />
                      </div>
                      <span className="text-sm font-medium text-foreground">Light Theme</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground border-b border-border pb-2 mb-4">Localization</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Language</label>
                      <select 
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground"
                      >
                        <option>English (US)</option>
                        <option>Spanish (ES)</option>
                        <option>French (FR)</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Timezone</label>
                      <select 
                        value={timezone}
                        onChange={(e) => setTimezone(e.target.value)}
                        className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground"
                      >
                        <option>Pacific Time (PT)</option>
                        <option>Eastern Time (ET)</option>
                        <option>Coordinated Universal Time (UTC)</option>
                        <option>Indian Standard Time (IST)</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Currency</label>
                      <select 
                        value={currency}
                        onChange={(e) => setCurrency(e.target.value)}
                        className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground"
                      >
                        <option>INR (₹)</option>
                        <option>USD ($)</option>
                        <option>EUR (€)</option>
                        <option>GBP (£)</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === "notifications" && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex flex-col gap-4">
                  {[
                    { icon: Mail, title: "Email Notifications", desc: "Receive daily digests and important updates via email.", active: true },
                    { icon: Smartphone, title: "Push Notifications", desc: "Receive real-time alerts in your browser.", active: false },
                    { icon: Globe, title: "Weekly Newsletter", desc: "Receive weekly product updates and CRM tips.", active: true },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
                          <item.icon size={18} className="text-muted-foreground" />
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-foreground">{item.title}</h4>
                          <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                        </div>
                      </div>
                      <div className={`w-10 h-5 rounded-full flex items-center p-1 cursor-pointer transition-colors ${item.active ? "bg-primary" : "bg-secondary"}`}>
                        <div className={`w-3.5 h-3.5 rounded-full bg-white shadow-sm transition-transform ${item.active ? "translate-x-4" : "translate-x-0"}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === "security" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div>
                  <h3 className="text-lg font-medium text-foreground border-b border-border pb-2 mb-4">Change Password</h3>
                  <div className="grid grid-cols-1 max-w-sm gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Current Password</label>
                      <input type="password" placeholder="••••••••" className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">New Password</label>
                      <input type="password" placeholder="••••••••" className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Confirm New Password</label>
                      <input type="password" placeholder="••••••••" className="px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:border-primary text-foreground" />
                    </div>
                    <button className="mt-2 px-4 py-2 bg-secondary text-foreground text-sm font-medium rounded hover:bg-secondary/80 transition-colors w-fit">
                      Update Password
                    </button>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground border-b border-border pb-2 mb-4">Two-Factor Authentication (2FA)</h3>
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                        <Lock size={18} className="text-emerald-500" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-foreground">Authenticator App</h4>
                        <p className="text-xs text-muted-foreground mt-0.5">Use an app like Google Authenticator to secure your account.</p>
                      </div>
                    </div>
                    <button className="px-3 py-1.5 bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 rounded transition-colors">
                      Enable 2FA
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
