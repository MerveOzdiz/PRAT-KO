from flask import Blueprint, jsonify
from services.category_service import CategoryService

category_bp = Blueprint('category_bp', __name__)

@category_bp.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = CategoryService.get_all_root_categories()
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": f"Kategoriler alınırken hata oluştu: {str(e)}"}), 500
