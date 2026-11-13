from abc import ABC, abstractmethod
from typing import List
from dto.product_dto import CanonicalProductDTO

class BaseMarketAdapter(ABC):
    @abstractmethod
    def get_chain_code(self) -> str:
        """Returns unique code for market chain, e.g. 'MIGROS', 'SOK'"""
        pass

    @abstractmethod
    def get_chain_name(self) -> str:
        """Returns display name for market chain, e.g. 'Migros', 'ŞOK'"""
        pass

    @abstractmethod
    def search_products(self, branch_id: str, search_term: str, distance_meters: float = 0.0, branch_name: str = "") -> List[CanonicalProductDTO]:
        """
        Searches products in a specific store branch and returns unified CanonicalProductDTOs.
        """
        pass
