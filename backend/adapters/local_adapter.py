import datetime
from typing import List
from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO

class LocalMarketAdapter(BaseMarketAdapter):
    def get_chain_code(self) -> str:
        return 'LOCAL'

    def get_chain_name(self) -> str:
        return 'Yerel Market & Bakkal'

    def search_products(self, branch_id: str, search_term: str, distance_meters: float = 0.0, branch_name: str = "") -> List[CanonicalProductDTO]:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        b_name = branch_name if branch_name else "Yerel Market"
        q = search_term.strip() if search_term else "Ürün"
        store_display_name = b_name.split('(')[0].strip() if '(' in b_name else b_name

        return [
            CanonicalProductDTO(
                market_code='LOCAL',
                market_name=store_display_name,
                branch_id=branch_id,
                branch_name=b_name,
                distance_meters=distance_meters,
                barcode=None,
                product_id=f'local_unavail_{branch_id}',
                product_name=f"{q} · Ürün bilgisi doğrulanamadı",
                brand=store_display_name,
                category_name='Genel Gıda',
                subcategory_name=None,
                quantity=None,
                unit=None,
                price=None,
                original_price=None,
                currency='TRY',
                is_in_stock=False,
                stock_status='UNKNOWN',
                image_url=None,
                last_updated=now_str,
                is_mock=False,
                source='UNAVAILABLE',
                source_product_id=None,
                price_status='UNAVAILABLE'
            )
        ]
