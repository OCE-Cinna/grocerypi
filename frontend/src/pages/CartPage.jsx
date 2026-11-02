import React, { useState } from "react";
import { ShoppingCart, CheckCircle2 } from "lucide-react";

export default function CartPage() {
  const [activeQueue, setActiveQueue] = useState("AH");
  const [synced, setSynced] = useState(false);

  // Store queues matching Figma
  const storeQueues = [
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
          quantityText: "2 × 1 L",
        },
        {
          id: 2,
          store: "AH",
          name: "Eggs",
          subtext: "Usually scanned every 10 days · due soon",
          quantityText: "1 × 12 pack",
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
          quantityText: "1 × 500 ml",
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
          quantityText: "1 × 1 kg",
        },
      ],
    },
  ];

  const currentQueue = storeQueues.find((q) => q.id === activeQueue) || storeQueues[0];

  const handleSyncCart = () => {
    setSynced(true);
    setTimeout(() => setSynced(false), 3000);
  };

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Page Title */}
      <div className="mb-6">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-gunmetal tracking-tight">
          Suggested Shopping List
        </h2>
        <p className="text-base text-kioskGray mt-1.5 font-normal">
          Likely replenishments, based on how often you scan items in.
        </p>
      </div>

      {/* Store Tabs (80px high, 3 horizontal queue cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-6">
        {storeQueues.map((q) => {
          const isActive = activeQueue === q.id;
          return (
            <button
              key={q.id}
              onClick={() => setActiveQueue(q.id)}
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
        {currentQueue.items.map((item) => (
          <div
            key={item.id}
            className="bg-white border border-gray-300/80 rounded-2xl p-5 sm:p-6 flex items-center justify-between shadow-xs"
          >
            <div className="flex items-center gap-3.5">
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold border border-gray-400 text-gray-700 bg-gray-50">
                {item.store}
              </span>
              <div>
                <h3 className="text-xl font-bold text-gunmetal tracking-tight">
                  {item.name}
                </h3>
                <p className="text-sm text-kioskGray mt-0.5 font-normal">
                  {item.subtext}
                </p>
              </div>
            </div>

            <span className="text-xl sm:text-2xl font-bold text-gunmetal shrink-0">
              {item.quantityText}
            </span>
          </div>
        ))}
      </div>

      {/* Primary Action Touch Button: Sync Cart */}
      <button
        onClick={handleSyncCart}
        className="w-full h-[76px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl flex items-center justify-center gap-3 transition-all active:scale-98 shadow-md"
      >
        {synced ? (
          <>
            <CheckCircle2 className="w-6 h-6 text-limeCream" />
            <span>Synced to {activeQueue} Cart!</span>
          </>
        ) : (
          <>
            <ShoppingCart className="w-6 h-6" />
            <span>Sync Recommended Items to Supermarket Cart (AH / Jumbo)</span>
          </>
        )}
      </button>

      {/* Footer Disclaimer */}
      <p className="text-xs text-kioskGray mt-4">
        Demo recommendations only · no live supermarket connection or order will be placed.
      </p>
    </div>
  );
}

