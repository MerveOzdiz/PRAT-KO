from datetime import datetime, timezone
from math import isfinite
from urllib.parse import quote

import requests

from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO


def lira(value):
    if type(value) in (int, float) and 0 < value < 10**12 and isfinite(value):
        return round(value / 100, 2)
    return None


class MigrosAdapter(BaseMarketAdapter):
    def get_chain_code(self):
        return 'MIGROS'

    def get_chain_name(self):
        return 'Migros Sanal Market'

    def search_products(self, branch_id, search_term, distance_meters=0, branch_name=''):
        base = 'https://www.migros.com.tr'
        url = f'{base}/rest/products/search?q={quote(search_term, safe="")}'
        try:
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=(3, 5))
            response.raise_for_status()
            payload = response.json()
            data = payload.get('data') if isinstance(payload, dict) else None
        except (requests.RequestException, ValueError):
            return []

        products = data.get('storeProductInfos') if isinstance(data, dict) else None
        if not isinstance(products, list):
            return []
        now = datetime.now(timezone.utc).isoformat()
        results = {}
        for row in products:
            if not isinstance(row, dict) or not isinstance(row.get('name'), str):
                continue
            name = row['name'].strip()
            sku = row.get('sku') or row.get('id')
            if not name or not isinstance(sku, (str, int)) or not sku:
                continue
            brand, category = row.get('brand'), row.get('category')
            price, regular = lira(row.get('shownPrice')), lira(row.get('regularPrice'))
            in_stock = row.get('status') == 'IN_SALE'
            images = row.get('images')
            urls = images[0].get('urls') if isinstance(images, list) and images and isinstance(images[0], dict) else None
            image = urls.get('PRODUCT_HD') or urls.get('PRODUCT_DETAIL') or urls.get('PRODUCT_LIST') if isinstance(urls, dict) else None
            path = row.get('prettyName')
            results[str(sku)] = CanonicalProductDTO(
                market_code='MIGROS', market_name='M Migros',
                branch_id=None, branch_name=None, distance_meters=None,
                barcode=str(row['barcode']) if isinstance(row.get('barcode'), (str, int)) else None,
                product_id=f'migros_{sku}', product_name=name,
                brand=brand.get('name') or '' if isinstance(brand, dict) else '',
                category_name=category.get('name') or '' if isinstance(category, dict) else '',
                subcategory_name=category.get('parentName') if isinstance(category, dict) else None,
                quantity=None, unit=None, price=price,
                original_price=regular if regular and price and regular > price else None,
                currency='TRY', is_in_stock=in_stock,
                stock_status='IN_STOCK' if in_stock else 'UNKNOWN',
                image_url=image if isinstance(image, str) and image.startswith('https://') else None,
                last_updated=now, source='MIGROS_LIVE_REST_API', source_product_id=str(sku),
                price_status='AVAILABLE' if price is not None else 'UNAVAILABLE',
                price_scope='ONLINE', source_url=url,
                product_url=f'{base}/{quote(path, safe="")}' if isinstance(path, str) and path else None,
            )
        return list(results.values())
