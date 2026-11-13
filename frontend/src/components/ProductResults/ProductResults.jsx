import React, { useState } from 'react';
import ProductCard from '../ProductCard/ProductCard';
import { isCampaign } from '../../services/pricePresentation';

function hasVerifiedPrice(item) {
  return item.price_status === 'AVAILABLE' && Number.isFinite(item.price) && item.price > 0 && !item.is_mock;
}

function OfferSection({ id, title, description, items, onOpenDetail, allowCheapest = false }) {
  if (!items.length) return null;
  return (
    <section aria-labelledby={id} className="space-y-4 rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4">
      <div>
        <h3 id={id} className="font-bold text-slate-800">{title}</h3>
        {description && <p className="mt-1 text-xs text-slate-600">{description}</p>}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <ProductCard key={item.product_id} item={item}
            isCheapest={allowCheapest && item.is_cheapest} onOpenDetail={onOpenDetail} />
        ))}
      </div>
    </section>
  );
}

function ProductResults({ query, results, loading, error, onClearSearch, onOpenDetail, sortBy = 'price', onSort }) {
  const [onlyInStock, setOnlyInStock] = useState(false);

  const verified = results.filter((item) => hasVerifiedPrice(item) && !isCampaign(item));
  const offers = onlyInStock ? verified.filter((item) => item.is_in_stock) : verified;
  const branches = new Set(offers.map((item) => item.branch_id).filter(Boolean));
  const campaigns = results.filter((item) => hasVerifiedPrice(item) && isCampaign(item));
  const withoutPrice = onlyInStock ? [] : results.filter((item) => !hasVerifiedPrice(item) && item.source !== 'UNAVAILABLE');
  const unconfirmedBranches = onlyInStock ? [] : results.filter((item) => item.source === 'UNAVAILABLE');

  if (loading) {
    return (
      <section role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
        <p className="text-sm font-semibold text-slate-600">Yakındaki marketlerde "{query}" aranıyor...</p>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-extrabold text-slate-800">Arama ve karşılaştırma sonuçları</h2>
          <p className="mt-1 text-xs text-slate-600">
            Bu sayfada <strong className="text-emerald-700">{offers.length} doğrulanmış fiyat kaydı</strong>
            {' · '}{branches.size} şube{' · '}{campaigns.length} kampanya kaydı
          </p>
        </div>
        <button type="button" onClick={onClearSearch}
          className="self-start rounded-full bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 sm:self-auto">
          Aramayı temizle
        </button>
      </div>

      {results.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3">
          <div role="group" aria-label="Sonuç sıralaması" className="flex flex-wrap gap-2">
            {[['price', 'Fiyata göre'], ['distance', 'En yakın']].map(([value, label]) => (
              <button key={value} type="button" aria-pressed={sortBy === value} onClick={() => onSort(value)}
                className={`rounded-full px-4 py-2 text-xs font-semibold ${sortBy === value ? 'bg-emerald-700 text-white' : 'bg-slate-100 text-slate-700'}`}>
                {label}
              </button>
            ))}
          </div>
          {verified.length > 0 && (
            <label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
              <input type="checkbox" checked={onlyInStock} onChange={(e) => setOnlyInStock(e.target.checked)} />
              Sadece Stokta Olanlar
            </label>
          )}
        </div>
      )}

      <OfferSection id="verified-heading" title="Doğrulanmış fiyatlar"
        items={offers} onOpenDetail={onOpenDetail} allowCheapest={!onlyInStock} />
      <OfferSection id="campaign-heading" title="Kampanya katalogları"
        description="Kampanya fiyatları fiyat karşılaştırmasına dahil edilmez."
        items={campaigns} onOpenDetail={onOpenDetail} />
      <OfferSection id="unpriced-heading" title="Fiyatı doğrulanamayan ürünler"
        description="Bu ürünler fiyat karşılaştırmasına dahil edilmez."
        items={withoutPrice} onOpenDetail={onOpenDetail} />

      {unconfirmedBranches.length > 0 && (
        <section aria-labelledby="unconfirmed-heading" className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 id="unconfirmed-heading" className="font-bold text-slate-800">Ürün bilgisi doğrulanamayan şubeler</h3>
          <p className="mt-1 text-xs text-slate-600">Bu şubelerde aradığınız ürünün bulunup bulunmadığı bilinmiyor.</p>
          <ul className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
            {unconfirmedBranches.map((item) => (
              <li key={item.product_id} className="rounded-lg bg-slate-50 px-3 py-2">
                {item.branch_name}
                {item.distance_meters != null && <span className="text-slate-500"> · {Math.round(item.distance_meters)} m</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(!offers.length && !campaigns.length && !withoutPrice.length) && (
        <p className="rounded-2xl border border-slate-200 bg-white p-6 text-center text-sm font-medium text-slate-600">
          {error || (onlyInStock ? 'Stokta olduğu doğrulanmış ürün bulunamadı.' : 'Aradığınız kriterlere uygun sonuç bulunamadı.')}
        </p>
      )}
    </div>
  );
}

export default ProductResults;
