import React from 'react';
import MarketCard from '../MarketCard/MarketCard';

function MarketGrid({ markets, loading, error }) {
  if (loading) {
    return (
      <main className="flex-grow bg-white rounded-2xl border border-slate-200/80 p-8 text-center shadow-sm">
        <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm font-semibold text-slate-600">Yakındaki marketler yükleniyor...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex-grow bg-white rounded-2xl border border-rose-200 p-8 text-center shadow-sm">
        <p className="text-sm font-semibold text-rose-600">{error}</p>
      </main>
    );
  }

  return (
    <main className="flex-grow space-y-4">
      <p className="text-xs text-slate-600" role="note">
        Google Maps sonuçları 3 km içindeki bütün marketleri içermeyebilir.
      </p>
      {markets.length === 0 ? (
        <div className="bg-white rounded-2xl p-10 border border-slate-200/80 text-center shadow-sm">
          <p className="text-slate-500 font-medium text-sm">Belirtilen mesafede market bulunamadı.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market) => (
            <MarketCard key={market.id} market={market} />
          ))}
        </div>
      )}
    </main>
  );
}

export default MarketGrid;
