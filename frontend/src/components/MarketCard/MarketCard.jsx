import React from 'react';

function MarketCard({ market }) {
  const distKm = market.distance_km || 0;
  const formattedDistance = distKm < 1
    ? `${Math.round(distKm * 1000)} m`
    : `${distKm.toFixed(2)} km`;

  return (
    <div className="group bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-xl hover:border-emerald-300 transition-all duration-300 flex flex-col justify-between hover:-translate-y-1">
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span>🏪</span>
            <span>{market.name}</span>
          </span>
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full">
            📍 {formattedDistance}
          </span>
        </div>

        <p className="text-xs text-slate-600 font-medium line-clamp-2 mb-4 leading-relaxed">
          {market.address || 'Mağaza adresi mevcut değil.'}
        </p>
      </div>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-slate-400 font-medium">Kuş uçuşu mesafe</span>
        {market.google_place_id && (
          <a href={'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(market.name)
            + '&query_place_id=' + encodeURIComponent(market.google_place_id)}
            target="_blank" rel="noreferrer" className="font-bold text-emerald-600">
            Haritada aç →
          </a>
        )}
      </div>
    </div>
  );
}

export default MarketCard;
