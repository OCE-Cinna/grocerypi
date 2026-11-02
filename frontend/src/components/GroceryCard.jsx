import React from "react";
import { EcoIcon, SpaIcon } from "./MaterialIcons";
import { FigmaMinus, FigmaPlus, FigmaEdit, FigmaTrash } from "./FigmaIcons";

export default function GroceryCard({ item, activeSortNutrient, onIncrement, onDecrement, onEdit, onDelete }) {
  const product = item.product || {};
  const qty = item.quantity ?? 1;

  // Clean name: remove AH / Albert Heijn
  const cleanName = (product.name || "")
    .replace(/^(AH|Albert Heijn)\s+/i, "")
    .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
    .trim();

  // Brand rules: remove if AH/Albert Heijn, only keep if not already in product name
  const rawBrand = product.brand?.trim();
  const isAHBrand = !rawBrand || ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"].includes(rawBrand.toLowerCase());
  const brandInName = rawBrand && cleanName.toLowerCase().includes(rawBrand.toLowerCase());
  const displayBrand = !isAHBrand && !brandInName ? rawBrand : null;

  // Format date: "14 Oct 2026"
  const formatDate = (dateStr) => {
    if (!dateStr) return "Recently";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
    } catch {
      return dateStr;
    }
  };

  // Render nutrient value badge if autosorted
  const renderNutrientBadge = () => {
    if (!activeSortNutrient?.key) return null;
    const key = activeSortNutrient.key;
    const label = activeSortNutrient.label;
    const val = product[key] ?? 0;
    const unit = key.includes("kj") ? "kJ" : key.includes("kcal") ? "kcal" : "g";
    return (
      <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-limeCream text-gunmetal border border-limeCream-dark/40">
        {label}: {val} {unit}
      </span>
    );
  };

  return (
    <div className="bg-white border border-gray-300/80 rounded-2xl shadow-xs overflow-hidden flex flex-col sm:flex-row sm:items-stretch justify-between mb-4.5 transition-shadow hover:shadow-sm">
      {/* Left Details Column */}
      <div className="p-5 sm:p-6 flex-1 flex flex-col justify-center">
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Store Tag (Only store tag kept) */}
          {product.preferred_store && (
            <span className="px-2 py-0.5 rounded-md text-xs font-bold border border-gray-400 text-gray-700 bg-gray-50">
              {product.preferred_store}
            </span>
          )}

          <h3 className="text-xl sm:text-2xl font-bold text-gunmetal tracking-tight">
            {cleanName}
          </h3>

          <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-300">
            {product.category || "Food"}
          </span>

          {/* Nutri-Score Badge */}
          {product.nutriscore && (
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-black tracking-wider shadow-2xs ${
                product.nutriscore === "A"
                  ? "bg-[#038141] text-white"
                  : product.nutriscore === "B"
                  ? "bg-[#85BB2F] text-white"
                  : product.nutriscore === "C"
                  ? "bg-[#FECB02] text-gunmetal font-extrabold"
                  : product.nutriscore === "D"
                  ? "bg-[#EE8100] text-white"
                  : "bg-[#E63E11] text-white"
              }`}
              title={`Nutri-Score: Grade ${product.nutriscore}`}
            >
              Nutri-Score {product.nutriscore}
            </span>
          )}

          {/* Diet Badge (Vegan / Vegetarian) */}
          {product.is_vegan ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
              <EcoIcon className="w-3.5 h-3.5 text-emerald-700" />
              <span>Vegan</span>
            </span>
          ) : product.is_vegetarian ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-green-50 text-green-800 border border-green-300">
              <SpaIcon className="w-3.5 h-3.5 text-green-700" />
              <span>Veg</span>
            </span>
          ) : null}

          {renderNutrientBadge()}
        </div>

        <p className="text-sm text-kioskGray font-normal mt-1.5">
          Last restocked · {formatDate(item.last_restocked_at)}
          {displayBrand && <span className="ml-2 text-gray-500">· {displayBrand}</span>}
        </p>
      </div>

      {/* Right Segmented Controls (Landscape Kiosk Row - +15% scaled) */}
      <div className="flex items-stretch border-t sm:border-t-0 sm:border-l border-gray-200 shrink-0 h-[74px] sm:h-auto">
        {/* Decrement Button */}
        <button
          onClick={() => onDecrement(item)}
          className="w-[74px] sm:w-[92px] bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200 cursor-pointer"
          title="Decrease count"
        >
          <FigmaMinus className="w-6 h-6 fill-gunmetal" />
        </button>

        {/* Quantity Badge (Lime Cream) */}
        <div className="w-[92px] sm:w-[110px] bg-limeCream flex flex-col items-center justify-center text-gunmetal px-2 select-none border-r border-gray-200">
          <span className="text-2xl font-extrabold leading-tight">{qty}</span>
          <span className="text-xs font-medium leading-none text-gunmetal/90">units</span>
        </div>

        {/* Increment Button */}
        <button
          onClick={() => onIncrement(item)}
          className="w-[74px] sm:w-[92px] bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200 cursor-pointer"
          title="Increase count"
        >
          <FigmaPlus className="w-6 h-6 fill-gunmetal" />
        </button>

        {/* Edit Button */}
        <button
          onClick={() => onEdit(item)}
          className="w-[92px] sm:w-[110px] bg-white hover:bg-gray-50 flex flex-col items-center justify-center text-gunmetal transition-colors border-r border-gray-200 gap-1 active:bg-gray-100 cursor-pointer"
          title="Edit item"
        >
          <FigmaEdit className="w-5 h-5 fill-gunmetal" />
          <span className="text-xs font-semibold text-gunmetal">Edit</span>
        </button>

        {/* Delete Button (Dusty Rose with Gunmetal text/icon) */}
        <button
          onClick={() => onDelete(item)}
          className="w-[92px] sm:w-[110px] bg-dustyRose hover:bg-dustyRose-dark text-gunmetal flex flex-col items-center justify-center transition-colors gap-1 active:opacity-90 cursor-pointer"
          title="Delete item"
        >
          <FigmaTrash className="w-5 h-5 fill-gunmetal" />
          <span className="text-xs font-semibold text-gunmetal">Delete</span>
        </button>
      </div>
    </div>
  );
}
