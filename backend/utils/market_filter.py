from typing import Dict, Any, List

def tr_lower(text: str) -> str:
    """Helper to convert Turkish text to lowercase handling 'İ' and 'I' properly."""
    if not text:
        return ""
    return text.replace('İ', 'i').replace('I', 'ı').replace('ı', 'i').lower()

# Keywords that explicitly indicate non-market businesses (AVM, Pazar Yeri, Benzinlik, Restoran, Tekel, etc.)
STRICT_EXCLUDE_IN_NAME = [
    'avm', 'alışveriş merkezi', 'alisveris merkezi', 'iş merkezi', 'is merkezi',
    'pazar yeri', 'semt pazarı', 'sosyete pazarı', 'bazaar',
    'petrol', 'benzinlik', 'otogaz', 'opet', 'shell', 'bp', 'total', 'petrol ofisi',
    'tekel', 'büfe', 'bufe', 'lokanta', 'restoran', 'cafe', 'kafe', 'döner', 'doner',
    'kebap', 'giyim', 'tekstil', 'oto tamir', 'kuaför', 'kuafor', 'eczane'
]

# Valid Google Places types for retail grocery markets
ALLOWED_TYPES = [
    'supermarket',
    'grocery_store',
    'convenience_store',
    'discount_store'
]

def is_valid_market(place: Dict[str, Any]) -> bool:
    """
    Evaluates whether a Google Places place object represents a valid grocery market / branch.
    Allows all legitimate supermarkets, hypermarkets, grocery stores, and local bakkals/markets.
    Excludes non-market entities like shopping malls (AVM), bazaars (pazar yeri), gas stations, tekel, etc.
    """
    name = tr_lower(place.get('name') or '')
    types = place.get('types') or []

    primary = place.get('primary_type')
    if primary and primary not in ALLOWED_TYPES:
        return False
    if set(types) & {'gas_station', 'restaurant', 'cafe', 'bar'}:
        return False

    if not name or any(word in name.split() for word in ('depo', 'kayak', 'firini', 'firin')):
        return False

    # 1. Strict Exclude Check in Name
    for kw in STRICT_EXCLUDE_IN_NAME:
        if kw in name:
            return False

    # 2. Check types if available
    if types:
        has_allowed_type = any(t in ALLOWED_TYPES for t in types)
        has_market_keyword = any(w in name for w in ['market', 'bakkal', 'gross', 'gıda', 'gida', 'süpermarket', 'supermarket', 'hipermarket'])

        if not (has_allowed_type or has_market_keyword):
            return False

    return True
