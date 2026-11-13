from models.category import Category
from typing import List, Dict, Any

class CategoryService:
    @staticmethod
    def get_all_root_categories() -> List[Dict[str, Any]]:
        root_categories = Category.query.filter_by(parent_id=None).order_by(Category.id).all()
        return [cat.to_dict() for cat in root_categories]
