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
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedDiet, setSelectedDiet] = useState("All");
  const [sortByOption, setSortByOption] = useState("newest");

  // Filter items by category, search term, and dietary requirements
  const filteredItems = useMemo(() => {
    let result = items.filter((item) => {
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

    // Handle sort options
    if (sortByOption === "nutriscore") {
      const nsRank = { A: 1, B: 2, C: 3, D: 4, E: 5 };
      result.sort((a, b) => {
        const rA = nsRank[a.product?.nutriscore?.toUpperCase()] || 99;
        const rB = nsRank[b.product?.nutriscore?.toUpperCase()] || 99;
        return rA - rB;
      });
    } else if (sortByOption === "protein") {
      result.sort((a, b) => (b.product?.protein_grams || 0) - (a.product?.protein_grams || 0));
    } else if (sortByOption === "fiber") {
      result.sort((a, b) => (b.product?.fiber_grams || 0) - (a.product?.fiber_grams || 0));
    }

    return result;
  }, [items, searchQuery, selectedCategory, selectedDiet, sortByOption]);

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Top Header Row: Left (Title + Subtitle + Search) & Right (Scan New Item) */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 mb-6">
        <div className="flex-1">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gunmetal tracking-tight">
            Your kitchen, stocked.
          </h2>
          <p className="text-base text-kioskGray mt-1.5 font-normal">
            Scan items in. Use + / – for corrections only.
          </p>

          {/* Search Bar (58px high) */}
          <div className="relative mt-4">
            <FigmaSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 stroke-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search inventory"
              className="w-full h-[58px] pl-12 pr-4 bg-white rounded-2xl border border-gray-300 focus:border-gunmetal text-base text-gunmetal placeholder-gray-400 outline-none transition-all shadow-xs"
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

        {/* Primary Action Touch Button (+15% larger: 368 × 133 px on desktop) */}
        <button
          onClick={onOpenScanModal}
          className="w-full md:w-[368px] h-[104px] md:h-[133px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-2xl flex items-center justify-center gap-4 transition-all active:scale-98 shadow-md shrink-0 cursor-pointer"
        >
          <div className="w-9 h-9 rounded-xl flex items-center justify-center">
            <FigmaBarcode className="w-8 h-8 fill-[#F7F4F2]" />
          </div>
          <span>Scan New Item</span>
        </button>
      </div>

      {/* Quick-Filter Tab Bar (+15% larger: 69px high) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5 mb-6">
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`h-[69px] rounded-2xl font-bold text-lg transition-all flex items-center justify-center active:scale-98 cursor-pointer ${
                isActive
                  ? "bg-gunmetal text-white shadow-sm"
                  : "bg-white text-gunmetal border-2 border-gray-300/80 hover:bg-gray-50"
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Diet Filters & Sorting Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 mb-5 p-3.5 bg-white/70 rounded-2xl border border-gray-200">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-xs font-bold text-kioskGray uppercase tracking-wider mr-1">
            Diet:
          </span>
          {["All", "Vegetarian", "Vegan"].map((diet) => {
            const isActive = selectedDiet === diet;
            return (
              <button
                key={diet}
                onClick={() => setSelectedDiet(diet)}
                className={`h-11 px-5 rounded-xl text-sm font-bold transition-all active:scale-95 border cursor-pointer ${
                  isActive
                    ? "bg-gunmetal text-white border-gunmetal shadow-xs"
                    : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
                }`}
              >
                {diet === "All" ? "All Diets" : diet}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2.5">
          <span className="text-xs font-bold text-kioskGray uppercase tracking-wider">
            Sort by:
          </span>
          <select
            value={sortByOption}
            onChange={(e) => setSortByOption(e.target.value)}
            className="h-11 px-3.5 bg-white border border-gray-300 rounded-xl text-sm font-bold text-gunmetal outline-none focus:border-gunmetal cursor-pointer"
          >
            <option value="newest">Newest restocked</option>
            <option value="nutriscore">Nutri-Score (Best A to E)</option>
            <option value="protein">Protein (Highest)</option>
            <option value="fiber">Fiber (Highest)</option>
          </select>
        </div>
      </div>

      {/* Active Nutrition Autosort Indicator */}
      {activeSortNutrient && (
        <div className="mb-5 p-3.5 bg-limeCream/25 border border-limeCream-dark/30 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-limeCream-dark" />
            <span className="text-sm font-bold text-gunmetal">
              Autosorted by: <span className="underline">{activeSortNutrient.label}</span> (Highest first)
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

      {/* Item List / Grocery Cards */}
      <div className="space-y-3.5">
        {filteredItems.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-300/80">
            <p className="text-xl font-bold text-gunmetal">No inventory items found</p>
            <p className="text-sm text-kioskGray mt-1">
              {searchQuery ? "Try searching for a different term." : "Use 'Scan New Item' to register products."}
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
      <div className="flex items-center justify-between text-xs text-kioskGray mt-6 pt-3 border-t border-gray-300">
        <span>{filteredItems.length} items · illustrative household · 14 Oct 2026</span>
        {filteredItems.length > 2 && (
          <span className="font-medium text-gray-500 inline-flex items-center gap-1.5">
            <span>Scroll for {Math.max(1, filteredItems.length - 2)} more items</span>
            <FigmaChevronDown className="w-3.5 h-3.5 fill-current" />
          </span>
        )}
      </div>
    </div>
  );
}
