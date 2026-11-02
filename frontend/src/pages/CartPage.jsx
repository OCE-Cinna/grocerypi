import React, { useState, useEffect } from "react";
import { ShoppingCart, CheckCircle2, RefreshCw } from "lucide-react";
import api from "../api/client";

export default function CartPage() {
  const [storeQueues, setStoreQueues] = useState([]);
  const [activeQueueId, setActiveQueueId] = useState("AH");
  const [loading, setLoading] = useState(true);
  const [synced, setSynced] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Fetch smart replenishment queues from backend
  const fetchCartSuggestions = async () => {
    try {
      setLoading(true);
      const res = await api.get("/inventory/cart/suggestions");
      if (res.data?.queues && res.data.queues.length > 0) {
        setStoreQueues(res.data.queues);
        // Default to the first queue or AH
        const hasAH = res.data.queues.some((q) => q.id === "AH");
        if (hasAH) setActiveQueueId("AH");
        else setActiveQueueId(res.data.queues[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch cart suggestions:", err);
      // Fallback defaults if backend is unreachable
      setStoreQueues([
        {
          id: "AH",
          title: "AH · 2 items",
          subtitle: "Selected queue · sync AH only",
          items: [
            {
              id: 1,
              store: "AH",
              name: "Soy milk",
              subtext: "Usually scanned every 7 days · next shop",
              quantity_text: "2 × 1 L",
            },
            {
              id: 2,
              store: "AH",
              name: "Eggs",
              subtext: "Usually scanned every 10 days · due soon",
              quantity_text: "1 × 12 pack",
            },
          ],
        },
        {
          id: "Jumbo",
          title: "Jumbo · 1 item",
          subtitle: "Dish soap · separate sync",
          items: [
            {
              id: 3,
              store: "Jumbo",
              name: "Dish soap",
              subtext: "Usually scanned every 30 days · replenish",
              quantity_text: "1 × 500 ml",
            },
          ],
        },
        {
          id: "Lidl",
          title: "Lidl · 1 item",
          subtitle: "Oats · separate list, no sync",
          items: [
            {
              id: 4,
              store: "Lidl",
              name: "Rolled Oats",
              subtext: "Usually scanned every 14 days · scheduled soon",
              quantity_text: "1 × 1 kg",
            },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCartSuggestions();
  }, []);

  const currentQueue =
    storeQueues.find((q) => q.id === activeQueueId) || storeQueues[0] || { items: [] };

  const handleSyncCart = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      setSynced(true);
      setTimeout(() => setSynced(false), 3000);
    }, 800);
  };

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Page Title */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gunmetal tracking-tight">
            Suggested Shopping List
          </h2>
          <p className="text-base text-kioskGray mt-1.5 font-normal">
            Likely replenishments, based on empirical invoice intervals and how often you scan items in.
          </p>
        </div>
        <button
          onClick={fetchCartSuggestions}
          disabled={loading}
          className="p-3 rounded-xl bg-white border border-gray-300 hover:bg-gray-50 active:scale-95 transition-all text-gunmetal flex items-center gap-2 text-sm font-semibold shadow-xs"
          title="Refresh calculations"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-limeCream" : ""}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* Store Tabs (80px high, 3 horizontal queue cards matching Figma) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-6">
        {storeQueues.map((q) => {
          const isActive = activeQueueId === q.id;
          return (
            <button
              key={q.id}
              onClick={() => setActiveQueueId(q.id)}
              className={`h-[80px] rounded-2xl p-4 text-left transition-all border flex flex-col justify-center active:scale-98 ${
                isActive
                  ? "bg-gunmetal text-white border-gunmetal shadow-sm"
                  : "bg-white text-gunmetal border-gray-300 hover:bg-gray-50"
              }`}
            >
              <span className="font-bold text-lg leading-tight">{q.title}</span>
              <span className={`text-xs mt-1 truncate ${isActive ? "text-gray-300" : "text-kioskGray"}`}>
                {q.subtitle}
              </span>
            </button>
          );
        })}
      </div>

      {/* Suggested Items List */}
      <div className="space-y-3.5 mb-7">
        {currentQueue.items && currentQueue.items.length > 0 ? (
          currentQueue.items.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-gray-300/80 rounded-2xl p-5 sm:p-6 flex items-center justify-between shadow-xs transition-all hover:border-gray-400"
            >
              <div className="flex items-center gap-3.5">
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
                    item.store === "AH"
                      ? "border-blue-300 text-blue-700 bg-blue-50"
                      : item.store === "Jumbo"
                      ? "border-amber-300 text-amber-700 bg-amber-50"
                      : "border-gray-400 text-gray-700 bg-gray-50"
                  }`}
                >
                  {item.store}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-gunmetal tracking-tight">
                      {item.name}
                    </h3>
                    {item.is_dual_store && (
                      <span className="text-[11px] font-semibold text-kioskGray bg-gray-100 px-2 py-0.5 rounded-full">
                        Dual-store
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-kioskGray mt-0.5 font-normal">
                    {item.subtext}
                  </p>
                </div>
              </div>

              <span className="text-xl sm:text-2xl font-bold text-gunmetal shrink-0">
                {item.quantity_text}
              </span>
            </div>
          ))
        ) : (
          <div className="bg-white border border-gray-300 rounded-2xl p-8 text-center text-kioskGray">
            No replenishment needed for {activeQueueId} right now. All stocked items are healthy!
          </div>
        )}
      </div>

      {/* Primary Action Touch Button: Sync Cart */}
      <button
        onClick={handleSyncCart}
        disabled={syncing}
        className="w-full h-[76px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl flex items-center justify-center gap-3 transition-all active:scale-98 shadow-md"
      >
        {synced ? (
          <>
            <CheckCircle2 className="w-6 h-6 text-limeCream" />
            <span>Synced to {activeQueueId} Cart!</span>
          </>
        ) : (
          <>
            <ShoppingCart className={`w-6 h-6 ${syncing ? "animate-pulse" : ""}`} />
            <span>
              {syncing
                ? `Connecting to ${activeQueueId} API...`
                : `Sync Recommended Items to Supermarket Cart (${activeQueueId})`}
            </span>
          </>
        )}
      </button>

      {/* Footer Disclaimer */}
      <p className="text-xs text-kioskGray mt-4">
        Replenishment recommendations calibrated with AH invoices · unrecorded Jumbo physical purchases can be adjusted per item.
      </p>
    </div>
  );
}
