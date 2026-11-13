import datetime
from typing import List
from .base_adapter import BaseMarketAdapter
from dto.product_dto import CanonicalProductDTO

class SokAdapter(BaseMarketAdapter):
    def get_chain_code(self) -> str:
        return 'SOK'

    def get_chain_name(self) -> str:
        return 'Cepte ŞOK'

    def search_products(self, branch_id: str, search_term: str, distance_meters: float = 0.0, branch_name: str = "") -> List[CanonicalProductDTO]:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        b_name = branch_name if branch_name else "ŞOK Market Şubesi"
        q = search_term.strip() if search_term else "Ürün"

        return [
            CanonicalProductDTO(
                market_code='SOK',
                market_name='ŞOK Market',
                branch_id=branch_id,
                branch_name=b_name,
                distance_meters=distance_meters,
                barcode=None,
                product_id=f'sok_unavail_{branch_id}',
                product_name=f"{q.capitalize()} (ŞOK Market)",
                brand='ŞOK',
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
