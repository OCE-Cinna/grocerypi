/**
 * Delete / Deplete Confirmation Modal component for GroceryPi.
 *
 * When the user taps 'Delete' (or decrements a 1-unit item to 0) on an active
 * inventory item, confirming marks the item as DEPLETED (0 units) and hides it
 * from the active Dashboard while keeping its learned restock interval for Cart
 * Suggestions. If the item is already depleted (viewed under 'Show Depleted'),
 * confirming permanently deletes it from the database.
 */

import React from "react";

export default function DeleteConfirmModal({ item, onConfirm, onCancel }) {
  if (!item) return null;
  const rawName = item.product?.name || "this item";
  const name = rawName
    .replace(/^(AH|Albert Heijn)\s+/i, "")
    .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
    .trim();

  const isAlreadyDepleted =
    item.status === "DEPLETED" || (item.quantity ?? 1) <= 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none">
      <div className="bg-white rounded-3xl p-8 sm:p-9 max-w-lg w-full shadow-2xl border border-gray-200">
        <h3 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight">
          {isAlreadyDepleted
            ? `Permanently delete ${name}?`
            : `Mark ${name} as depleted?`}
        </h3>
        <p className="text-base text-kioskGray mt-3 leading-relaxed">
          {isAlreadyDepleted
            ? `Completely remove ${name} and its restock interval history from the database.`
            : `Marks ${name} as finished (0 units), hides it from the active dashboard, and moves it to Cart Suggestions while keeping its learned restock interval.`}
        </p>

        <div className="grid grid-cols-2 gap-4 mt-8">
          <button
            onClick={onCancel}
            className="h-[74px] rounded-2xl border-2 border-gunmetal bg-transparent hover:bg-gray-50 text-gunmetal font-bold text-xl transition-all active:scale-98 flex items-center justify-center cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(item)}
            className="h-[74px] rounded-2xl bg-dustyRose hover:bg-dustyRose-dark text-gunmetal font-bold text-xl transition-all active:scale-98 flex items-center justify-center shadow-sm cursor-pointer"
          >
            {isAlreadyDepleted ? "Delete Forever" : "Mark Depleted"}
          </button>
        </div>
      </div>
    </div>
  );
}
