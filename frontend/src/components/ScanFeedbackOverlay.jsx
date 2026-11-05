import React, { useEffect, useState } from "react";
import { FigmaCheckmark, FigmaUndo } from "./FigmaIcons";

export default function ScanFeedbackOverlay({ scanEvent, onUndo, onClose }) {
  const [secondsRemaining, setSecondsRemaining] = useState(5);

  useEffect(() => {
    if (!scanEvent) return;
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
  }, [scanEvent, onClose]);

  if (!scanEvent) return null;

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

        {/* Undo Button (+15% larger: 83px high) */}
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
