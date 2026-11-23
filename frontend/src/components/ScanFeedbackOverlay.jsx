/**
 * Barcode Scan Feedback & Confirmation Overlay for GroceryPi.
 *
 * Displays two clear states after a barcode is read:
 * 1. SUCCESS: Shows the product name, new quantity, a 5-second auto-dismiss
 *    timer, and a large 'Undo' button.
 * 2. UNKNOWN_BARCODE: When a scanned barcode is not found in Albert Heijn or
 *    Open Food Facts (or was misread due to motion blur), stops it from
 *    silently entering the database and asks the user to either 'Redo Scan'
 *    or 'Confirm & Add Custom Item'.
 */

import React, { useEffect, useState } from "react";
import { FigmaBarcode, FigmaCheckmark, FigmaUndo } from "./FigmaIcons";

export default function ScanFeedbackOverlay({
  scanEvent,
  onUndo,
  onConfirmUnknown,
  onClose,
}) {
  const [secondsRemaining, setSecondsRemaining] = useState(5);
  const isUnknown = scanEvent?.scan_status === "UNKNOWN_BARCODE";

  // Only start the 5-second auto-close timer when a recognized product was added
  useEffect(() => {
    if (!scanEvent || isUnknown) return;
    setSecondsRemaining(5);

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    const timer = setTimeout(() => {
      if (onClose) onClose();
    }, 5000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [scanEvent, isUnknown, onClose]);

  if (!scanEvent) return null;

  // State 2: Unrecognized or motion-blurred barcode -> Ask user to Redo or Confirm
  if (isUnknown) {
    const rawCode = scanEvent.barcode || "";
    const isValidLength = /^\d{8}$|^\d{12,14}$/.test(rawCode);

    return (
      <div
        onClick={(e) => {
          if (e.target === e.currentTarget && onClose) onClose();
        }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none"
      >
        <div className="bg-white rounded-3xl p-8 sm:p-10 max-w-lg w-full shadow-2xl border border-gray-200 text-center relative animate-scale-in">
          <div className="w-16 h-16 rounded-2xl bg-dustyRose/40 flex items-center justify-center mx-auto mb-5 shadow-xs">
            <FigmaBarcode className="w-8 h-8 fill-gunmetal" />
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight">
            {isValidLength ? "Barcode Not Recognized" : "Unclear Barcode Read"}
          </h2>

          <p className="text-base font-mono font-bold text-gunmetal mt-2">
            {rawCode}
          </p>

          <p className="text-base text-kioskGray mt-2.5 leading-relaxed">
            {isValidLength
              ? "This barcode was not found in Albert Heijn or Open Food Facts. Hold the item steady and redo the scan if it was misread, or confirm to add it as a custom item."
              : "The camera read an incomplete number (likely due to motion blur). Please hold the item steady 10–25 cm from the lens and redo the scan."}
          </p>

          <div className="mt-7 space-y-3.5">
            <button
              type="button"
              onClick={onClose}
              className="w-full h-[74px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl flex items-center justify-center gap-3 active:scale-98 transition-all shadow-md cursor-pointer"
            >
              <span>Redo Scan (Try Again)</span>
            </button>

            {isValidLength && onConfirmUnknown && (
              <button
                type="button"
                onClick={() => onConfirmUnknown(rawCode)}
                className="w-full h-[68px] rounded-2xl border-2 border-gunmetal bg-transparent hover:bg-gray-50 text-gunmetal font-bold text-lg flex items-center justify-center active:scale-98 transition-all cursor-pointer"
              >
                <span>Confirm &amp; Add Custom Item</span>
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // State 1: Recognized product added -> Show confirmation & 5-second Undo button
  const product = scanEvent.product || {};
  const inv = scanEvent.inventory_item || {};
  const packageSize = product.package_size || "1 unit";
  const qty = inv.quantity ?? 1;

  const cleanName = (product.name || "Item Scanned")
    .replace(/^(AH|Albert Heijn)\s+/i, "")
    .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
    .trim();

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none"
    >
      <div className="bg-white rounded-3xl p-8 sm:p-10 max-w-lg w-full shadow-2xl border border-gray-200 text-center relative animate-scale-in">
        {/* Top Lime Cream Check Icon */}
        <div className="w-16 h-16 rounded-2xl bg-limeCream flex items-center justify-center mx-auto mb-5 shadow-xs">
          <FigmaCheckmark className="w-8 h-8 fill-gunmetal" />
        </div>

        {/* Product Name */}
        <h2 className="text-3xl font-extrabold text-gunmetal tracking-tight">
          {cleanName}
        </h2>

        {/* Status Line */}
        <p className="text-xl font-bold text-gunmetal mt-2">
          Added to Stock Inventory
        </p>

        {/* Added & Total Count Detail */}
        <p className="text-base text-kioskGray mt-2 font-normal">
          1 × {packageSize} added · {qty} units now recorded
        </p>

        {/* Undo Button (83px high) */}
        <div className="mt-8">
          <button
            onClick={() => onUndo(scanEvent)}
            className="w-full h-[83px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-2xl flex items-center justify-center gap-3.5 active:scale-98 transition-all shadow-md cursor-pointer"
          >
            <FigmaUndo className="w-7 h-7 fill-white" />
            <span>Undo</span>
          </button>
        </div>

        {/* Auto-Dismiss 5-Second Progress Bar */}
        <div className="w-full bg-gray-100 rounded-full h-1.5 mt-6 overflow-hidden">
          <div className="bg-limeCream h-full rounded-full animate-auto-dismiss" />
        </div>
        <p className="text-xs text-kioskGray mt-2 font-medium">
          Auto-closing in {secondsRemaining}s
        </p>

        {/* Bottom Hardware Subtext */}
        <p className="text-xs text-gray-400 mt-3">
          {scanEvent.device_info || "Demo scan · no barcode hardware connected"}
        </p>
      </div>
    </div>
  );
}
