from datetime import datetime, timezone
import re
from urllib.parse import quote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO


class CarrefourAdapter(BaseMarketAdapter):
    def get_chain_code(self):
        return 'CARREFOUR'

    def get_chain_name(self):
        return 'CarrefourSA'

    def search_products(self, branch_id, search_term, distance_meters=0, branch_name=''):
        url = 'https://www.carrefoursa.com/search/?text=' + quote(search_term, safe='')
        try:
            response = requests.get(url, timeout=(3, 6))
            response.raise_for_status()
        except requests.RequestException:
            return []

        now = datetime.now(timezone.utc).isoformat()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = {}
        for card in soup.select('.product-card, .product_listing_item'):
            title = card.select_one('.item-name')
            link = card.select_one('a[href*="-p-"]')
            if not title or not link:
                continue
            name = title.get_text(strip=True)
            product_url = urljoin(url, link['href'])
            sku = re.search(r'-p-(\d+)$', urlsplit(product_url).path)
            if not name or not sku or not product_url.startswith('https://www.carrefoursa.com/'):
                continue
            sku = sku.group(1)
            price_node = card.select_one('.item-price')
            price_text = price_node.get_text(' ', strip=True) if price_node else ''
            amount = re.fullmatch(r'₺?\s*((?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?)\s*(?:TL|₺)?', price_text)
            price = float(amount[1].replace('.', '').replace(',', '.')) if amount and len(amount[1]) < 15 else None
            price = price or None
            image = card.select_one('img')
            image_url = urljoin(url, image.get('src') or image.get('data-src') or '') if image else ''
            results[sku] = CanonicalProductDTO(
                market_code='CARREFOUR', market_name='CarrefourSA',
                branch_id=None, branch_name=None, distance_meters=None, barcode=None,
                product_id=f'carrefour_{sku}', product_name=name, brand='',
                category_name='', subcategory_name=None, quantity=None, unit=None,
                price=price, original_price=None, currency='TRY',
                is_in_stock=False, stock_status='UNKNOWN',
                image_url=image_url if image_url.startswith('https://') and image_url != url else None,
                last_updated=now, source='CARREFOUR_WEB_SEARCH', source_product_id=sku,
                price_status='AVAILABLE' if price is not None else 'UNAVAILABLE',
                price_scope='ONLINE', product_url=product_url, source_url=url,
            )
        return list(results.values())
