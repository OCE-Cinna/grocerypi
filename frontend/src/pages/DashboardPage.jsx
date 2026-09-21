import { useState, useEffect, useCallback } from "react";
import { Plus, Loader2, LayoutGrid, RefreshCw } from "lucide-react";
import api from "../api/client";
import GroceryCard from "../components/GroceryCard";
import Modal from "../components/Modal";
import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create list modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const fetchLists = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/lists/");
      setLists(data);
    } catch {
      setError("Failed to load your grocery lists.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLists();
  }, [fetchLists]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setCreateError("");
    try {
      const { data } = await api.post("/lists/", {
        name: newName.trim(),
        description: newDesc.trim() || null,
      });
      setLists((prev) => [data, ...prev]);
      setModalOpen(false);
      setNewName("");
      setNewDesc("");
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Failed to create list.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Good {greeting()},{" "}
            <span className="text-brand-400">{user?.username}</span> 👋
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {lists.length === 0
              ? "Create your first grocery list to get started."
              : `You have ${lists.length} list${lists.length !== 1 ? "s" : ""}.`}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            id="refresh-lists-btn"
            onClick={fetchLists}
            className="btn-icon btn-ghost text-gray-400"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && lists.length === 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card h-40 animate-pulse bg-surface-700/50" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && lists.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-surface-700/50">
            <LayoutGrid size={32} className="text-gray-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-400">No lists yet</h2>
          <p className="mt-1 text-sm text-gray-600">
            Tap the + button to create your first grocery list.
          </p>
        </div>
      )}

      {/* Grid */}
      {lists.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {lists.map((list) => (
            <GroceryCard key={list.id} list={list} />
          ))}
        </div>
      )}

      {/* FAB */}
      <button
        id="create-list-fab"
        className="fab"
        onClick={() => setModalOpen(true)}
        aria-label="Create new grocery list"
      >
        <Plus size={24} strokeWidth={2.5} />
      </button>

      {/* Create list modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setCreateError(""); }}
        title="New Grocery List"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label htmlFor="list-name" className="mb-1.5 block text-xs font-medium text-gray-400">
              List Name *
            </label>
            <input
              id="list-name"
              className="input"
              placeholder="e.g. Weekly Shop, Party Supplies…"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="list-desc" className="mb-1.5 block text-xs font-medium text-gray-400">
              Description <span className="text-gray-600">(optional)</span>
            </label>
            <input
              id="list-desc"
              className="input"
              placeholder="Add a note…"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
            />
          </div>

          {createError && (
            <p className="text-xs text-red-400">{createError}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={() => { setModalOpen(false); setCreateError(""); }}
              className="btn-ghost flex-1"
            >
              Cancel
            </button>
            <button
              id="create-list-confirm-btn"
              type="submit"
              disabled={creating || !newName.trim()}
              className="btn-primary flex-1"
            >
              {creating ? <Loader2 size={15} className="animate-spin" /> : "Create"}
            </button>
          </div>
        </form>
      </Modal>
    </main>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 18) return "afternoon";
  return "evening";
}
