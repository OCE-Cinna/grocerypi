/**
 * Grocery Card component for GroceryPi.
 *
 * Uses a 5-column split (3 columns for product info on the left, 2 columns for
 * the 5 touch action buttons on the right):
 * - Left column top row: Store badge is left-aligned, Product Name sits next to it,
 *   and the Category badge (plus Nutri-Score and Diet badges) is right-aligned so
 *   categories form a clean vertical column down the list.
 * - Right column: 5 equal-width segmented buttons (-, units, +, Edit, Delete)
 *   aligned directly under the 'Scan New Item' button.
 */

import React from "react";
import { FigmaMinus, FigmaPlus, FigmaEdit, FigmaTrash } from "./FigmaIcons";

export default function GroceryCard({
  item,
  activeSortNutrient,
  onIncrement,
  onDecrement,
  onEdit,
  onDelete,
}) {
  const product = item.product || {};
  const qty = item.quantity ?? 1;

  // Remove repeated store names from the product title so the card stays clean
  const cleanName = (product.name || "")
    .replace(/^(AH|Albert Heijn)\s+/i, "")
    .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
    .trim();

  // Only show the brand name if it is not Albert Heijn and not already in the title
  const rawBrand = product.brand?.trim();
  const isAHBrand =
    !rawBrand ||
    ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"].includes(
      rawBrand.toLowerCase()
    );
  const brandInName =
    rawBrand && cleanName.toLowerCase().includes(rawBrand.toLowerCase());
  const displayBrand = !isAHBrand && !brandInName ? rawBrand : null;

  /**
   * Formats a database timestamp into a readable date like "14 Oct 2026".
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return "Recently";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  /**
   * Shows a highlighted green badge with the item's nutrient amount when the
   * user taps a nutrition bar on the Nutrition screen.
   */
  const renderNutrientBadge = () => {
    if (!activeSortNutrient?.key) return null;
    const key = activeSortNutrient.key;
    const label = activeSortNutrient.label;
    const val = product[key] ?? 0;
    const unit = key.includes("kj") ? "kJ" : key.includes("kcal") ? "kcal" : "g";
    return (
      <span className="h-6 px-2.5 rounded-full text-xs font-bold leading-none inline-flex items-center bg-limeCream text-gunmetal border border-limeCream-dark/40 shrink-0">
        {label}: {val} {unit}
      </span>
    );
  };

  const effectiveInterval =
    item.manual_interval_override ?? item.restock_interval_days;

  return (
    <div className="bg-white border border-gray-300/80 rounded-2xl shadow-xs overflow-hidden grid grid-cols-1 md:grid-cols-5 items-stretch transition-shadow hover:shadow-sm">
      {/* Left Details Column (Spans Columns 1–3) */}
      <div className="md:col-span-3 p-5 sm:p-6 flex flex-col justify-center">
        <div className="flex items-center justify-between gap-3">
          {/* Left-Aligned Group: Store Tag + Product Name */}
          <div className="flex items-center gap-3 min-w-0">
            {product.preferred_store && (
              <span className="h-6 min-w-[42px] px-2 rounded-md text-xs font-bold leading-none inline-flex items-center justify-center border border-gray-400 text-gray-700 bg-gray-50 shrink-0">
                {product.preferred_store}
              </span>
            )}

            <h3 className="text-xl sm:text-2xl font-bold text-gunmetal tracking-tight leading-snug truncate">
              {cleanName}
            </h3>

            {renderNutrientBadge()}
          </div>

          {/* Right-Aligned Group: Diet, Nutri-Score, and Category Badge */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Diet Badge: Vegan or Vegetarian */}
            {product.is_vegan ? (
              <span className="h-6 px-2.5 rounded-md text-xs font-bold leading-none inline-flex items-center bg-emerald-50 text-emerald-800 border border-emerald-300">
                Vegan
              </span>
            ) : product.is_vegetarian ? (
              <span className="h-6 px-2.5 rounded-md text-xs font-bold leading-none inline-flex items-center bg-green-50 text-green-800 border border-green-300">
                Vegetarian
              </span>
            ) : null}

            {/* Nutri-Score Badge */}
            {product.nutriscore && (
              <span
                className={`h-6 px-2 rounded-md text-[11px] font-black leading-none inline-flex items-center tracking-wider shadow-2xs ${
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

            {/* Category Badge (Pinned flush right) */}
            <span className="h-6 min-w-[84px] px-2.5 rounded-md text-xs font-semibold leading-none inline-flex items-center justify-center bg-gray-100 text-gray-700 border border-gray-300">
              {product.category || "Food"}
            </span>
          </div>
        </div>

        <p className="text-sm text-kioskGray font-normal mt-1.5 leading-snug">
          Last restocked · {formatDate(item.last_restocked_at)}
          {product.package_size && (
            <span className="ml-2 text-gray-500">· {product.package_size}</span>
          )}
          {effectiveInterval && (
            <span className="ml-2 text-gray-500">
              · every {Math.round(effectiveInterval)}d
            </span>
          )}
          {displayBrand && (
            <span className="ml-2 text-gray-500">· {displayBrand}</span>
          )}
        </p>
      </div>

      {/* Right Segmented Touch Controls (Spans Columns 4–5) */}
      <div className="md:col-span-2 grid grid-cols-5 items-stretch border-t md:border-t-0 md:border-l border-gray-200 h-[74px] md:h-auto">
        {/* Decrement Button (-) */}
        <button
          onClick={() => onDecrement(item)}
          className="bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200 cursor-pointer"
          title="Decrease count"
        >
          <FigmaMinus className="w-6 h-6 fill-gunmetal" />
        </button>

        {/* Quantity Badge (Lime Cream) */}
        <div className="bg-limeCream flex flex-col items-center justify-center text-gunmetal px-1 select-none border-r border-gray-200">
          <span className="text-2xl font-extrabold leading-tight">{qty}</span>
          <span className="text-xs font-medium leading-none text-gunmetal/90 mt-0.5">
            units
          </span>
        </div>

        {/* Increment Button (+) */}
        <button
          onClick={() => onIncrement(item)}
          className="bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200 cursor-pointer"
          title="Increase count"
        >
          <FigmaPlus className="w-6 h-6 fill-gunmetal" />
        </button>

        {/* Edit Button */}
        <button
          onClick={() => onEdit(item)}
          className="bg-white hover:bg-gray-50 flex flex-col items-center justify-center text-gunmetal transition-colors border-r border-gray-200 gap-1 active:bg-gray-100 cursor-pointer"
          title="Edit item"
        >
          <FigmaEdit className="w-5 h-5 fill-gunmetal" />
          <span className="text-xs font-semibold leading-none text-gunmetal">
            Edit
          </span>
        </button>

        {/* Delete Button (Dusty Rose) */}
        <button
          onClick={() => onDelete(item)}
          className="bg-dustyRose hover:bg-dustyRose-dark text-gunmetal flex flex-col items-center justify-center transition-colors gap-1 active:opacity-90 cursor-pointer"
          title="Delete item"
        >
          <FigmaTrash className="w-5 h-5 fill-gunmetal" />
          <span className="text-xs font-semibold leading-none text-gunmetal">
            Delete
          </span>
        </button>
      </div>
    </div>
  );
}
