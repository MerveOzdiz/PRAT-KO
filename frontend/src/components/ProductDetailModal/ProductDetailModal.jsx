import React from 'react';
import { formatPrice, priceScopeLabels } from '../../services/pricePresentation';

function ProductDetailModal({ item, isOpen, onClose }) {
  if (!isOpen || !item) return null;

  const hasRealPrice = Number.isFinite(item.price) && item.price > 0 && item.price_status === 'AVAILABLE';
  const isDiscounted = hasRealPrice && item.original_price && item.original_price > item.price;
  const distMeters = Math.round(item.distance_meters || 0);
  const distKm = distMeters / 1000.0;
  const formattedDistance = distKm < 1 ? `${distMeters} m` : `${distKm.toFixed(2)} km`;

  const sourceLabel = item.source === 'MARKET_OWNER'
    ? 'Market sahibi bildirimi'
    : item.source === 'MIGROS_LIVE_REST_API'
    ? 'Migros Live REST API'
    : item.source === 'CARREFOUR_WEB_SEARCH'
    ? 'CarrefourSA Web Arama'
    : hasRealPrice
    ? (item.source || 'Canlı Veri')
    : 'Resmi Canlı Veri Bulunamadı';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl overflow-hidden border border-slate-200/80 animate-in zoom-in-95 duration-200">

        {/* Header */}
        <div className="p-5 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="bg-emerald-500 text-white font-extrabold text-xs px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              Ürün Detayı & Mağaza Bilgisi
            </span>
            <span className="text-xs text-slate-300 font-medium">
              ID: #{item.product_id}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center font-bold text-sm transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Image & Main Info */}
          <div className="flex flex-col sm:flex-row gap-5 items-center">
            {item.image_url ? (
              <div className="w-32 h-32 flex-shrink-0 bg-slate-50 rounded-2xl p-3 border border-slate-100 flex items-center justify-center">
                <img src={item.image_url} alt={item.product_name} className="max-h-full max-w-full object-contain" />
              </div>
            ) : (
              <div className="w-32 h-32 flex-shrink-0 bg-slate-100 rounded-2xl flex items-center justify-center text-4xl">
                🏪
              </div>
            )}

            <div className="space-y-2 flex-grow text-center sm:text-left">
              <h3 className="font-extrabold text-slate-900 text-lg leading-tight">
                {item.product_name}
              </h3>
              {item.source === 'MARKET_OWNER' && (
                <p className="text-xs text-slate-600">{item.brand} · {item.quantity} {item.unit}</p>
              )}

              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-800 text-xs font-bold px-3 py-1 rounded-full border border-slate-200">
                  <span>🏪</span>
                  <span>{item.market_name}</span>
                </span>
                {item.distance_meters != null && <span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2.5 py-1 rounded-full">
                  📍 {formattedDistance} Uzaklıkta
                </span>}
              </div>
            </div>
          </div>

          {/* Detailed Specifications Grid */}
          <div className="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-2xl border border-slate-200/60 text-xs">
            <div>
              <span className="block text-slate-400 font-semibold mb-0.5">
                {item.source === 'MARKET_OWNER' && item.price_scope === 'ONLINE' ? 'Bildirimi yapan şube' : 'Şube Adı'}
              </span>
              <span className="font-bold text-slate-800 line-clamp-1">{item.branch_name || '—'}</span>
            </div>
            <div>
              <span className="block text-slate-400 font-semibold mb-0.5">Stok Durumu</span>
              <span className={`font-bold ${hasRealPrice && item.is_in_stock ? 'text-emerald-600' : 'text-slate-500'}`}>
                {hasRealPrice && item.is_in_stock ? '✓ Stokta Var' : '✕ Bilgi Yok'}
              </span>
            </div>
            <div>
              <span className="block text-slate-400 font-semibold mb-0.5">Veri Kaynağı</span>
              <span className={`font-bold ${hasRealPrice ? 'text-emerald-600' : 'text-slate-500'}`}>
                {sourceLabel}
              </span>
            </div>
            <div>
              <span className="block text-slate-400 font-semibold mb-0.5">Fiyat Durumu</span>
              <span className={`font-bold ${hasRealPrice ? 'text-emerald-600' : 'text-rose-600'}`}>
                {item.source === 'MARKET_OWNER' ? 'Yönetici onaylı' : hasRealPrice ? '✓ Doğrulanmış Fiyat' : '✕ Fiyat Mevcut Değil'}
              </span>
            </div>
          </div>

          {hasRealPrice && (
            <p className="text-xs text-slate-500">
              {item.campaign_label && <span>Katalog etiketi · {item.campaign_label} · </span>}
              {item.valid_until && <span>Son geçerlilik tarihi {item.valid_until} · </span>}
              Kaynaktan alınma zamanı · <time dateTime={item.last_updated}>{new Date(item.last_updated).toLocaleString('tr-TR')}</time>
            </p>
          )}

          {/* Pricing Highlight */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
            <div>
              <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                {priceScopeLabels[item.price_scope] || 'Fiyat'}
              </span>
              {hasRealPrice ? (
                <>
                  {isDiscounted && (
                    <span className="text-xs text-slate-400 line-through font-medium mr-2">
                      {formatPrice(item.original_price, item.currency)}
                    </span>
                  )}
                  <span className="text-3xl font-black text-emerald-700 tracking-tight">
                    {formatPrice(item.price, item.currency)}
                  </span>
                </>
              ) : (
                <span className="text-sm font-bold text-slate-500 italic">
                  Fiyat bilgisi mevcut değil
                </span>
              )}
            </div>

            {item.product_url && (
              <a href={item.product_url} target="_blank" rel="noreferrer"
                className="px-5 py-3 bg-emerald-600 text-white font-bold text-xs rounded-xl">
                Kaynağı aç
              </a>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

export default ProductDetailModal;
