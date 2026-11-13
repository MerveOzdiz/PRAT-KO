export const priceScopeLabels = {
  BRANCH: 'Şube fiyatı',
  ONLINE: 'Online fiyat',
  CAMPAIGN: 'Kampanya fiyatı',
  CATALOG: 'Kampanya kataloğu',
};

export function isCampaign(item) {
  return item.price_scope === 'CATALOG' || item.price_scope === 'CAMPAIGN';
}

export function formatPrice(price, currency = 'TRY') {
  return currency === 'TRY' ? '₺' + price.toFixed(2) : price.toFixed(2) + ' ' + currency;
}
