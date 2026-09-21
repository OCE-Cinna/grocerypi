import { useNavigate } from "react-router-dom";
import { ShoppingBasket, ChevronRight, CheckCircle2 } from "lucide-react";

export default function GroceryCard({ list }) {
  const navigate = useNavigate();
  const progress =
    list.item_count > 0 ? (list.checked_count / list.item_count) * 100 : 0;
  const allDone = list.item_count > 0 && list.checked_count === list.item_count;

  return (
    <article
      id={`grocery-card-${list.id}`}
      className="card-hover group relative overflow-hidden animate-slide-up"
      onClick={() => navigate(`/lists/${list.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && navigate(`/lists/${list.id}`)}
    >
      {/* Subtle top accent */}
      <div
        className={`absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl transition-all duration-300 ${
          allDone ? "bg-brand-500" : "bg-surface-600 group-hover:bg-brand-700"
        }`}
      />

      <div className="flex items-start justify-between mb-3">
        {/* Icon */}
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl transition-colors duration-200 ${
            allDone
              ? "bg-brand-500/20 text-brand-400"
              : "bg-surface-700 text-gray-400 group-hover:bg-brand-500/10 group-hover:text-brand-400"
          }`}
        >
          {allDone ? (
            <CheckCircle2 size={20} />
          ) : (
            <ShoppingBasket size={20} />
          )}
        </div>

        <ChevronRight
          size={16}
          className="text-gray-600 group-hover:text-brand-400 group-hover:translate-x-0.5 transition-all duration-200 mt-1"
        />
      </div>

      {/* Name */}
      <h3 className="font-semibold text-base text-white mb-1 truncate pr-2">
        {list.name}
      </h3>

      {/* Description */}
      {list.description && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{list.description}</p>
      )}

      {/* Progress bar */}
      {list.item_count > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-gray-500">
              {list.checked_count}/{list.item_count} items
            </span>
            <span className={`text-xs font-medium ${allDone ? "text-brand-400" : "text-gray-400"}`}>
              {Math.round(progress)}%
            </span>
          </div>
          <div className="h-1 rounded-full bg-surface-600 overflow-hidden">
            <div
              className="h-full rounded-full bg-brand-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {list.item_count === 0 && (
        <p className="text-xs text-gray-600 mt-2 italic">No items yet</p>
      )}
    </article>
  );
}
