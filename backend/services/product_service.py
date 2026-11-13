from sqlalchemy.orm import joinedload
from models.category import Category
from models.product import Product
from typing import List, Dict, Any, Optional

class ProductService:
    @staticmethod
    def search_products(query_str: Optional[str], category_id: Optional[int]) -> List[Dict[str, Any]]:
        q = Product.query.options(joinedload(Product.market))

        if category_id:
            category = Category.query.get(category_id)
            if category:
                ids_to_search = [cat.id for cat in category.sub_categories]
                ids_to_search.append(category_id)
                q = q.filter(Product.category_id.in_(ids_to_search))

        if query_str:
            search_terms = query_str.split()
            for term in search_terms:
                q = q.filter(Product.name.ilike(f'%{term}%'))

        results = q.all()
        markets_with_products = {}
        for p in results:
            m_id = p.market.id
            if m_id not in markets_with_products:
                markets_with_products[m_id] = {
                    'market_id': m_id,
                    'market_name': p.market.name,
                    'products': []
                }
            markets_with_products[m_id]['products'].append({
                'product_id': p.id,
                'product_name': p.name,
                'product_price': p.price
            })

        return list(markets_with_products.values())
