/**
 * Reusable Modal / Overlay Box component for GroceryPi.
 *
 * Matches the 7-inch kiosk wireframe specification: a centered white card with
 * dark Gunmetal headings, a dimmed background overlay, an optional subtitle,
 * a top-right close button, and space for large touch action buttons inside.
 */

import React, { useEffect } from "react";
import { FigmaClose } from "./FigmaIcons";

export default function Modal({ isOpen, onClose, title, subtitle, children }) {
  // Allow closing the modal by pressing the Escape key on a keyboard
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && onClose) onClose();
    };
    if (isOpen) document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none"
    >
      <div
        role="dialog"
        aria-modal="true"
        className="bg-white rounded-3xl p-8 sm:p-9 max-w-lg w-full shadow-2xl border border-gray-200 relative"
      >
        {/* Top-Right Close Button */}
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-5 right-5 p-2.5 text-gray-400 hover:text-gunmetal rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <FigmaClose className="w-6 h-6 fill-current" />
          </button>
        )}

        {/* Modal Title & Optional Description */}
        {title && (
          <h3 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight pr-10">
            {title}
          </h3>
        )}
        {subtitle && (
          <p className="text-base text-kioskGray mt-2.5 leading-relaxed">
            {subtitle}
          </p>
        )}

        {/* Custom Modal Content & Touch Buttons */}
        <div className="mt-7">{children}</div>
      </div>
    </div>
  );
}
