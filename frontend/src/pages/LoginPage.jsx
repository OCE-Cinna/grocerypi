/**
 * Mobile / Remote Web Login Page for GroceryPi.
 *
 * Styled in the GroceryPi kitchen color palette (Gunmetal #383D3B, Parchment #F7F4F2,
 * Lime Cream #C3E48B, Dusty Rose #CD7A7A). Protects remote mobile browser access
 * with a bcrypt-hashed password while keeping the physical Raspberry Pi kitchen
 * kiosk hands-free on localhost.
 */

import React, { useState } from "react";
import { FigmaBarcode } from "../components/FigmaIcons";
import api from "../api/client";

export default function LoginPage({ onAuthenticated }) {
  const [tab, setTab] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const endpoint = tab === "login" ? "/auth/login" : "/auth/register";
      const payload =
        tab === "login"
          ? { username: form.username.trim(), password: form.password }
          : {
              username: form.username.trim(),
              email: form.email.trim(),
              password: form.password,
            };
      const res = await api.post(endpoint, payload);
      const { access_token, user } = res.data;
      localStorage.setItem("gp_token", access_token);
      localStorage.setItem("gp_user", JSON.stringify(user));
      if (onAuthenticated) onAuthenticated(user);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not verify credentials. Please check your username and password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-parchment text-gunmetal flex flex-col items-center justify-center px-4 py-10 select-none font-sans">
      <div className="w-full max-w-md bg-white rounded-3xl p-7 sm:p-8 shadow-xl border border-gray-300/80">
        {/* Header Brand */}
        <div className="flex items-center gap-3.5 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gunmetal text-white flex items-center justify-center shrink-0">
            <FigmaBarcode className="w-7 h-7 fill-[#F7F4F2]" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight leading-none">
              GroceryPi Mobile
            </h1>
            <p className="text-xs sm:text-sm text-kioskGray mt-1">
              Hashed-password gate for remote pantry &amp; shopping list sync
            </p>
          </div>
        </div>

        {/* Sign In / Create Account Switcher */}
        <div className="grid grid-cols-2 gap-2 p-1.5 bg-parchment rounded-2xl border border-gray-300 mb-6">
          {["login", "register"].map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => {
                setTab(mode);
                setError("");
              }}
              className={`h-11 rounded-xl font-bold text-sm capitalize transition-all cursor-pointer ${
                tab === mode
                  ? "bg-gunmetal text-white shadow-xs"
                  : "text-gunmetal hover:bg-white/60"
              }`}
            >
              {mode === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
              Username
            </label>
            <input
              name="username"
              type="text"
              required
              value={form.username}
              onChange={handleChange}
              placeholder="e.g. cinna"
              className="w-full h-[52px] px-4 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base font-semibold text-gunmetal outline-none transition-colors"
            />
          </div>

          {tab === "register" && (
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
                Email
              </label>
              <input
                name="email"
                type="email"
                required
                value={form.email}
                onChange={handleChange}
                placeholder="household@example.com"
                className="w-full h-[52px] px-4 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base font-semibold text-gunmetal outline-none transition-colors"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
              Password
            </label>
            <input
              name="password"
              type="password"
              required
              minLength={tab === "register" ? 6 : 1}
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              className="w-full h-[52px] px-4 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base font-semibold text-gunmetal outline-none transition-colors"
            />
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-dustyRose/30 border border-dustyRose-dark text-xs font-bold text-gunmetal">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full h-[60px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-lg transition-all active:scale-98 flex items-center justify-center shadow-md cursor-pointer mt-2"
          >
            {loading
              ? "Verifying..."
              : tab === "login"
              ? "Unlock GroceryPi Mobile"
              : "Register & Unlock"}
          </button>
        </form>
      </div>
    </div>
  );
}
