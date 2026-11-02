import React from "react";

export default function NutritionPage({ summary, onSelectNutrientSort }) {
  // Nutrient metrics in strict order with live summary calculations or fallback estimates
  const metrics = [
    {
      key: "protein_grams",
      label: "Protein",
      total: summary?.total_protein_grams ?? 180,
      unit: "g",
      max: 300,
    },
    {
      key: "carbohydrate_grams",
      label: "Carbohydrates",
      total: summary?.total_carbohydrate_grams ?? 620,
      unit: "g",
      max: 1000,
    },
    {
      key: "sugar_grams",
      label: "Sugar",
      total: summary?.total_sugar_grams ?? 95,
      unit: "g",
      max: 200,
    },
    {
      key: "fat_grams",
      label: "Fat",
      total: summary?.total_fat_grams ?? 125,
      unit: "g",
      max: 250,
    },
    {
      key: "saturated_fat_grams",
      label: "Saturated Fat",
      total: summary?.total_saturated_fat_grams ?? 38,
      unit: "g",
      max: 80,
    },
    {
      key: "fiber_grams",
      label: "Fibers",
      total: summary?.total_fiber_grams ?? 65,
      unit: "g",
      max: 150,
    },
    {
      key: "salt_grams",
      label: "Salt",
      total: summary?.total_salt_grams ?? 12.5,
      unit: "g",
      max: 30,
    },
    {
      key: "energy_kcal",
      label: "Energy",
      total: summary?.total_energy_kcal ?? 3250,
      unit: "kcal",
      max: 6000,
    },
  ];

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-6">
        <div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gunmetal tracking-tight">
            A look inside your pantry.
          </h2>
          <p className="text-base text-kioskGray mt-1.5 font-normal">
            Sample nutrient totals from recorded food stock, not what you have eaten.
          </p>
        </div>

        <span className="self-start sm:self-auto px-4 py-1.5 rounded-xl text-sm font-bold bg-limeCream/40 text-gunmetal border border-limeCream-dark/30">
          Illustrative estimates
        </span>
      </div>

      {/* Interactive Progress Bar Cards */}
      <div className="space-y-4 mb-7">
        {metrics.map((m) => {
          const percent = Math.min(100, Math.max(10, Math.round((m.total / m.max) * 100)));
          return (
            <div
              key={m.key}
              onClick={() => onSelectNutrientSort({ key: m.key, label: m.label })}
              className="bg-white border border-gray-300/80 hover:border-gunmetal rounded-2xl p-5 shadow-xs cursor-pointer transition-all active:scale-99 group"
              title={`Click to autosort dashboard by ${m.label}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold text-gunmetal tracking-tight group-hover:text-gunmetal-dark">
                    {m.label}
                  </h3>
                  <span className="text-xs text-gray-400 group-hover:text-gunmetal opacity-0 group-hover:opacity-100 transition-opacity">
                    (Tap to autosort)
                  </span>
                </div>
                <span className="text-lg font-medium text-gunmetal">
                  {Math.round(m.total)} {m.unit} · sample estimate
                </span>
              </div>

              {/* Progress Track & Fill (Lime Cream) */}
              <div className="w-full h-3.5 bg-[#EAE7E1] rounded-full overflow-hidden">
                <div
                  className="h-full bg-limeCream rounded-full transition-all duration-300"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Note Box */}
      <div className="bg-white/80 border border-gray-300 rounded-2xl p-6">
        <h4 className="font-bold text-base text-gunmetal">
          A pantry snapshot, not a health score.
        </h4>
        <p className="text-sm text-kioskGray mt-1 leading-relaxed">
          Demo figures and bar lengths are placeholders, not daily targets or clinical advice.
        </p>
      </div>
    </div>
  );
}

