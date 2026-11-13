import React from 'react';

const DISTANCE_OPTIONS = [0.5, 1, 1.5, 2, 3];

function DistanceFilter({ selectedDistance, onSelectDistance }) {
  return (
    <aside className="w-full md:w-64 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 flex-shrink-0 h-fit">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <span className="text-emerald-600 font-bold">⚙️</span>
        <h3 className="font-bold text-slate-800 text-base tracking-tight">Filtreler</h3>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
          Maksimum Uzaklık
        </label>
        <div className="grid grid-cols-2 gap-1.5 md:grid-cols-1">
          {DISTANCE_OPTIONS.map((dist) => {
            const isActive = selectedDistance === dist;
            return (
              <button
                type="button"
                aria-pressed={isActive}
                key={dist}
                onClick={() => onSelectDistance(dist)}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer transition-all border ${
                  isActive
                    ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-semibold shadow-sm'
                    : 'bg-slate-50/60 border-slate-200/60 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                    isActive ? 'border-emerald-600 bg-emerald-600' : 'border-slate-300 bg-white'
                  }`}>
                    {isActive && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </div>
                  <span className="text-xs">{dist < 1 ? `${dist * 1000} Metre` : `${dist} Kilometre`}</span>
                </div>
                {isActive && <span aria-hidden="true" className="text-xs text-emerald-600 font-bold">✓</span>}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

export default DistanceFilter;
