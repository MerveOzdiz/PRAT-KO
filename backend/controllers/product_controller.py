from flask import Blueprint, jsonify, request
from services.product_service import ProductService

product_bp = Blueprint('product_bp', __name__)

@product_bp.route('/api/product-search', methods=['GET'])
def product_search():
    query = request.args.get('query', '')
    category_id = request.args.get('category_id', type=int)

    try:
        results = ProductService.search_products(query, category_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Ürün araması sırasında hata oluştu: {str(e)}"}), 500
