import datetime
from typing import List
from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO

class A101Adapter(BaseMarketAdapter):
    def get_chain_code(self) -> str:
        return 'A101'

    def get_chain_name(self) -> str:
        return 'A101 Kapıda'

    def search_products(self, branch_id: str, search_term: str, distance_meters: float = 0.0, branch_name: str = "") -> List[CanonicalProductDTO]:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        b_name = branch_name if branch_name else "A101 Şubesi"
        q = search_term.strip() if search_term else "Ürün"

        return [
            CanonicalProductDTO(
                market_code='A101',
                market_name='A101',
                branch_id=branch_id,
                branch_name=b_name,
                distance_meters=distance_meters,
                barcode=None,
                product_id=f'a101_unavail_{branch_id}',
                product_name=f"{q.capitalize()} (A101)",
                brand='A101',
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
                source='VERİ_MEVCUT_DEĞİL',
                source_product_id=None,
                price_status='UNAVAILABLE'
            )
        ]
