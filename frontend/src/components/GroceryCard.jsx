import React from "react";
import { Plus, Minus, Pencil, Trash2 } from "lucide-react";

export default function GroceryCard({ item, activeSortNutrient, onIncrement, onDecrement, onEdit, onDelete }) {
  const product = item.product || {};
  const qty = item.quantity ?? 1;

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
          <h3 className="text-xl sm:text-2xl font-bold text-gunmetal tracking-tight">
            {product.name}
          </h3>
          <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-300">
            {product.category || "Food"}
          </span>
          {renderNutrientBadge()}
        </div>

        <p className="text-sm text-kioskGray font-normal mt-1.5">
          Last restocked · {formatDate(item.last_restocked_at)}
          {product.brand && <span className="ml-2 text-gray-400">({product.brand})</span>}
          {product.preferred_store && (
            <span className="ml-2 text-xs font-medium text-gray-500">[{product.preferred_store}]</span>
          )}
        </p>
      </div>

      {/* Right Segmented Controls (Landscape Kiosk Row) */}
      <div className="flex items-stretch border-t sm:border-t-0 sm:border-l border-gray-200 shrink-0 h-16 sm:h-auto">
        {/* Decrement Button */}
        <button
          onClick={() => onDecrement(item)}
          className="w-16 sm:w-20 bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200"
          title="Decrease count"
        >
          <Minus className="w-5 h-5 stroke-[2.5]" />
        </button>

        {/* Quantity Badge (Lime Cream) */}
        <div className="w-20 sm:w-24 bg-limeCream flex flex-col items-center justify-center text-gunmetal px-2 select-none border-r border-gray-200">
          <span className="text-2xl font-extrabold leading-tight">{qty}</span>
          <span className="text-[11px] font-medium leading-none text-gunmetal/90">units</span>
        </div>

        {/* Increment Button */}
        <button
          onClick={() => onIncrement(item)}
          className="w-16 sm:w-20 bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal transition-colors active:bg-gray-200 border-r border-gray-200"
          title="Increase count"
        >
          <Plus className="w-5 h-5 stroke-[2.5]" />
        </button>

        {/* Edit Button */}
        <button
          onClick={() => onEdit(item)}
          className="w-20 sm:w-24 bg-white hover:bg-gray-50 flex flex-col items-center justify-center text-gray-700 transition-colors border-r border-gray-200 gap-1 active:bg-gray-100"
          title="Edit item"
        >
          <Pencil className="w-4 h-4 stroke-[2]" />
          <span className="text-xs font-medium">Edit</span>
        </button>

        {/* Delete Button (Dusty Rose) */}
        <button
          onClick={() => onDelete(item)}
          className="w-20 sm:w-24 bg-dustyRose hover:bg-dustyRose-dark text-white flex flex-col items-center justify-center transition-colors gap-1 active:opacity-90"
          title="Delete item"
        >
          <Trash2 className="w-4 h-4 stroke-[2]" />
          <span className="text-xs font-medium text-white">Delete</span>
        </button>
      </div>
    </div>
  );
}
