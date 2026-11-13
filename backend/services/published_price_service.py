from datetime import datetime

from dto.product_dto import CanonicalProductDTO
from models.db import db
from services.account_service import query_all
from services.owner_catalog_service import TURKEY_TIME
from services.product_comparison import normalize
from utils.distance import haversine


def published_owner_prices(query, category, coordinates, radius):
    if db.engine.dialect.name != 'sqlite':
        return []
    latitude, longitude = coordinates
    lat_delta = radius / 110
    rows = query_all("""
        SELECT s.id, s.branch_id, s.catalog_product_id, s.price_minor, s.currency, s.price_scope,
               s.valid_until, s.created_at, p.name, p.brand, p.quantity, p.unit,
               b.name AS branch_name, b.google_place_id, b.latitude, b.longitude,
               COALESCE(chain.name, claim.business_name, b.name) AS market_name,
               COALESCE(parent.name, category.name) AS category_name,
               CASE WHEN parent.id IS NOT NULL THEN category.name END AS subcategory_name
        FROM price_submission AS s
        JOIN catalog_product AS p ON p.id = s.catalog_product_id
        JOIN branch AS b ON b.id = s.branch_id
        JOIN branch_membership AS membership ON membership.branch_id = s.branch_id
                                           AND membership.user_id = s.submitted_by
        JOIN ownership_application AS claim ON claim.id = membership.application_id
        JOIN category ON category.id = p.category_id
        LEFT JOIN category AS parent ON parent.id = category.parent_id
        LEFT JOIN market_chain AS chain ON chain.id = b.market_chain_id
        WHERE s.status = 'APPROVED' AND s.reviewed_by IS NOT NULL AND s.reviewed_at IS NOT NULL
          AND s.valid_until >= :today AND b.is_active = 1
          AND b.latitude BETWEEN :min_lat AND :max_lat
          AND NOT EXISTS (
              SELECT 1 FROM price_submission AS newer
              WHERE newer.branch_id = s.branch_id AND newer.catalog_product_id = s.catalog_product_id
                AND newer.submitted_by = s.submitted_by
                AND newer.price_scope = s.price_scope AND newer.currency = s.currency
                AND newer.status = 'APPROVED' AND newer.reviewed_by IS NOT NULL
                AND newer.reviewed_at IS NOT NULL AND newer.id > s.id
          )
    """, today=datetime.now(TURKEY_TIME).date().isoformat(),
        min_lat=latitude - lat_delta, max_lat=latitude + lat_delta)

    terms = normalize(query).split()
    category_key = normalize(category)
    results = []
    for row in rows:
        distance = haversine(latitude, longitude, row['latitude'], row['longitude'])
        if distance > radius:
            continue
        product_text = normalize(f"{row['name']} {row['brand']} {row['quantity']} {row['unit']}")
        if query and (not terms or not all(term in product_text for term in terms)):
            continue
        if category and category_key not in (
            normalize(row['category_name']), normalize(row['subcategory_name']),
        ):
            continue
        offer = CanonicalProductDTO(
            market_code='OWNER', market_name=row['market_name'],
            branch_id=row['google_place_id'] or f"owner-branch:{row['branch_id']}", branch_name=row['branch_name'],
            distance_meters=distance * 1000, barcode=None, product_id=f"owner-price:{row['id']}",
            product_name=row['name'], brand=row['brand'], category_name=row['category_name'],
            subcategory_name=row['subcategory_name'], quantity=row['quantity'], unit=row['unit'],
            price=row['price_minor'] / 100, original_price=None, currency=row['currency'],
            is_in_stock=False, stock_status='UNKNOWN', image_url=None,
            last_updated=row['created_at'].replace(' ', 'T') + 'Z', source='MARKET_OWNER',
            source_product_id=str(row['catalog_product_id']), price_status='AVAILABLE',
            price_scope=row['price_scope'], valid_until=row['valid_until'],
        )
        results.append(offer.to_dict())
    return results
