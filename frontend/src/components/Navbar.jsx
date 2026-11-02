import React from "react";
import { Home } from "lucide-react";

export default function Navbar({ activeTab, onSelectTab, onHome, scannerStatus = "demo", storesStatus = "not connected" }) {
  return (
    <header className="bg-gunmetal text-white select-none sticky top-0 z-40 border-b border-gray-800">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 h-[72px] flex items-center justify-between">
        {/* Brand / Logo */}
        <div 
          onClick={onHome}
          className="flex items-center gap-3 cursor-pointer group"
        >
          {/* Custom Barcode-like Icon [::] */}
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-mono font-bold text-xl tracking-tighter">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 7V5a2 2 0 0 1 2-2h2" />
              <path d="M17 3h2a2 2 0 0 1 2 2v2" />
              <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
              <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
              <line x1="8" y1="8" x2="8" y2="16" />
              <line x1="12" y1="8" x2="12" y2="16" />
              <line x1="16" y1="8" x2="16" y2="16" />
            </svg>
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-white">GroceryPi</span>
        </div>

        {/* Center Tabs: 64px high navigation container */}
        <nav className="flex items-center gap-2">
          <button
            onClick={() => onSelectTab("dashboard")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all ${
              activeTab === "dashboard"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => onSelectTab("cart")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all ${
              activeTab === "cart"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            Cart
          </button>

          <button
            onClick={() => onSelectTab("nutrition")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all ${
              activeTab === "nutrition"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            Nutrition
          </button>
        </nav>

        {/* Right Status & Home Button (Home: 88 × 72 px style) */}
        <div className="flex items-center gap-6">
          <div className="text-right text-xs leading-tight text-gray-300 hidden md:block">
            <div>Scanner · <span className="text-gray-400">{scannerStatus}</span></div>
            <div>Stores · <span className="text-gray-400">{storesStatus}</span></div>
          </div>

          <button
            onClick={onHome}
            className="w-[88px] h-[52px] rounded-xl border border-gray-600 bg-gunmetal-light/30 hover:bg-gunmetal-light text-white flex flex-col items-center justify-center gap-0.5 active:scale-95 transition-all"
            title="Reset to Dashboard"
          >
            <Home className="w-5 h-5" />
            <span className="text-[11px] font-semibold tracking-wide">Home</span>
          </button>
        </div>
      </div>
    </header>
  );
}
