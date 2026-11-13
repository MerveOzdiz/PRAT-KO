from typing import Dict, Type, Optional, List
from .base_adapter import BaseMarketAdapter
from .migros_adapter import MigrosAdapter
from .sok_adapter import SokAdapter
from .carrefour_adapter import CarrefourAdapter
from .a101_adapter import A101Adapter
from .bim_adapter import BimAdapter
from .local_adapter import LocalMarketAdapter

class AdapterRegistry:
    _adapters: Dict[str, BaseMarketAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseMarketAdapter) -> None:
        cls._adapters[adapter.get_chain_code().upper()] = adapter

    @classmethod
    def get(cls, chain_code: str) -> Optional[BaseMarketAdapter]:
        return cls._adapters.get(chain_code.upper())

    @classmethod
    def get_all(cls) -> List[BaseMarketAdapter]:
        return list(cls._adapters.values())

# Initialize all market adapters
AdapterRegistry.register(MigrosAdapter())
AdapterRegistry.register(SokAdapter())
AdapterRegistry.register(CarrefourAdapter())
AdapterRegistry.register(A101Adapter())
AdapterRegistry.register(BimAdapter())
AdapterRegistry.register(LocalMarketAdapter())
