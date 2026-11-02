import React from "react";
import { Check, Undo2 } from "lucide-react";

export default function ScanFeedbackOverlay({ scanEvent, onUndo, onClose }) {
  if (!scanEvent) return null;

  const product = scanEvent.product || {};
  const inv = scanEvent.inventory_item || {};
  const packageSize = product.package_size || "1 unit";
  const qty = inv.quantity ?? 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none">
      <div className="bg-white rounded-3xl p-8 sm:p-10 max-w-lg w-full shadow-2xl border border-gray-200 text-center relative">
        {/* Top Lime Cream Check Icon */}
        <div className="w-16 h-16 rounded-2xl bg-limeCream flex items-center justify-center mx-auto mb-5 shadow-xs">
          <Check className="w-9 h-9 stroke-[3] text-gunmetal" />
        </div>

        {/* Product Name */}
        <h2 className="text-3xl font-extrabold text-gunmetal tracking-tight">
          {product.name || "Item Scanned"}
        </h2>

        {/* Status Line */}
        <p className="text-xl font-bold text-gunmetal mt-2">
          Added to Stock Inventory
        </p>

        {/* Added & Total Count Detail */}
        <p className="text-base text-kioskGray mt-2 font-normal">
          1 × {packageSize} added · {qty} units now recorded
        </p>

        {/* Undo Button (Gunmetal #383D3B) */}
        <div className="mt-8">
          <button
            onClick={() => onUndo(scanEvent)}
            className="w-full h-18 rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl flex items-center justify-center gap-3 active:scale-98 transition-all shadow-md"
          >
            <Undo2 className="w-6 h-6 stroke-[2.5]" />
            <span>Undo</span>
          </button>
        </div>

        {/* Bottom Hardware Subtext */}
        <p className="text-xs text-gray-400 mt-5">
          {scanEvent.device_info || "Demo scan · no barcode hardware connected"}
        </p>
      </div>
    </div>
  );
}
