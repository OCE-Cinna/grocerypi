import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  M3ArrowBack as ArrowLeft,
  M3Add as Plus,
  M3Loader as Loader2,
  M3Trash as Trash2,
  M3CheckCircle as CheckCircle2,
  M3Circle as Circle,
  M3Package as Package
} from "../components/Material3Icons";
import { CelebrationIcon } from "../components/MaterialIcons";
import api from "../api/client";
import ItemRow from "../components/ItemRow";
import Modal from "../components/Modal";

export default function ListDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [list, setList] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Add item modal
  const [addOpen, setAddOpen] = useState(false);
  const [newItem, setNewItem] = useState({ name: "", quantity: "1", unit: "" });
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");

  // Delete list confirm
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/lists/${id}`);
      setList(data);
      setItems(data.items || []);
    } catch {
      setError("List not found or you don't have access.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  // ── Item actions ────────────────────────────────────────────────────────────

  const handleToggle = async (itemId, checked) => {
    setItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, checked } : i))
    );
    try {
      await api.put(`/lists/${id}/items/${itemId}`, { checked });
    } catch {
      // revert on failure
      setItems((prev) =>
        prev.map((i) => (i.id === itemId ? { ...i, checked: !checked } : i))
      );
    }
  };

  const handleEdit = async (itemId, updates) => {
    try {
      const { data } = await api.put(`/lists/${id}/items/${itemId}`, updates);
      setItems((prev) => prev.map((i) => (i.id === data.id ? data : i)));
    } catch {
      /* silent */
    }
  };

  const handleDelete = async (itemId) => {
    setItems((prev) => prev.filter((i) => i.id !== itemId));
    try {
      await api.delete(`/lists/${id}/items/${itemId}`);
    } catch {
      fetchList();
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newItem.name.trim()) return;
    setAdding(true);
    setAddError("");
    try {
      const { data } = await api.post(`/lists/${id}/items`, {
        name: newItem.name.trim(),
        quantity: newItem.quantity.trim() || "1",
        unit: newItem.unit.trim() || null,
      });
      setItems((prev) => [...prev, data]);
      setAddOpen(false);
      setNewItem({ name: "", quantity: "1", unit: "" });
    } catch (err) {
      setAddError(err.response?.data?.detail || "Failed to add item.");
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteList = async () => {
    setDeleting(true);
    try {
      await api.delete(`/lists/${id}`);
      navigate("/");
    } catch {
      setDeleting(false);
      setDeleteConfirm(false);
    }
  };

  // ── Stats ───────────────────────────────────────────────────────────────────

  const checkedCount = items.filter((i) => i.checked).length;
  const totalCount = items.length;
  const progress = totalCount > 0 ? (checkedCount / totalCount) * 100 : 0;
  const allDone = totalCount > 0 && checkedCount === totalCount;

  // ── Render ──────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 size={32} className="animate-spin text-brand-500" />
      </div>
    );
  }

  if (error || !list) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-red-400 mb-4">{error || "List not found."}</p>
        <button onClick={() => navigate("/")} className="btn-ghost inline-flex items-center gap-1.5">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      {/* Back */}
      <button
        id="back-to-dashboard-btn"
        onClick={() => navigate("/")}
        className="mb-6 flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ArrowLeft size={15} />
        All Lists
      </button>

      {/* List header */}
      <div className="card mb-6 animate-slide-up">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-white truncate">{list.name}</h1>
            {list.description && (
              <p className="mt-0.5 text-sm text-gray-500">{list.description}</p>
            )}
          </div>
          <button
            id="delete-list-btn"
            onClick={() => setDeleteConfirm(true)}
            className="btn-icon btn-danger ml-3 shrink-0"
            title="Delete list"
          >
            <Trash2 size={15} />
          </button>
        </div>

        {/* Progress */}
        {totalCount > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm">
                {allDone ? (
                  <CheckCircle2 size={16} className="text-brand-400" />
                ) : (
                  <Circle size={16} className="text-gray-600" />
                )}
                <span className={allDone ? "text-brand-400 font-semibold inline-flex items-center gap-1.5" : "text-gray-400"}>
                  {allDone ? (
                    <>
                      <span>All done!</span>
                      <CelebrationIcon className="w-4 h-4 text-brand-400" />
                    </>
                  ) : (
                    `${checkedCount} of ${totalCount} items checked`
                  )}
                </span>
              </div>
              <span className="text-xs text-gray-500">{Math.round(progress)}%</span>
            </div>
            <div className="h-2 rounded-full bg-surface-700 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  allDone ? "bg-brand-500" : "bg-brand-600"
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Items */}
      <div className="card animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Items ({totalCount})
          </h2>
          <button
            id="add-item-btn"
            onClick={() => setAddOpen(true)}
            className="btn-primary py-1.5 px-3 text-xs gap-1.5"
          >
            <Plus size={13} />
            Add Item
          </button>
        </div>

        {items.length === 0 && (
          <div className="flex flex-col items-center py-10 text-center text-gray-600">
            <Package size={28} className="mb-2" />
            <p className="text-sm">No items yet. Add something!</p>
          </div>
        )}

        {items.length > 0 && (
          <ul className="divide-y divide-surface-700/30 -mx-1">
            {/* Unchecked first */}
            {[...items]
              .sort((a, b) => Number(a.checked) - Number(b.checked))
              .map((item) => (
                <ItemRow
                  key={item.id}
                  item={item}
                  onToggle={handleToggle}
                  onDelete={handleDelete}
                  onEdit={handleEdit}
                />
              ))}
          </ul>
        )}
      </div>

      {/* FAB */}
      <button
        id="add-item-fab"
        className="fab"
        onClick={() => setAddOpen(true)}
        aria-label="Add grocery item"
      >
        <Plus size={24} strokeWidth={2.5} />
      </button>

      {/* Add item modal */}
      <Modal
        isOpen={addOpen}
        onClose={() => { setAddOpen(false); setAddError(""); }}
        title="Add Item"
      >
        <form onSubmit={handleAdd} className="space-y-4">
          <div>
            <label htmlFor="item-name" className="mb-1.5 block text-xs font-medium text-gray-400">
              Item Name *
            </label>
            <input
              id="item-name"
              className="input"
              placeholder="e.g. Apples, Milk, Bread..."
              value={newItem.name}
              onChange={(e) => setNewItem((f) => ({ ...f, name: e.target.value }))}
              required
              autoFocus
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="item-qty" className="mb-1.5 block text-xs font-medium text-gray-400">
                Quantity
              </label>
              <input
                id="item-qty"
                className="input"
                placeholder="1"
                value={newItem.quantity}
                onChange={(e) => setNewItem((f) => ({ ...f, quantity: e.target.value }))}
              />
            </div>
            <div>
              <label htmlFor="item-unit" className="mb-1.5 block text-xs font-medium text-gray-400">
                Unit <span className="text-gray-600">(optional)</span>
              </label>
              <input
                id="item-unit"
                className="input"
                placeholder="kg, pcs, ml..."
                value={newItem.unit}
                onChange={(e) => setNewItem((f) => ({ ...f, unit: e.target.value }))}
              />
            </div>
          </div>

          {addError && <p className="text-xs text-red-400">{addError}</p>}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={() => { setAddOpen(false); setAddError(""); }}
              className="btn-ghost flex-1"
            >
              Cancel
            </button>
            <button
              id="add-item-confirm-btn"
              type="submit"
              disabled={adding || !newItem.name.trim()}
              className="btn-primary flex-1"
            >
              {adding ? <Loader2 size={15} className="animate-spin" /> : "Add"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete confirm modal */}
      <Modal
        isOpen={deleteConfirm}
        onClose={() => setDeleteConfirm(false)}
        title="Delete List?"
      >
        <p className="text-sm text-gray-400 mb-6">
          Are you sure you want to delete <span className="font-semibold text-white">"{list.name}"</span>?
          This will permanently remove all {totalCount} item{totalCount !== 1 ? "s" : ""} in this list.
        </p>
        <div className="flex gap-3">
          <button onClick={() => setDeleteConfirm(false)} className="btn-ghost flex-1">
            Cancel
          </button>
          <button
            id="delete-list-confirm-btn"
            onClick={handleDeleteList}
            disabled={deleting}
            className="btn-danger flex-1 bg-red-600 text-white hover:bg-red-500"
          >
            {deleting ? <Loader2 size={15} className="animate-spin" /> : "Delete"}
          </button>
        </div>
      </Modal>
    </main>
  );
}
