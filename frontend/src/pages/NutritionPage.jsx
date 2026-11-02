import React, { useState, useMemo } from "react";
import { CheckCircleIcon, M3BarChart, FigmaNutrition } from "../components/MaterialIcons";

export default function NutritionPage({ summary, onSelectNutrientSort }) {
  const [viewMode, setViewMode] = useState("bars"); // "bars" | "pie"
  const [hoveredSlice, setHoveredSlice] = useState(null);

  // Nutrient metrics in strict European order
  const metrics = [
    {
      key: "protein_grams",
      label: "Protein",
      total: summary?.total_protein_grams ?? 180,
      unit: "g",
      max: 1000,
      color: "#85BB2F",
    },
    {
      key: "carbohydrate_grams",
      label: "Carbohydrates",
      total: summary?.total_carbohydrate_grams ?? 620,
      unit: "g",
      max: 2000,
      color: "#383D3B",
    },
    {
      key: "sugar_grams",
      label: "Sugar",
      total: summary?.total_sugar_grams ?? 95,
      unit: "g",
      max: 500,
      color: "#E09F3E",
    },
    {
      key: "fat_grams",
      label: "Fat",
      total: summary?.total_fat_grams ?? 125,
      unit: "g",
      max: 1500,
      color: "#CD7A7A",
    },
    {
      key: "saturated_fat_grams",
      label: "Saturated Fat",
      total: summary?.total_saturated_fat_grams ?? 38,
      unit: "g",
      max: 500,
      color: "#9E2A2B",
    },
    {
      key: "fiber_grams",
      label: "Fiber",
      total: summary?.total_fiber_grams ?? 65,
      unit: "g",
      max: 400,
      color: "#7C8B68",
    },
    {
      key: "salt_grams",
      label: "Salt",
      total: summary?.total_salt_grams ?? 12.5,
      unit: "g",
      max: 150,
      color: "#999999",
    },
    {
      key: "energy_kcal",
      label: "Energy",
      total: summary?.total_energy_kcal ?? 3250,
      unit: "kcal",
      max: 25000,
      color: "#6B7280",
    },
  ];

  // Nutri-Score grades configuration
  const nutriscoreGrades = [
    { grade: "A", color: "#038141", label: "Best" },
    { grade: "B", color: "#85BB2F", label: "Good" },
    { grade: "C", color: "#FECB02", textColor: "#383D3B", label: "Moderate" },
    { grade: "D", color: "#EE8100", label: "Low" },
    { grade: "E", color: "#E63E11", label: "Lowest" },
  ];

  const avgNutriscore = summary?.average_nutriscore || "B";
  const avgNutriNumeric = summary?.average_nutriscore_numeric || 2.1;
  const nutriCounts = summary?.nutriscore_counts || { A: 53, B: 7, C: 13, D: 18, E: 5 };
  const totalVeg = summary?.total_vegetarian_items ?? 89;
  const totalVegan = summary?.total_vegan_items ?? 59;

  // Macro pie slices calculation (excluding Energy and Salt which are non-weight/micro)
  const macroSlices = useMemo(() => {
    const macroKeys = [
      { key: "protein_grams", label: "Protein", color: "#85BB2F" },
      { key: "carbohydrate_grams", label: "Carbohydrates", color: "#383D3B" },
      { key: "sugar_grams", label: "Sugar", color: "#E09F3E" },
      { key: "fat_grams", label: "Fat", color: "#CD7A7A" },
      { key: "saturated_fat_grams", label: "Saturated Fat", color: "#9E2A2B" },
      { key: "fiber_grams", label: "Fiber", color: "#7C8B68" },
    ];

    const data = macroKeys.map((k) => ({
      ...k,
      grams: Math.max(1, Math.round(summary?.[`total_${k.key}`] || 0)),
    }));

    const totalGrams = data.reduce((sum, item) => sum + item.grams, 0) || 1;

    let cumulativePercent = 0;
    return data.map((item) => {
      const percentage = (item.grams / totalGrams) * 100;
      const startPercent = cumulativePercent;
      cumulativePercent += percentage;
      return {
        ...item,
        percentage: Math.round(percentage),
        startPercent,
        endPercent: cumulativePercent,
      };
    });
  }, [summary]);

  const totalMacroGrams = useMemo(() => {
    return macroSlices.reduce((acc, s) => acc + s.grams, 0);
  }, [macroSlices]);

  // Helper to calculate SVG donut arc path coordinates
  const getCoordinatesForPercent = (percent, radius, cx = 150, cy = 150) => {
    const angle = (percent / 100) * 2 * Math.PI - Math.PI / 2;
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  };

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 pb-20 select-none">
      {/* Top Header: Title & View Mode Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gunmetal tracking-tight">
            A look inside your pantry.
          </h2>
          <p className="text-base text-kioskGray mt-1.5 font-normal">
            Sample nutrient totals and diet balance from recorded food stock.
          </p>
        </div>

        {/* View Switcher Toggle Button (Bars vs Pie Chart - +15% scaled) */}
        <div className="flex items-center p-1.5 bg-white border border-gray-300 rounded-2xl shadow-xs shrink-0 self-start sm:self-auto">
          <button
            onClick={() => setViewMode("bars")}
            className={`h-[51px] px-5 rounded-xl font-bold text-base flex items-center gap-2.5 transition-all active:scale-95 cursor-pointer ${
              viewMode === "bars"
                ? "bg-gunmetal text-white shadow-xs"
                : "text-gunmetal hover:bg-gray-100"
            }`}
          >
            <M3BarChart className="w-5 h-5 fill-current" />
            <span>Nutrition Bars</span>
          </button>
          <button
            onClick={() => setViewMode("pie")}
            className={`h-[51px] px-5 rounded-xl font-bold text-base flex items-center gap-2.5 transition-all active:scale-95 cursor-pointer ${
              viewMode === "pie"
                ? "bg-gunmetal text-white shadow-xs"
                : "text-gunmetal hover:bg-gray-100"
            }`}
          >
            <FigmaNutrition className="w-5 h-5 stroke-current" />
            <span>Macro Pie Chart</span>
          </button>
        </div>
      </div>

      {/* ─── Nutri-Score & Dietary Overview Card ─── */}
      <div className="bg-white border border-gray-300/80 rounded-3xl p-6 sm:p-7 mb-7 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left: European Nutri-Score Indicator */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-extrabold text-kioskGray uppercase tracking-wider">
                Pantry Average Nutri-Score
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-limeCream/40 text-gunmetal border border-limeCream-dark/30">
                Score {avgNutriNumeric} / 5
              </span>
            </div>

            {/* Nutri-Score 5-letter grade blocks */}
            <div className="flex items-center gap-2 mt-3">
              {nutriscoreGrades.map((n) => {
                const isCurrent = n.grade === avgNutriscore;
                return (
                  <div
                    key={n.grade}
                    className={`relative flex flex-col items-center justify-center rounded-xl transition-all ${
                      isCurrent
                        ? "w-16 sm:w-20 h-16 sm:h-20 scale-105 shadow-md ring-4 ring-gunmetal/20 z-10"
                        : "w-12 sm:w-14 h-12 sm:h-14 opacity-75 hover:opacity-100"
                    }`}
                    style={{ backgroundColor: n.color }}
                  >
                    <span
                      className={`font-black text-2xl sm:text-3xl leading-none ${
                        n.textColor || "text-white"
                      }`}
                    >
                      {n.grade}
                    </span>
                    {isCurrent && (
                      <span className="absolute -bottom-2 bg-gunmetal text-white text-[10px] font-black uppercase px-1.5 py-0.5 rounded-full shadow-xs">
                        Avg
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Grade counts summary */}
            <p className="text-xs text-kioskGray mt-4">
              Stock breakdown: <strong className="text-gunmetal">{nutriCounts.A}</strong> Grade A ·{" "}
              <strong className="text-gunmetal">{nutriCounts.B}</strong> Grade B ·{" "}
              <strong className="text-gunmetal">{nutriCounts.C}</strong> Grade C ·{" "}
              <strong className="text-gunmetal">{nutriCounts.D}</strong> Grade D ·{" "}
              <strong className="text-gunmetal">{nutriCounts.E}</strong> Grade E
            </p>
          </div>

          {/* Right: Vegetarian & Vegan Counters (Mutually exclusive - no double counting) */}
          <div className="lg:border-l lg:border-gray-200 lg:pl-8 flex flex-col gap-3 shrink-0">
            <div className="flex flex-row lg:flex-col gap-3">
              <div className="p-3.5 sm:p-4 rounded-2xl bg-emerald-50 border border-emerald-200/80 flex flex-col justify-center flex-1 sm:w-64">
                <span className="text-2xl font-black text-emerald-950 block leading-tight">
                  {totalVegan}
                </span>
                <span className="text-xs font-bold text-emerald-800">
                  Vegan (100% plant-based)
                </span>
              </div>

              <div className="p-3.5 sm:p-4 rounded-2xl bg-green-50 border border-green-200/80 flex flex-col justify-center flex-1 sm:w-64">
                <span className="text-2xl font-black text-green-950 block leading-tight">
                  {totalVeg}
                </span>
                <span className="text-xs font-bold text-green-800">
                  Vegetarian (dairy & eggs)
                </span>
              </div>
            </div>

            <p className="text-[11px] text-kioskGray font-medium text-center lg:text-left flex items-center gap-1.5 justify-center lg:justify-start">
              <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Mutually exclusive · No double counting ({totalVegan + totalVeg} total meat-free)</span>
            </p>
          </div>
        </div>
      </div>

      {/* ─── Mode A: Progress Bars View ─── */}
      {viewMode === "bars" && (
        <div className="space-y-4 mb-7">
          {metrics.map((m) => {
            const percent = Math.min(100, Math.max(8, Math.round((m.total / m.max) * 100)));
            return (
              <div
                key={m.key}
                onClick={() => onSelectNutrientSort({ key: m.key, label: m.label })}
                className="bg-white border border-gray-300/80 hover:border-gunmetal rounded-2xl p-5 shadow-xs cursor-pointer transition-all active:scale-99 group"
                title={`Click to autosort dashboard by ${m.label}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className="w-4 h-4 rounded-full shrink-0 shadow-2xs"
                      style={{ backgroundColor: m.color }}
                    />
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

                {/* Progress Track & Fill with matching pie chart color */}
                <div className="w-full h-3.5 bg-[#EAE7E1] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300 shadow-2xs"
                    style={{
                      width: `${percent}%`,
                      backgroundColor: m.color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ─── Mode B: Interactive Macro Pie / Donut Chart View ─── */}
      {viewMode === "pie" && (
        <div className="bg-white border border-gray-300/80 rounded-3xl p-6 sm:p-8 mb-7 shadow-xs">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
            {/* SVG Donut / Pie Chart */}
            <div className="relative w-[300px] h-[300px] sm:w-[340px] sm:h-[340px] shrink-0 flex items-center justify-center">
              <svg viewBox="0 0 300 300" className="w-full h-full -rotate-90">
                {macroSlices.map((slice) => {
                  const cx = 150;
                  const cy = 150;
                  const outerR = 135;
                  const innerR = 75;

                  const startAngle = (slice.startPercent / 100) * 2 * Math.PI;
                  const endAngle = (slice.endPercent / 100) * 2 * Math.PI;

                  // Outer coordinates
                  const x1 = cx + outerR * Math.cos(startAngle);
                  const y1 = cy + outerR * Math.sin(startAngle);
                  const x2 = cx + outerR * Math.cos(endAngle);
                  const y2 = cy + outerR * Math.sin(endAngle);

                  // Inner coordinates
                  const x3 = cx + innerR * Math.cos(endAngle);
                  const y3 = cy + innerR * Math.sin(endAngle);
                  const x4 = cx + innerR * Math.cos(startAngle);
                  const y4 = cy + innerR * Math.sin(startAngle);

                  const largeArc = slice.percentage > 50 ? 1 : 0;
                  const d = `M ${x1} ${y1} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerR} ${innerR} 0 ${largeArc} 0 ${x4} ${y4} Z`;

                  const isHovered = hoveredSlice === slice.key;

                  return (
                    <path
                      key={slice.key}
                      d={d}
                      fill={slice.color}
                      className="cursor-pointer transition-all duration-200 hover:opacity-85"
                      style={{
                        transformOrigin: "150px 150px",
                        transform: isHovered ? "scale(1.04)" : "scale(1)",
                      }}
                      onMouseEnter={() => setHoveredSlice(slice.key)}
                      onMouseLeave={() => setHoveredSlice(null)}
                      onClick={() => onSelectNutrientSort({ key: slice.key, label: slice.label })}
                    />
                  );
                })}
              </svg>

              {/* Center Donut Label */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                <span className="text-xs uppercase font-extrabold text-kioskGray tracking-wider">
                  Total Macros
                </span>
                <span className="text-3xl font-extrabold text-gunmetal mt-0.5">
                  {totalMacroGrams}g
                </span>
                <span className="text-[11px] text-gray-400 mt-0.5 font-medium">
                  Tap slice to autosort
                </span>
              </div>
            </div>

            {/* Interactive Legend & Details */}
            <div className="flex-1 w-full space-y-3">
              <h4 className="text-base font-extrabold text-gunmetal tracking-tight mb-2">
                Pantry Macro Proportion
              </h4>
              <p className="text-xs text-kioskGray mb-4">
                Relative weight of primary nutrients in your active kitchen inventory.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {macroSlices.map((slice) => {
                  const isHovered = hoveredSlice === slice.key;
                  return (
                    <div
                      key={slice.key}
                      onMouseEnter={() => setHoveredSlice(slice.key)}
                      onMouseLeave={() => setHoveredSlice(null)}
                      onClick={() => onSelectNutrientSort({ key: slice.key, label: slice.label })}
                      className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between active:scale-98 ${
                        isHovered
                          ? "bg-parchment border-gunmetal shadow-xs"
                          : "bg-white border-gray-200 hover:border-gray-400"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className="w-4 h-4 rounded-full shrink-0 shadow-2xs"
                          style={{ backgroundColor: slice.color }}
                        />
                        <div>
                          <span className="font-bold text-sm text-gunmetal block leading-tight">
                            {slice.label}
                          </span>
                          <span className="text-xs text-kioskGray">
                            {slice.grams} g
                          </span>
                        </div>
                      </div>

                      <span className="text-base font-extrabold text-gunmetal">
                        {slice.percentage}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Note Box */}
      <div className="bg-white/80 border border-gray-300 rounded-2xl p-6">
        <h4 className="font-bold text-base text-gunmetal">
          A pantry snapshot, not a health score.
        </h4>
        <p className="text-sm text-kioskGray mt-1 leading-relaxed">
          Demo figures, bars, and pie slices represent recorded inventory stock, not daily personal targets or clinical advice.
        </p>
      </div>
    </div>
  );
}
