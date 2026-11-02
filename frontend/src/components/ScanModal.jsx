import React, { useState } from "react";
import { ArrowRight } from "lucide-react";
import { FigmaBarcode, FigmaClose } from "./FigmaIcons";

export default function ScanModal({ isOpen, onClose, onScanBarcode, sampleProducts = [] }) {
  const [barcodeInput, setBarcodeInput] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (barcodeInput.trim()) {
      onScanBarcode(barcodeInput.trim());
      setBarcodeInput("");
      onClose();
    }
  };

  const handlePickSample = (code) => {
    onScanBarcode(code);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none">
      <div className="bg-white rounded-3xl p-7 sm:p-8 max-w-lg w-full shadow-2xl border border-gray-200 relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 text-gray-400 hover:text-gunmetal rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
        >
          <FigmaClose className="w-5 h-5 fill-current" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="w-12 h-12 rounded-2xl bg-gunmetal text-white flex items-center justify-center">
            <FigmaBarcode className="w-7 h-7 stroke-white" />
          </div>
          <div>
            <h3 className="text-2xl font-extrabold text-gunmetal tracking-tight">Scan New Item</h3>
            <p className="text-sm text-kioskGray">Optical sensor ready · Or enter barcode below</p>
          </div>
        </div>

        {/* Barcode Form */}
        <form onSubmit={handleSubmit} className="mb-6">
          <div className="flex gap-2">
            <input
              type="text"
              value={barcodeInput}
              onChange={(e) => setBarcodeInput(e.target.value)}
              placeholder="e.g. 8710400035541"
              autoFocus
              className="flex-1 h-14 px-4 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-lg text-gunmetal font-medium outline-none transition-colors"
            />
            <button
              type="submit"
              className="h-14 px-6 rounded-xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold flex items-center gap-2 active:scale-95 transition-all"
            >
              <span>Scan</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </form>

        {/* Quick Sample Barcode Pills */}
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-kioskGray mb-2.5">
            Quick 1-Tap Barcode Test (Seed Catalog)
          </p>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
            {sampleProducts.slice(0, 6).map((p) => {
              const cleanName = (p.name || "")
                .replace(/^(AH|Albert Heijn)\s+/i, "")
                .replace(/\s+\b(AH|Albert Heijn)\b/i, "")
                .trim();
              return (
                <button
                  key={p.barcode}
                  type="button"
                  onClick={() => handlePickSample(p.barcode)}
                  className="p-3 text-left rounded-xl border border-gray-200 hover:border-gunmetal bg-parchment hover:bg-white transition-all text-xs flex flex-col justify-between"
                >
                  <span className="font-bold text-gunmetal truncate block">{cleanName}</span>
                  <span className="text-[10px] text-gray-500 font-mono mt-1">{p.barcode}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

