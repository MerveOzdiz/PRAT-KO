from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class CanonicalProductDTO:
    market_code: str
    market_name: str
    branch_id: Optional[str]
    branch_name: Optional[str]
    distance_meters: Optional[float]
    barcode: Optional[str]
    product_id: str
    product_name: str
    brand: str
    category_name: str
    subcategory_name: Optional[str]
    quantity: Optional[str]
    unit: Optional[str]
    price: Optional[float]
    original_price: Optional[float]
    currency: str
    is_in_stock: bool
    stock_status: str
    image_url: Optional[str]
    last_updated: str
    is_mock: bool = False
    source: str = 'UNAVAILABLE'
    source_product_id: Optional[str] = None
    price_status: str = 'UNAVAILABLE'
    price_scope: Optional[str] = None
    product_url: Optional[str] = None
    source_url: Optional[str] = None
    campaign_label: Optional[str] = None
    valid_until: Optional[str] = None

    def to_dict(self):
        return asdict(self)
