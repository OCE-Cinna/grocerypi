import { ShoppingCart, LogOut, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-30 border-b border-surface-700/60 bg-surface-900/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 font-bold text-lg tracking-tight hover:opacity-80 transition-opacity"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-white shadow-lg shadow-brand-500/30">
            <ShoppingCart size={16} strokeWidth={2.5} />
          </span>
          <span className="text-white">
            Grocery<span className="text-brand-400">Pi</span>
          </span>
        </Link>

        {/* Right side */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl bg-surface-800 px-3 py-1.5 text-sm">
              <User size={14} className="text-brand-400" />
              <span className="text-gray-300 font-medium">{user.username}</span>
            </div>
            <button
              id="navbar-logout-btn"
              onClick={handleLogout}
              className="btn-icon btn-ghost text-gray-400 hover:text-red-400"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
