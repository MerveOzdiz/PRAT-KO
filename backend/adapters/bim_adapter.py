from datetime import datetime, timezone
import re
from threading import Lock
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO
from services.cache_service import SimpleTTLCache
from services.product_comparison import normalize


catalog_cache = SimpleTTLCache()
catalog_lock = Lock()
SOURCE = 'https://www.bim.com.tr/'


class BimAdapter(BaseMarketAdapter):
    def get_chain_code(self):
        return 'BIM'

    def get_chain_name(self):
        return 'BİM'

    def search_products(self, branch_id, search_term, distance_meters=0, branch_name=''):
        with catalog_lock:
            catalog = catalog_cache.get(SOURCE)
            if catalog is None:
                try:
                    response = requests.get(SOURCE, timeout=(3, 6))
                    response.raise_for_status()
                    catalog = self.parse_catalog(response.text)
                except requests.RequestException:
                    catalog = []
                catalog_cache.set(SOURCE, catalog, ttl_seconds=None if catalog else 30)

        terms = set(normalize(search_term).split())
        return [item for item in catalog if terms <= set(normalize(item.product_name).split())]

    @staticmethod
    def parse_catalog(html):
        soup = BeautifulSoup(html, 'html.parser')
        tab = soup.select_one('.aktuelArea .tabArea .subButton.active')
        if not tab:
            return []
        label = tab.get_text(' ', strip=True)
        now = datetime.now(timezone.utc).isoformat()
        products = {}
        for card in soup.select('.aktuelArea .productArea .product'):
            title, brand, pack = (card.select_one(selector) for selector in (
                '.descArea .title', '.descArea .subTitle', '.gramajadet',
            ))
            link = card.select_one('.imageArea a[href^="/aktuel-urunler/"]')
            price_node = card.select_one('.priceArea .gButton')
            if not title or not link or not title.get_text(strip=True):
                continue
            price = re.fullmatch(r'(\d{1,6}(?:\.\d{3})*),\s*(\d{2})\s*₺',
                                 price_node.get_text(' ', strip=True) if price_node else '')
            amount = float(price[1].replace('.', '') + '.' + price[2]) if price else None
            amount = amount or None
            name = title.get_text(' ', strip=True)
            brand_name = brand.get_text(' ', strip=True) if brand else ''
            quantity = pack.get_text(' ', strip=True).lstrip('• ').strip() if pack else ''
            image = card.select_one('.imageArea img')
            image_url = image.get('src', '') if image else ''
            path = link['href']
            products[path] = CanonicalProductDTO(
                market_code='BIM', market_name='BİM', branch_id=None, branch_name=None,
                distance_meters=None, barcode=None, product_id=f'bim:{path}',
                product_name=' '.join(filter(None, (brand_name, name, quantity))),
                brand=brand_name, category_name='', subcategory_name=None,
                quantity=quantity or None, unit=None, price=amount, original_price=None,
                currency='TRY', is_in_stock=False, stock_status='UNKNOWN',
                image_url=image_url if image_url.startswith('https://') else None,
                last_updated=now, source='BIM_OFFICIAL_CATALOG', source_product_id=path,
                price_status='AVAILABLE' if amount else 'UNAVAILABLE', price_scope='CATALOG', source_url=SOURCE,
                product_url=urljoin(SOURCE, path), campaign_label=label,
            )
        return list(products.values())
