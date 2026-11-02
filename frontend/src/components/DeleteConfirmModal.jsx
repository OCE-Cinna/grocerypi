import React from "react";

export default function DeleteConfirmModal({ item, onConfirm, onCancel }) {
  if (!item) return null;
  const name = item.product?.name || "this item";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gunmetal/60 backdrop-blur-xs select-none">
      <div className="bg-white rounded-3xl p-8 sm:p-9 max-w-lg w-full shadow-2xl border border-gray-200">
        <h3 className="text-2xl sm:text-3xl font-extrabold text-gunmetal tracking-tight">
          Delete {name}?
        </h3>
        <p className="text-base text-kioskGray mt-3 leading-relaxed">
          Remove {name} from your stock inventory. This is an optional correction, not a daily stock update.
        </p>

        <div className="grid grid-cols-2 gap-4 mt-8">
          <button
            onClick={onCancel}
            className="h-16 rounded-2xl border-2 border-gray-300 bg-white hover:bg-gray-50 text-gunmetal font-bold text-lg transition-all active:scale-98 flex items-center justify-center"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(item)}
            className="h-16 rounded-2xl bg-dustyRose hover:bg-dustyRose-dark text-white font-bold text-lg transition-all active:scale-98 flex items-center justify-center shadow-sm"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
