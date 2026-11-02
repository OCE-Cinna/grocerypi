import React, { useState, useEffect } from "react";
import { FigmaBarcode, FigmaClose } from "./FigmaIcons";

export default function ScanModal({ isOpen, onClose, onScanBarcode, sampleProducts = [] }) {
  const [barcodeInput, setBarcodeInput] = useState("");
  const [streamError, setStreamError] = useState(false);
  const [streamLoaded, setStreamLoaded] = useState(false);
  const [streamUrl, setStreamUrl] = useState("");

  useEffect(() => {
    if (isOpen) {
      // Connect fresh MJPEG stream with timestamp to prevent stale browser caching
      setStreamUrl(`/scanner/preview?t=${Date.now()}`);
      setStreamError(false);
      setStreamLoaded(false);
    } else {
      setStreamUrl("");
    }
  }, [isOpen]);

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
      <div className="bg-white rounded-3xl p-6 sm:p-7 max-w-lg w-full shadow-2xl border border-gray-200 relative max-h-[92vh] flex flex-col overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 text-gray-400 hover:text-gunmetal rounded-xl hover:bg-gray-100 transition-colors cursor-pointer z-10"
          aria-label="Close scan modal"
        >
          <FigmaClose className="w-5 h-5 fill-current" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-11 h-11 rounded-2xl bg-gunmetal text-white flex items-center justify-center shrink-0">
            <FigmaBarcode className="w-6 h-6 stroke-white" />
          </div>
          <div>
            <h3 className="text-2xl font-extrabold text-gunmetal tracking-tight leading-tight">
              Scan New Item
            </h3>
            <p className="text-xs sm:text-sm text-kioskGray font-medium">
              Live optical scanner · Hold barcode in camera frame
            </p>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="overflow-y-auto pr-1 flex-1 space-y-4">
          {/* Live Camera Viewfinder */}
          <div className="relative w-full h-56 sm:h-64 rounded-2xl overflow-hidden bg-gunmetal-dark border-2 border-gunmetal shadow-inner flex items-center justify-center group">
            {/* Live MJPEG Feed */}
            {streamUrl && !streamError && (
              <img
                src={streamUrl}
                alt="Raspberry Pi Camera Module v3 live preview"
                className={`w-full h-full object-cover transition-opacity duration-300 ${
                  streamLoaded ? "opacity-100" : "opacity-0"
                }`}
                onLoad={() => setStreamLoaded(true)}
                onError={() => setStreamError(true)}
              />
            )}

            {/* Loading / Error Fallback Placeholder */}
            {(!streamLoaded || streamError) && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gunmetal-dark text-parchment p-4 text-center">
                <div className="w-12 h-12 rounded-full border-3 border-limeCream border-t-transparent animate-spin mb-3" />
                <p className="text-sm font-bold text-limeCream">
                  {streamError ? "Hardware Viewfinder Standby" : "Connecting Camera Module v3..."}
                </p>
                <p className="text-xs text-kioskGray-light mt-1 max-w-xs">
                  {streamError
                    ? "Camera is actively scanning in background · Center barcode in lens field"
                    : "Continuous autofocus (PDAF) calibrating lens"}
                </p>
              </div>
            )}

            {/* Viewfinder Overlays & Reticle (Always visible on top of stream) */}
            <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-between p-3.5">
              {/* Top Status Badges */}
              <div className="w-full flex items-center justify-between">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gunmetal-dark/85 backdrop-blur-xs border border-white/10 text-[11px] font-semibold text-parchment shadow-xs">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-limeCream opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-limeCream"></span>
                  </span>
                  <span>LIVE SENSOR</span>
                </div>

                <div className="px-2.5 py-1 rounded-full bg-gunmetal-dark/85 backdrop-blur-xs border border-white/10 text-[11px] font-medium text-parchment shadow-xs">
                  PDAF Autofocus Active
                </div>
              </div>

              {/* Central Barcode Targeting Box / Reticle */}
              <div className="relative w-56 h-32 sm:w-64 sm:h-36 flex items-center justify-center">
                {/* 4 Corner Targeting Brackets */}
                <span className="absolute top-0 left-0 w-6 h-6 border-t-3 border-l-3 border-limeCream rounded-tl-md shadow-xs"></span>
                <span className="absolute top-0 right-0 w-6 h-6 border-t-3 border-r-3 border-limeCream rounded-tr-md shadow-xs"></span>
                <span className="absolute bottom-0 left-0 w-6 h-6 border-b-3 border-l-3 border-limeCream rounded-bl-md shadow-xs"></span>
                <span className="absolute bottom-0 right-0 w-6 h-6 border-b-3 border-r-3 border-limeCream rounded-br-md shadow-xs"></span>

                {/* Subtle Center Crosshair Guide */}
                <div className="w-8 h-8 relative flex items-center justify-center opacity-40">
                  <span className="w-4 h-0.5 bg-white rounded-full"></span>
                  <span className="w-0.5 h-4 bg-white rounded-full absolute"></span>
                </div>

                {/* Animated Horizontal Laser Scan Beam */}
                <div className="absolute inset-x-2 h-0.5 bg-gradient-to-r from-transparent via-limeCream to-transparent animate-pulse shadow-[0_0_8px_rgba(195,228,139,0.9)]"></div>
              </div>

              {/* Distance Guidance Pill */}
              <div className="px-3.5 py-1.5 rounded-full bg-gunmetal-dark/90 backdrop-blur-xs border border-limeCream/40 text-xs font-semibold text-limeCream shadow-lg flex items-center gap-2">
                <svg
                  className="w-4 h-4 fill-none stroke-current"
                  viewBox="0 0 24 24"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                  <line x1="12" y1="22.08" x2="12" y2="12" />
                </svg>
                <span>Optimal Distance: 10 – 25 cm (4 – 10 in)</span>
              </div>
            </div>
          </div>

          {/* Quick Framing Helper Tips */}
          <div className="grid grid-cols-3 gap-2 text-center text-[11px] font-medium text-gunmetal bg-parchment p-2.5 rounded-xl border border-parchment-border">
            <div className="flex flex-col items-center">
              <span className="font-bold text-gunmetal">1. Frame</span>
              <span className="text-kioskGray text-[10px]">Center in green box</span>
            </div>
            <div className="flex flex-col items-center border-x border-parchment-border px-1">
              <span className="font-bold text-gunmetal">2. Distance</span>
              <span className="text-kioskGray text-[10px]">10 to 25 cm from lens</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="font-bold text-gunmetal">3. Instant Scan</span>
              <span className="text-kioskGray text-[10px]">Autofocus reads &lt; 0.5s</span>
            </div>
          </div>

          {/* Manual Barcode Form */}
          <form onSubmit={handleSubmit}>
            <p className="text-xs font-bold uppercase tracking-wider text-kioskGray mb-1.5">
              Or Enter Barcode Manually
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={barcodeInput}
                onChange={(e) => setBarcodeInput(e.target.value)}
                placeholder="e.g. 8710400035541"
                className="flex-1 h-12 px-3.5 rounded-xl border-2 border-gray-300 focus:border-gunmetal text-base text-gunmetal font-medium outline-none transition-colors"
              />
              <button
                type="submit"
                className="h-12 px-5 rounded-xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold flex items-center gap-2 active:scale-95 transition-all text-sm shrink-0 cursor-pointer"
              >
                <span>Add</span>
                <svg
                  className="w-4 h-4 fill-none stroke-current"
                  viewBox="0 0 24 24"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </button>
            </div>
          </form>

          {/* Quick Sample Barcode Pills (Seed Catalog) */}
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-kioskGray mb-2">
              Quick 1-Tap Barcode Test (Seed Catalog)
            </p>
            <div className="grid grid-cols-2 gap-2 max-h-36 overflow-y-auto pr-1">
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
                    className="p-2.5 text-left rounded-xl border border-gray-200 hover:border-gunmetal bg-parchment hover:bg-white transition-all text-xs flex flex-col justify-between cursor-pointer active:scale-98"
                  >
                    <span className="font-bold text-gunmetal truncate block">{cleanName}</span>
                    <span className="text-[10px] text-gray-500 font-mono mt-0.5">{p.barcode}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
