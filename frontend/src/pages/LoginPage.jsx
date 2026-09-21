import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShoppingCart, Leaf, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await login(form.username, form.password);
      } else {
        await register(form.username, form.email, form.password);
      }
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 -right-32 h-80 w-80 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-brand-700/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-500 shadow-2xl shadow-brand-500/40">
            <ShoppingCart size={28} className="text-white" strokeWidth={2} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Grocery<span className="text-brand-400">Pi</span>
          </h1>
          <p className="mt-1 text-sm text-gray-500 flex items-center gap-1.5">
            <Leaf size={12} className="text-brand-500" />
            Smart grocery tracking for your home
          </p>
        </div>

        {/* Card */}
        <div className="card">
          {/* Tabs */}
          <div className="mb-6 flex rounded-xl bg-surface-900/60 p-1">
            {["login", "register"].map((t) => (
              <button
                key={t}
                id={`tab-${t}`}
                onClick={() => { setTab(t); setError(""); }}
                className={`flex-1 rounded-lg py-2 text-sm font-semibold capitalize transition-all duration-200 ${
                  tab === t
                    ? "bg-surface-700 text-white shadow"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label htmlFor="username" className="mb-1.5 block text-xs font-medium text-gray-400">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                className="input"
                placeholder="your_username"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username"
              />
            </div>

            {/* Email (register only) */}
            {tab === "register" && (
              <div className="animate-fade-in">
                <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-gray-400">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                />
              </div>
            )}

            {/* Password */}
            <div>
              <label htmlFor="password" className="mb-1.5 block text-xs font-medium text-gray-400">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  className="input pr-11"
                  placeholder={tab === "register" ? "Min. 6 characters" : "••••••••"}
                  value={form.password}
                  onChange={handleChange}
                  required
                  minLength={tab === "register" ? 6 : 1}
                  autoComplete={tab === "register" ? "new-password" : "current-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400 animate-fade-in">
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              id="auth-submit-btn"
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2"
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : tab === "login" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-gray-600">
          GroceryPi — running on your Raspberry Pi
        </p>
      </div>
    </div>
  );
}
