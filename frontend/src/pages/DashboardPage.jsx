/**
 * Main Inventory Dashboard Page for GroceryPi.
 *
 * Built around a shared 5-column vertical grid so elements across every row
 * line up cleanly with each other:
 * - Row 1 (Hero): Title + Search bar span Columns 1–3; 'Scan New Item' button spans Columns 4–5.
 * - Row 2 (Categories): 5 equal buttons (All, Food, Pets, Household, Hygiene) in Columns 1–5.
 * - Row 3 (Diet & Sort): 'DIET: All Diets' in Column 1, 'Vegetarian' in Column 2,
 *   'Vegan' in Column 3, and 'SORT BY: [Dropdown]' across Columns 4–5.
 * - Row 4 (Inventory Cards): Left item details span Columns 1–3; right action
 *   buttons (-, units, +, Edit, Delete) align under Columns 4–5.
 */

import React, { useState, useMemo } from "react";
import GroceryCard from "../components/GroceryCard";
import {
  FigmaSearch,
  FigmaBarcode,
  FigmaChevronDown,
  FigmaClose,
} from "../components/FigmaIcons";

const CATEGORIES = ["All", "Food", "Pets", "Household", "Hygiene"];

export default function DashboardPage({
  items,
  activeSortNutrient,
  onClearNutrientSort,
  onIncrement,
  onDecrement,
  onEdit,
  onDelete,
  onOpenScanModal,
  canScan = true,
  scannerStatus = "Pi Camera v3",
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedDiet, setSelectedDiet] = useState("All");
  const [sortByOption, setSortByOption] = useState("newest");
  const [showDepleted, setShowDepleted] = useState(false);
  const [dismissedCycleBanner, setDismissedCycleBanner] = useState(false);

  /**
   * Counts how many items have reached 100% of their restock cycle (Depleted / In Cart)
   * and how many stocked items are at 75% or more of their cycle (running low).
   */
  const { depletedCount, runningLowCount } = useMemo(() => {
    let depleted = 0;
    let low = 0;
    const nowMs = Date.now();

    for (const item of items) {
      const isDep = item.status === "DEPLETED" || (item.quantity ?? 1) <= 0;
      if (isDep) {
        depleted += 1;
      } else if (item.last_restocked_at) {
        const elapsedDays = Math.max(
          0,
          (nowMs - new Date(item.last_restocked_at).getTime()) / 86400000
        );
        const effInterval =
          item.manual_interval_override ?? item.restock_interval_days ?? 7;
        if (effInterval > 0 && elapsedDays / effInterval >= 0.75) {
          low += 1;
        }
      }
    }
    return { depletedCount: depleted, runningLowCount: low };
  }, [items]);

  /**
   * Filters the displayed items based on active stock status (hiding depleted/synced
   * 0-unit items unless toggled on), search box, selected category tab, selected
   * diet button, and chosen sort order.
   */
  const filteredItems = useMemo(() => {
    let result = items.filter((item) => {
      const isDepleted =
        item.status === "DEPLETED" || (item.quantity ?? 1) <= 0;
      if (!showDepleted && isDepleted) {
        return false;
      }

      const p = item.product || {};
      const matchesSearch =
        searchQuery.trim() === "" ||
        p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.brand?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.barcode?.includes(searchQuery);

      const itemCat = (p.category || "").toLowerCase();
      const selCat = selectedCategory.toLowerCase();
      const matchesCategory =
        selectedCategory === "All" ||
        itemCat === selCat ||
        (selCat === "pets" && itemCat === "pet") ||
        (selCat === "pet" && itemCat === "pets");

      const matchesDiet =
        selectedDiet === "All" ||
        (selectedDiet === "Vegetarian" && (p.is_vegetarian || p.is_vegan)) ||
        (selectedDiet === "Vegan" && p.is_vegan);

      return matchesSearch && matchesCategory && matchesDiet;
    });

    if (sortByOption === "nutriscore") {
      const nsRank = { A: 1, B: 2, C: 3, D: 4, E: 5 };
      result.sort((a, b) => {
        const rA = nsRank[a.product?.nutriscore?.toUpperCase()] || 99;
        const rB = nsRank[b.product?.nutriscore?.toUpperCase()] || 99;
        return rA - rB;
      });
    } else if (sortByOption === "protein") {
      result.sort(
        (a, b) => (b.product?.protein_grams || 0) - (a.product?.protein_grams || 0)
      );
    } else if (sortByOption === "fiber") {
      result.sort(
        (a, b) => (b.product?.fiber_grams || 0) - (a.product?.fiber_grams || 0)
      );
    }

    return result;
  }, [items, searchQuery, selectedCategory, selectedDiet, sortByOption, showDepleted]);

  return (
    <div className="max-w-[1180px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Row 1: 5-Column Hero Grid (Cols 1-3: Title + Search | Cols 4-5: Scan New Item) */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 items-stretch mb-5">
        <div className="md:col-span-3 flex flex-col justify-between">
          <div>
            <h2 className="text-3xl sm:text-[40px] font-extrabold text-gunmetal tracking-tight leading-tight">
              Scan items in inventory.
            </h2>
            <p className="text-base text-kioskGray mt-1 font-normal">
              Scan items in. Use + / – for corrections only.
            </p>
          </div>

          {/* Search Bar (Spans exact width of Columns 1–3) */}
          <div className="relative mt-3.5">
            <FigmaSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 stroke-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search inventory"
              className="w-full h-[56px] pl-12 pr-10 bg-white rounded-2xl border border-gray-300 focus:border-gunmetal text-base text-gunmetal placeholder-gray-400 outline-none transition-all shadow-xs"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gunmetal p-1 cursor-pointer"
              >
                <FigmaClose className="w-5 h-5 fill-current" />
              </button>
            )}
          </div>
        </div>

        {/* Primary Action Touch Button (Spans exact width of Columns 4–5; locked when no Pi camera is detected) */}
        <button
          type="button"
          onClick={() => {
            if (canScan) onOpenScanModal();
          }}
          disabled={!canScan}
          title={
            canScan
              ? "Open live barcode scanner"
              : "Barcode scanning is only enabled on the Raspberry Pi camera kiosk"
          }
          className={`md:col-span-2 w-full min-h-[104px] md:min-h-[136px] rounded-2xl font-bold flex flex-col items-center justify-center gap-1.5 transition-all shadow-md ${canScan
              ? "bg-gunmetal hover:bg-gunmetal-dark text-white active:scale-98 cursor-pointer"
              : "bg-gray-300 text-gray-600 cursor-not-allowed opacity-85"
            }`}
        >
          <div className="flex items-center gap-3.5 text-2xl">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center">
              <FigmaBarcode
                className={`w-8 h-8 ${canScan ? "fill-[#F7F4F2]" : "fill-gray-600"
                  }`}
              />
            </div>
            <span>Scan New Item</span>
          </div>
          {!canScan && (
            <span className="text-xs font-semibold text-gray-600">
              Scanner · {scannerStatus} (Kiosk Camera Required)
            </span>
          )}
        </button>
      </div>

      {/* Row 2: 5-Column Category Filter Bar (Cols 1-5) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5 mb-5">
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`h-[64px] rounded-2xl font-bold text-lg transition-all flex items-center justify-center active:scale-98 cursor-pointer ${isActive
                  ? "bg-gunmetal text-white shadow-sm"
                  : "bg-white text-gunmetal border-2 border-gray-300/80 hover:bg-gray-50"
                }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Row 3: 5-Column Diet Filters & Sort Toolbar */}
      <div className="p-3 bg-white/70 rounded-2xl border border-gray-200 mb-5">
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3.5 items-center">
          {/* Column 1: DIET label + All Diets button */}
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold text-kioskGray uppercase tracking-wider shrink-0 pl-1">
              DIET:
            </span>
            <button
              onClick={() => setSelectedDiet("All")}
              className={`flex-1 h-11 px-3 rounded-xl text-sm font-bold leading-none inline-flex items-center justify-center transition-all active:scale-95 border cursor-pointer ${selectedDiet === "All"
                  ? "bg-gunmetal text-white border-gunmetal shadow-xs"
                  : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
                }`}
            >
              All Diets
            </button>
          </div>

          {/* Column 2: Vegetarian button (Directly under 'Food') */}
          <button
            onClick={() => setSelectedDiet("Vegetarian")}
            className={`w-full h-11 px-4 rounded-xl text-sm font-bold leading-none inline-flex items-center justify-center transition-all active:scale-95 border cursor-pointer ${selectedDiet === "Vegetarian"
                ? "bg-gunmetal text-white border-gunmetal shadow-xs"
                : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
              }`}
          >
            Vegetarian
          </button>

          {/* Column 3: Vegan button (Directly under 'Pets') */}
          <button
            onClick={() => setSelectedDiet("Vegan")}
            className={`w-full h-11 px-4 rounded-xl text-sm font-bold leading-none inline-flex items-center justify-center transition-all active:scale-95 border cursor-pointer ${selectedDiet === "Vegan"
                ? "bg-gunmetal text-white border-gunmetal shadow-xs"
                : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
              }`}
          >
            Vegan
          </button>

          {/* Columns 4–5: SORT BY label + Select dropdown (Directly under 'Household' + 'Hygiene') */}
          <div className="sm:col-span-2 flex items-center justify-end gap-3">
            <span className="text-xs font-bold text-kioskGray uppercase tracking-wider shrink-0">
              SORT BY:
            </span>
            <select
              value={sortByOption}
              onChange={(e) => setSortByOption(e.target.value)}
              className="w-full sm:w-[220px] h-11 px-3.5 bg-white border border-gray-300 rounded-xl text-sm font-bold text-gunmetal outline-none focus:border-gunmetal cursor-pointer"
            >
              <option value="newest">Newest restocked</option>
              <option value="nutriscore">Nutri-Score (Best A to E)</option>
              <option value="protein">Protein (Highest)</option>
              <option value="fiber">Fiber (Highest)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Non-Blocking Restock Cycle Banner (75% Running Low & 100% Auto-Depleted) */}
      {!dismissedCycleBanner && (depletedCount > 0 || runningLowCount > 0) && (
        <div className="mb-5 p-3.5 bg-white border border-gray-300 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-2.5 text-sm text-gunmetal">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
            <span>
              <strong className="font-bold">Restock cycle update:</strong>{" "}
              {depletedCount > 0 && (
                <span>
                  {depletedCount} item{depletedCount === 1 ? "" : "s"} reached
                  100% &amp; moved to Cart
                </span>
              )}
              {depletedCount > 0 && runningLowCount > 0 && <span> · </span>}
              {runningLowCount > 0 && (
                <span>
                  {runningLowCount} item{runningLowCount === 1 ? "" : "s"} at
                  ≥75% cycle (running low)
                </span>
              )}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {depletedCount > 0 && (
              <button
                type="button"
                onClick={() => setShowDepleted((prev) => !prev)}
                className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gunmetal text-white hover:bg-gunmetal-dark transition-colors cursor-pointer"
              >
                {showDepleted
                  ? `Hide Depleted (${depletedCount})`
                  : `Review Depleted (${depletedCount})`}
              </button>
            )}
            <button
              type="button"
              onClick={() => setDismissedCycleBanner(true)}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gunmetal border border-gray-300 transition-colors cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Active Nutrition Autosort Banner */}
      {activeSortNutrient && (
        <div className="mb-5 p-3.5 bg-limeCream/25 border border-limeCream-dark/30 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-limeCream-dark" />
            <span className="text-sm font-bold text-gunmetal">
              Autosorted by:{" "}
              <span className="underline">{activeSortNutrient.label}</span>{" "}
              (Highest first)
            </span>
          </div>
          <button
            onClick={onClearNutrientSort}
            className="px-3.5 py-1.5 bg-white hover:bg-gray-100 rounded-xl text-xs font-bold text-gunmetal border border-gray-300 flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <span>Reset Sort</span>
            <FigmaClose className="w-4 h-4 fill-current" />
          </button>
        </div>
      )}

      {/* Row 4: Item List / Grocery Cards */}
      <div className="space-y-3.5">
        {filteredItems.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-300/80">
            <p className="text-xl font-bold text-gunmetal">
              No inventory items found
            </p>
            <p className="text-sm text-kioskGray mt-1">
              {searchQuery
                ? "Try searching for a different term."
                : "Use 'Scan New Item' to register products."}
            </p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <GroceryCard
              key={item.id}
              item={item}
              activeSortNutrient={activeSortNutrient}
              onIncrement={onIncrement}
              onDecrement={onDecrement}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))
        )}
      </div>

      {/* Footer Info Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-kioskGray mt-6 pt-3 border-t border-gray-300">
        <div className="flex items-center gap-3">
          <span>{filteredItems.length} stocked items shown</span>
          {depletedCount > 0 && (
            <button
              type="button"
              onClick={() => setShowDepleted((prev) => !prev)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${showDepleted
                  ? "bg-gunmetal text-white border-gunmetal"
                  : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
                }`}
            >
              {showDepleted
                ? `Hide Depleted / Synced (${depletedCount})`
                : `Show Depleted / Synced (${depletedCount})`}
            </button>
          )}
        </div>
        {filteredItems.length > 2 && (
          <span className="font-medium text-gray-500 inline-flex items-center gap-1.5">
            <span>
              Scroll for {Math.max(1, filteredItems.length - 2)} more items
            </span>
            <FigmaChevronDown className="w-3.5 h-3.5 fill-current" />
          </span>
        )}
      </div>
    </div>
  );
}
