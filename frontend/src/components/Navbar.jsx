/**
 * Top Navigation Bar component for GroceryPi.
 *
 * Uses the same 5-column grid as the Dashboard screen so every navbar item
 * lines up vertically with the columns below it:
 * - Column 1: GroceryPi logo and title (clicking exits kiosk mode).
 * - Column 2: Dashboard tab button.
 * - Column 3: Cart tab button.
 * - Column 4: Nutrition tab button.
 * - Column 5: Live Scanner and Stores status indicators aligned to the right edge.
 */

import React from "react";
import { FigmaBarcode, FigmaCart, FigmaNutrition } from "./FigmaIcons";

export default function Navbar({
  activeTab,
  onSelectTab,
  onHome,
  scannerStatus = "Not detected",
  scannerState = "not_detected",
  storesStatus = "Not connected",
  storesConnected = false,
}) {
  const scannerDotColor =
    scannerState === "online"
      ? "bg-emerald-400"
      : scannerState === "lagging"
      ? "bg-amber-400"
      : "bg-rose-400";

  const storesDotColor = storesConnected ? "bg-emerald-400" : "bg-rose-400";

  return (
    <header className="bg-gunmetal text-white select-none sticky top-0 z-40 border-b border-gray-800">
      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 h-[80px] grid grid-cols-2 md:grid-cols-5 gap-3.5 items-center">
        {/* Column 1: Brand Logo & Title (Aligns over 'All' category column) */}
        <div
          onClick={onHome}
          className="flex items-center gap-3 cursor-pointer group"
          title="Exit Kiosk Mode"
        >
          <div className="w-10 h-10 rounded-xl bg-white/10 group-hover:bg-white/20 transition-colors flex items-center justify-center text-white shrink-0">
            <FigmaBarcode className="w-6 h-6 fill-[#F7F4F2]" />
          </div>
          <span className="font-extrabold text-2xl leading-none tracking-tight text-white">
            GroceryPi
          </span>
        </div>

        {/* Column 2: Dashboard Tab (Aligns over 'Food' column) */}
        <button
          onClick={() => onSelectTab("dashboard")}
          className={`w-full h-[54px] px-4 rounded-2xl font-bold text-base leading-none transition-all flex items-center justify-center gap-2.5 cursor-pointer active:scale-95 ${
            activeTab === "dashboard"
              ? "bg-white text-gunmetal shadow-sm"
              : "text-gray-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <span>Dashboard</span>
        </button>

        {/* Column 3: Cart Tab (Aligns over 'Pets' column) */}
        <button
          onClick={() => onSelectTab("cart")}
          className={`w-full h-[54px] px-4 rounded-2xl font-bold text-base leading-none transition-all flex items-center justify-center gap-2.5 cursor-pointer active:scale-95 ${
            activeTab === "cart"
              ? "bg-white text-gunmetal shadow-sm"
              : "text-gray-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <FigmaCart
            className={`w-5 h-5 shrink-0 ${
              activeTab === "cart" ? "fill-gunmetal" : "fill-gray-300"
            }`}
          />
          <span>Cart</span>
        </button>

        {/* Column 4: Nutrition Tab (Aligns over 'Household' column) */}
        <button
          onClick={() => onSelectTab("nutrition")}
          className={`w-full h-[54px] px-4 rounded-2xl font-bold text-base leading-none transition-all flex items-center justify-center gap-2.5 cursor-pointer active:scale-95 ${
            activeTab === "nutrition"
              ? "bg-white text-gunmetal shadow-sm"
              : "text-gray-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <FigmaNutrition
            className={`w-5 h-5 shrink-0 ${
              activeTab === "nutrition" ? "stroke-gunmetal" : "stroke-gray-300"
            }`}
          />
          <span>Nutrition</span>
        </button>

        {/* Column 5: Scanner & Store Status with Live Status Dots (Aligns over 'Hygiene' column) */}
        <div className="hidden md:flex flex-col items-end justify-center text-right text-xs leading-snug text-gray-300 gap-1">
          <div className="inline-flex items-center gap-1.5">
            <span>Scanner ·</span>
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${scannerDotColor}`}
              aria-hidden="true"
            />
            <span className="text-gray-200 font-semibold">{scannerStatus}</span>
          </div>
          <div className="inline-flex items-center gap-1.5">
            <span>Stores ·</span>
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${storesDotColor}`}
              aria-hidden="true"
            />
            <span className="text-gray-200 font-semibold">{storesStatus}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
