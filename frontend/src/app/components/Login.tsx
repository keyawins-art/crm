import { useState } from "react";
import { useNavigate } from "react-router";
import { Zap, Eye, EyeOff, ArrowRight, AlertCircle } from "lucide-react";
import { login } from "../../lib/auth";

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      console.error("Login failed:", err);
      if (err.response) {
        setError(err.response?.data?.detail || `Server Error: ${err.response.status}`);
      } else {
        setError(err.message || "Network Error: Could not connect to backend");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-background" style={{ fontFamily: "var(--font-sans)" }}>
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col justify-between w-[480px] shrink-0 p-10 relative overflow-hidden"
        style={{ background: "linear-gradient(145deg, #0d1121 0%, #131929 50%, #1a1040 100%)" }}>
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
              <Zap size={18} className="text-white" />
            </div>
            <span className="text-lg font-semibold text-foreground tracking-tight">NexusCRM</span>
          </div>
          <h2 className="text-3xl font-semibold text-foreground leading-tight mb-4">
            Streamline your<br />
            <span style={{ color: "var(--primary)" }}>sales pipeline</span>
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
            Manage leads, close deals, and grow revenue with a CRM built for modern sales teams.
          </p>
        </div>

        {/* Decorative stats */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: "Deals Closed", value: "$2.4M", sub: "This quarter" },
            { label: "Win Rate", value: "38.9%", sub: "+2.3pp vs last" },
            { label: "Active Leads", value: "143", sub: "48 qualified" },
            { label: "Team Members", value: "12", sub: "3 departments" },
          ].map(s => (
            <div key={s.label} className="rounded border border-border/30 bg-white/[0.03] p-3">
              <p className="text-lg font-mono font-semibold text-foreground">{s.value}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{s.label}</p>
              <p className="text-[10px] text-muted-foreground/50">{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Decorative glow */}
        <div className="absolute -bottom-32 -right-32 w-64 h-64 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, var(--primary) 0%, transparent 70%)" }} />
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2.5 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="text-base font-semibold text-foreground">NexusCRM</span>
          </div>

          <h1 className="text-xl font-semibold text-foreground mb-1">Welcome back</h1>
          <p className="text-xs text-muted-foreground mb-8">Sign in to your account to continue</p>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded border border-destructive/30 bg-destructive/10 text-destructive text-xs mb-4">
              <AlertCircle size={13} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-foreground block mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                className="w-full px-3 py-2 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-3 py-2 pr-9 text-xs bg-white/5 border border-border rounded text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign in <ArrowRight size={13} />
                </>
              )}
            </button>
          </form>

          <p className="text-[11px] text-muted-foreground/50 text-center mt-8">
            Default: admin@example.com / admin
          </p>
        </div>
      </div>
    </div>
  );
}
