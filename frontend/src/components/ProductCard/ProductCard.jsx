import React from 'react';
import { formatPrice, priceScopeLabels } from '../../services/pricePresentation';

function ProductCard({ item, isCheapest, onOpenDetail }) {
  const hasRealPrice = Number.isFinite(item.price) && item.price > 0 && item.price_status === 'AVAILABLE';
  const isDiscounted = hasRealPrice && item.original_price && item.original_price > item.price;
  const distMeters = Math.round(item.distance_meters || 0);
  const distKm = distMeters / 1000.0;
  const formattedDistance = distKm < 1 ? `${distMeters} m` : `${distKm.toFixed(2)} km`;

  return (
    <div className={`relative bg-white rounded-2xl p-5 transition-all duration-300 flex flex-col justify-between hover:-translate-y-1 ${
      isCheapest && hasRealPrice
        ? 'border-2 border-emerald-500 shadow-lg shadow-emerald-500/10 ring-2 ring-emerald-500/20'
        : 'border border-slate-200/80 shadow-sm hover:shadow-md'
    }`}>
      {/* Cheapest Badge */}
      {isCheapest && hasRealPrice && (
        <div className="absolute -top-3 right-4 bg-gradient-to-r from-emerald-600 to-green-500 text-white text-[11px] font-extrabold px-3 py-1 rounded-full shadow-md tracking-wide uppercase flex items-center gap-1">
          <span>🏆</span>
          <span>EN UCUZ GERÇEK FİYAT</span>
        </div>
      )}

      <div>
        {/* Header Store info & Live/Status Badge */}
        <div className="flex items-center justify-between gap-2 mb-3 mt-1">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
            isCheapest && hasRealPrice ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
          }`}>
            <span>🏪</span>
            <span>{item.market_name}</span>
          </span>

          <div className="flex items-center gap-1.5">
            {hasRealPrice ? (
              <span className="text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {(priceScopeLabels[item.price_scope] || 'Fiyat').toLocaleUpperCase('tr-TR')}
              </span>
            ) : (
              <span className="text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200 px-2 py-0.5 rounded-full">
                VERİ YOK
              </span>
            )}
            {item.distance_meters != null && <span className="text-xs font-medium text-slate-500 bg-slate-50 px-2 py-0.5 rounded-full">
              📍 {formattedDistance}
            </span>}
          </div>
        </div>

        {/* Product Image */}
        {item.image_url ? (
          <div
            onClick={() => onOpenDetail && onOpenDetail(item)}
            className="w-full h-28 flex items-center justify-center mb-3 p-2 bg-slate-50 rounded-xl cursor-pointer hover:bg-slate-100/80 transition-colors group"
          >
            <img src={item.image_url} alt={item.product_name} className="max-h-full object-contain group-hover:scale-105 transition-transform" />
          </div>
        ) : (
          <div
            onClick={() => onOpenDetail && onOpenDetail(item)}
            className="w-full h-24 flex items-center justify-center mb-3 p-2 bg-slate-50 rounded-xl cursor-pointer text-3xl"
          >
            🏪
          </div>
        )}

        {/* Product Title & Branch */}
        <h4
          onClick={() => onOpenDetail && onOpenDetail(item)}
          className="font-bold text-slate-800 text-sm leading-snug mb-1 line-clamp-2 cursor-pointer hover:text-emerald-600 transition-colors"
        >
          {item.product_name}
        </h4>
        <p className="text-xs text-slate-400 font-medium mb-3 line-clamp-1">
          {item.source === 'MARKET_OWNER' && item.price_scope === 'ONLINE' && 'Bildirimi yapan şube · '}
          {item.campaign_label || item.branch_name}
        </p>
        {item.source === 'MARKET_OWNER' && (
          <p className="mb-3 text-xs text-slate-600">
            {item.brand} · {item.quantity} {item.unit} · Market sahibi bildirimi
          </p>
        )}
      </div>

      {/* Footer Price & Add to Cart */}
      <div className="pt-3 border-t border-slate-100 space-y-3">
        <div className="flex items-end justify-between">
          <div>
            {hasRealPrice ? (
              <>
                {isDiscounted && (
                  <span className="block text-xs text-slate-400 line-through font-medium">
                    {formatPrice(item.original_price, item.currency)}
                  </span>
                )}
                <span className={`text-xl font-extrabold tracking-tight ${
                  isCheapest ? 'text-emerald-600' : 'text-slate-900'
                }`}>
                  {formatPrice(item.price, item.currency)}
                </span>
              </>
            ) : (
              <span className="text-xs font-semibold text-slate-400 italic block py-1">
                Fiyat bilgisi mevcut değil
              </span>
            )}
          </div>

          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
            hasRealPrice && item.is_in_stock
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-slate-100 text-slate-500'
          }`}>
            {item.stock_status === 'OUT_OF_STOCK' ? 'Stokta yok' : item.is_in_stock ? '✓ Stokta' : 'Stok bilgisi yok'}
          </span>
        </div>

        {item.product_url && (
          <a href={item.product_url} target="_blank" rel="noreferrer"
            className="block w-full py-2 bg-slate-900 hover:bg-emerald-600 text-white font-semibold text-xs rounded-xl text-center">
            Kaynağı aç
          </a>
        )}
      </div>
    </div>
  );
}

export default ProductCard;
