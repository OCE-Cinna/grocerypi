import { useState } from "react";
import { Trash2, Pencil, Check } from "lucide-react";

export default function ItemRow({ item, onToggle, onDelete, onEdit }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(item.name);
  const [editQty, setEditQty] = useState(item.quantity || "1");
  const [editUnit, setEditUnit] = useState(item.unit || "");

  const handleEditSave = () => {
    if (!editName.trim()) return;
    onEdit(item.id, {
      name: editName.trim(),
      quantity: editQty.trim(),
      unit: editUnit.trim() || null,
    });
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <li
        id={`item-row-edit-${item.id}`}
        className="flex items-center gap-2 px-4 py-3 bg-surface-700/60 rounded-xl border border-brand-500/30 animate-scale-in"
      >
        <input
          className="input flex-1 py-1.5 text-sm"
          value={editName}
          onChange={(e) => setEditName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleEditSave()}
          autoFocus
          placeholder="Item name"
        />
        <input
          className="input w-20 py-1.5 text-sm"
          value={editQty}
          onChange={(e) => setEditQty(e.target.value)}
          placeholder="Qty"
        />
        <input
          className="input w-20 py-1.5 text-sm"
          value={editUnit}
          onChange={(e) => setEditUnit(e.target.value)}
          placeholder="Unit"
        />
        <button
          onClick={handleEditSave}
          className="btn-icon btn-primary shrink-0"
          title="Save"
        >
          <Check size={15} />
        </button>
        <button
          onClick={() => setIsEditing(false)}
          className="btn-icon btn-ghost shrink-0 text-gray-400"
          title="Cancel"
        >
          ✕
        </button>
      </li>
    );
  }

  return (
    <li
      id={`item-row-${item.id}`}
      className={`group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
        item.checked ? "opacity-60" : "hover:bg-surface-700/40"
      }`}
    >
      <input
        type="checkbox"
        className="grocery-checkbox shrink-0"
        checked={item.checked}
        onChange={() => onToggle(item.id, !item.checked)}
        id={`check-${item.id}`}
      />
      <label
        htmlFor={`check-${item.id}`}
        className={`flex-1 cursor-pointer select-none transition-all duration-200 ${
          item.checked ? "line-through text-gray-500" : "text-gray-200"
        }`}
      >
        <span className="font-medium">{item.name}</span>
        {(item.quantity || item.unit) && (
          <span className="ml-2 text-xs text-gray-500">
            {item.quantity} {item.unit}
          </span>
        )}
      </label>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
        <button
          onClick={() => setIsEditing(true)}
          className="btn-icon btn-ghost p-1.5 text-gray-500 hover:text-gray-200"
          title="Edit"
        >
          <Pencil size={13} />
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="btn-icon btn-danger p-1.5"
          title="Delete"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </li>
  );
}
