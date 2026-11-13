from utils.distance import haversine
from utils.market_filter import tr_lower
from services.google_maps_service import GoogleMapsService


class MarketService:
    @staticmethod
    def get_sorted_nearby_markets(user_lat, user_lon, api_key):
        markets = []
        seen_ids = set()
        for place in GoogleMapsService.fetch_nearby_places(user_lat, user_lon, api_key):
            place_id = place.get('place_id')
            if place_id and place_id in seen_ids:
                continue

            name = place.get('name') or 'Market'
            address = place.get('vicinity') or ''
            location = place.get('geometry', {}).get('location', {})
            lat, lon = location.get('lat'), location.get('lng')
            if not isinstance(lat, (float, int)) or not isinstance(lon, (float, int)):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            distance = haversine(user_lat, user_lon, lat, lon)
            if distance > 3:
                continue

            # Coordinates only corroborate identity when at least one ID is missing.
            if address and any(
                not (place_id and market['google_place_id'])
                and tr_lower(name.strip()) == tr_lower(market['name'].strip())
                and tr_lower(address.strip()) == tr_lower(market['address'].strip())
                and haversine(lat, lon, market['latitude'], market['longitude']) < 0.03
                for market in markets
            ):
                continue

            if place_id:
                seen_ids.add(place_id)
            markets.append({
                'id': place_id or f'{lat}:{lon}:{name}',
                'google_place_id': place_id,
                'name': name,
                'address': address,
                'distance_km': distance,
                'latitude': lat,
                'longitude': lon,
            })
        return sorted(markets, key=lambda market: market['distance_km'])
