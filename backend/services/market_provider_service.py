import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from adapters.registry import AdapterRegistry
from services.product_comparison import mark_cheapest
from services.catalog_categories import matches_category
from utils.market_filter import tr_lower


def chain_code(name):
    name = tr_lower(name)
    for pattern, code in (
        (r'\bmigros\b', 'MIGROS'), (r'\bcarrefour(?:sa)?\b', 'CARREFOUR'),
        (r'\b[şs]ok\b', 'SOK'), (r'\ba101\b', 'A101'),
        (r'\bbim\b', 'BIM'), (r'\bfile\b', 'FILE'),
    ):
        if re.search(pattern, name):
            return code
    return 'LOCAL'


class MarketProviderService:
    @staticmethod
    def search_all_providers(search_term, nearby_branches, category_filter=None, page=1, page_size=50, owner_prices=(), sort_by='price'):
        catalog_query = search_term
        owner_branch_ids = {offer['branch_id'] for offer in owner_prices}
        branches_by_code = {}
        for branch in sorted(nearby_branches, key=lambda item: item['distance_km']):
            code = chain_code(branch['name'])
            branches_by_code.setdefault(code, {}).setdefault(
                branch.get('google_place_id') or branch['id'], branch
            )

        def search_chain(entry):
            code, branches = entry
            adapter = AdapterRegistry.get(code)
            if code == 'BIM':
                offers = adapter.search_products(None, search_term)
                if category_filter:
                    offers = [item for item in offers if matches_category(item.to_dict(), category_filter)]
                if offers:
                    return offers
            if category_filter:
                return []
            return [
                replace(item, market_code=code)
                for branch in branches.values()
                if (branch.get('google_place_id') or branch['id']) not in owner_branch_ids
                for item in AdapterRegistry.get('LOCAL').search_products(
                    branch['id'], catalog_query, branch['distance_km'] * 1000, branch['name']
                )
            ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            batches = executor.map(search_chain, branches_by_code.items())
            products = [item.to_dict() for batch in batches for item in batch]
        products.extend(owner_prices)
        mark_cheapest(products)
        def sort_key(item):
            verified = item['price_status'] == 'AVAILABLE' and item['price'] is not None
            group = (1 if item['price_scope'] in ('CATALOG', 'CAMPAIGN') else 0) if verified else 2
            distance = item['distance_meters'] if item['distance_meters'] is not None else float('inf')
            if sort_by == 'distance' or not verified:
                return group, distance
            return group, item['currency'], item['price_scope'] or '', item['price']

        products.sort(key=sort_key)
        total = len(products)
        return {
            'results': products[(page - 1) * page_size:page * page_size],
            'total': total, 'page': page, 'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }
