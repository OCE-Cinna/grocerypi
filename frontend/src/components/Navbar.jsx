import React from "react";
import { FigmaBarcode, FigmaHome, FigmaCart, FigmaNutrition } from "./FigmaIcons";

export default function Navbar({ activeTab, onSelectTab, onHome, scannerStatus = "demo", storesStatus = "not connected" }) {
  return (
    <header className="bg-gunmetal text-white select-none sticky top-0 z-40 border-b border-gray-800">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 h-[72px] flex items-center justify-between">
        {/* Brand / Logo */}
        <div 
          onClick={onHome}
          className="flex items-center gap-3 cursor-pointer group"
        >
          {/* Custom Figma Barcode Scanner Icon */}
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white">
            <FigmaBarcode className="w-6 h-6 stroke-[#F7F4F2]" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-white">GroceryPi</span>
        </div>

        {/* Center Tabs: 64px high navigation container */}
        <nav className="flex items-center gap-2">
          <button
            onClick={() => onSelectTab("dashboard")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all flex items-center gap-2 cursor-pointer ${
              activeTab === "dashboard"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => onSelectTab("cart")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all flex items-center gap-2 cursor-pointer ${
              activeTab === "cart"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            <FigmaCart className={`w-5 h-5 ${activeTab === "cart" ? "stroke-gunmetal" : "stroke-gray-300"}`} />
            <span>Cart</span>
          </button>

          <button
            onClick={() => onSelectTab("nutrition")}
            className={`min-h-[46px] px-6 rounded-xl font-bold text-base transition-all flex items-center gap-2 cursor-pointer ${
              activeTab === "nutrition"
                ? "bg-white text-gunmetal shadow-sm"
                : "text-gray-300 hover:text-white"
            }`}
          >
            <FigmaNutrition className={`w-5 h-5 ${activeTab === "nutrition" ? "stroke-gunmetal" : "stroke-gray-300"}`} />
            <span>Nutrition</span>
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
            className="w-[88px] h-[52px] rounded-xl border border-gray-600 bg-gunmetal-light/30 hover:bg-gunmetal-light text-white flex flex-col items-center justify-center gap-0.5 active:scale-95 transition-all cursor-pointer"
            title="Reset to Dashboard"
          >
            <FigmaHome className="w-5 h-5 stroke-[#F7F4F2]" />
            <span className="text-[11px] font-semibold tracking-wide">Home</span>
          </button>
        </div>
      </div>
    </header>
  );
}
