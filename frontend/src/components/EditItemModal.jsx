/**
 * Edit Item Modal component for GroceryPi.
 *
 * Opens a clean pop-up box when the user taps 'Edit' on any inventory card.
 * Keeps the same wireframe look as DeleteConfirmModal and allows editing:
 * 1. Product Name and Package Size (useful for renaming fallback scanned items).
 * 2. Preferred Store badge (AH, Jumbo, Lidl, or Other).
 * 3. Custom Restock Interval in days (how often the item is usually bought).
 */

import React, { useState, useEffect } from "react";
import { FigmaClose, FigmaMinus, FigmaPlus } from "./FigmaIcons";

const STORES = ["AH", "Jumbo", "Lidl", "Other"];

export default function EditItemModal({ item, onSave, onCancel }) {
  const [name, setName] = useState("");
  const [packageSize, setPackageSize] = useState("");
  const [preferredStore, setPreferredStore] = useState("AH");
  const [intervalDays, setIntervalDays] = useState(7);
  const [saving, setSaving] = useState(false);

  // Fill the form with the current item details whenever an item is opened for editing
  useEffect(() => {
    if (!item) return;
    const product = item.product || {};
    const cleanName = (product.name || "")
      .replace(/^(AH|Albert Heijn)\s+/i, "")
      .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
      .trim();

    setName(cleanName || product.name || "");
    setPackageSize(product.package_size || "1 unit");
    setPreferredStore(product.preferred_store || "AH");
    const effectiveInterval =
      item.manual_interval_override ?? item.restock_interval_days ?? 7;
    setIntervalDays(Math.max(1, Math.round(effectiveInterval)));
  }, [item]);

  if (!item) return null;

  /**
   * Sends the updated product and restock interval settings back to App.jsx
   * when the user taps the 'Save' button.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSave(item, {
        name: name.trim(),
        package_size: packageSize.trim() || "1 unit",
        preferred_store: preferredStore,
        manual_interval_override: Math.max(1, Number(intervalDays) || 7),
      });
    } finally {
      setSaving(false);
    }
  };

  /**
   * Adjusts the restock interval days up or down using large touch buttons.
   */
  const adjustInterval = (delta) => {
    setIntervalDays((prev) => Math.max(1, (Number(prev) || 7) + delta));
  };

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && onCancel) onCancel();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none"
    >
      <div className="bg-white rounded-3xl p-7 sm:p-8 max-w-lg w-full shadow-2xl border border-gray-200 relative">
        {/* Top-Right Close Button */}
        <button
          type="button"
          onClick={onCancel}
          className="absolute top-5 right-5 p-2.5 text-gray-400 hover:text-gunmetal rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
          aria-label="Close edit modal"
        >
          <FigmaClose className="w-6 h-6 fill-current" />
        </button>

        {/* Modal Title & Barcode Subtitle */}
        <h3 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight pr-10">
          Edit Item
        </h3>
        <p className="text-sm text-kioskGray mt-1 font-mono">
          Barcode · {item.product?.barcode}
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          {/* 1. Product Name & Package Size */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
                Product Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Product name"
                required
                className="w-full h-[54px] px-4 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base font-bold text-gunmetal outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
                Package Size
              </label>
              <input
                type="text"
                value={packageSize}
                onChange={(e) => setPackageSize(e.target.value)}
                placeholder="e.g. 1 L or 500g"
                className="w-full h-[54px] px-3.5 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base font-semibold text-gunmetal outline-none transition-colors"
              />
            </div>
          </div>

          {/* 2. Preferred Store Selector Buttons */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
              Preferred Store
            </label>
            <div className="grid grid-cols-4 gap-2.5">
              {STORES.map((store) => {
                const isSelected = preferredStore === store;
                return (
                  <button
                    key={store}
                    type="button"
                    onClick={() => setPreferredStore(store)}
                    className={`h-[54px] rounded-xl font-bold text-base transition-all flex items-center justify-center cursor-pointer active:scale-98 border-2 ${
                      isSelected
                        ? "bg-gunmetal text-white border-gunmetal shadow-xs"
                        : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {store}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Restock Interval (Days) Override */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
              Restock Interval (Usually bought every X days)
            </label>
            <div className="flex items-stretch h-[58px] rounded-2xl border-2 border-gray-300 overflow-hidden bg-white">
              <button
                type="button"
                onClick={() => adjustInterval(-1)}
                className="w-[68px] bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal border-r border-gray-300 active:bg-gray-200 transition-colors cursor-pointer"
                title="Decrease days"
              >
                <FigmaMinus className="w-5 h-5 fill-gunmetal" />
              </button>

              <div className="flex-1 flex items-center justify-center gap-2 px-3 bg-limeCream/30">
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={intervalDays}
                  onChange={(e) => setIntervalDays(e.target.value)}
                  className="w-16 text-center text-xl font-extrabold text-gunmetal bg-transparent outline-none"
                />
                <span className="text-sm font-bold text-gunmetal">days</span>
              </div>

              <button
                type="button"
                onClick={() => adjustInterval(1)}
                className="w-[68px] bg-parchment hover:bg-parchment-hover flex items-center justify-center text-gunmetal border-l border-gray-300 active:bg-gray-200 transition-colors cursor-pointer"
                title="Increase days"
              >
                <FigmaPlus className="w-5 h-5 fill-gunmetal" />
              </button>
            </div>
          </div>

          {/* Bottom Cancel & Save Touch Buttons (matching DeleteConfirmModal layout) */}
          <div className="grid grid-cols-2 gap-4 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="h-[68px] rounded-2xl border-2 border-gunmetal bg-transparent hover:bg-gray-50 text-gunmetal font-bold text-xl transition-all active:scale-98 flex items-center justify-center cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="h-[68px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl transition-all active:scale-98 flex items-center justify-center shadow-sm cursor-pointer"
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
