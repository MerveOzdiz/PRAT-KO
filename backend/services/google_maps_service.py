from concurrent.futures import ThreadPoolExecutor
from math import cos, radians
import logging

import requests

from utils.market_filter import is_valid_market


logger = logging.getLogger(__name__)


class PlacesUnavailable(Exception):
    pass


class GoogleMapsService:
    @staticmethod
    def fetch_nearby_places(user_lat, user_lon, api_key):
        if not api_key or 'Buraya' in api_key:
            logger.warning('Google Places is not configured.')
            raise PlacesUnavailable()
        headers = {
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': (
                'places.id,places.displayName,places.formattedAddress,'
                'places.location,places.types,places.primaryType,places.businessStatus'
            ),
        }

        def fetch(method, payload):
            try:
                response = requests.post(
                    f'https://places.googleapis.com/v1/places:{method}',
                    headers=headers, json=payload, timeout=(3, 5),
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and isinstance(data.get('places', []), list):
                    return data.get('places', [])
                logger.warning('Google Places %s returned an unexpected response.', method)
            except requests.HTTPError as failure:
                status = failure.response.status_code if failure.response is not None else 'unknown'
                logger.warning('Google Places %s returned HTTP %s.', method, status)
            except (requests.RequestException, ValueError) as failure:
                logger.warning('Google Places %s failed (%s).', method, type(failure).__name__)
            return None

        def nearby(rank):
            return fetch('searchNearby', {
                'includedTypes': ['supermarket', 'grocery_store', 'convenience_store'],
                'excludedPrimaryTypes': ['gas_station', 'restaurant', 'cafe'],
                'maxResultCount': 20, 'rankPreference': rank, 'languageCode': 'tr',
                'locationRestriction': {'circle': {
                    'center': {'latitude': user_lat, 'longitude': user_lon}, 'radius': 3000,
                }},
            })

        def text_search(term):
            lat_delta = 0.028
            lon_delta = lat_delta / max(cos(radians(abs(user_lat) + lat_delta)), 0.00001)
            low_lon, high_lon = -180, 180
            if lon_delta < 180:
                low_lon = (user_lon - lon_delta + 180) % 360 - 180
                high_lon = (user_lon + lon_delta + 180) % 360 - 180
            return fetch('searchText', {
                'textQuery': term, 'pageSize': 20, 'languageCode': 'tr',
                'locationRestriction': {'rectangle': {
                    'low': {'latitude': max(-90, user_lat - lat_delta), 'longitude': low_lon},
                    'high': {'latitude': min(90, user_lat + lat_delta), 'longitude': high_lon},
                }},
            })

        with ThreadPoolExecutor(max_workers=2) as executor:
            batches = list(executor.map(nearby, ('POPULARITY', 'DISTANCE')))
            if all(batch is None for batch in batches):
                raise PlacesUnavailable()
            # Keep supplemental requests bounded. MarketService applies the exact circle.
            if any(batch and len(batch) >= 20 for batch in batches):
                batches.extend(executor.map(text_search, ('süpermarket', 'bakkal')))
        places = {}
        for batch in batches:
            for item in batch or []:
                if not isinstance(item, dict) or not item.get('id'):
                    continue
                if item.get('businessStatus') == 'CLOSED_PERMANENTLY':
                    continue
                location = item.get('location')
                name = item.get('displayName')
                if not isinstance(location, dict) or not isinstance(name, dict):
                    continue
                if not isinstance(name.get('text'), str) or not isinstance(item.get('types'), list):
                    continue
                place = {
                    'place_id': item['id'],
                    'name': name['text'],
                    'vicinity': item['formattedAddress'] if isinstance(item.get('formattedAddress'), str) else '',
                    'types': item.get('types', []),
                    'primary_type': item.get('primaryType'),
                    'geometry': {'location': {
                        'lat': location.get('latitude'), 'lng': location.get('longitude'),
                    }},
                }
                if is_valid_market(place):
                    places.setdefault(item['id'], place)
        return list(places.values())

    @staticmethod
    def reverse_geocode(lat, lon, api_key):
        if not api_key:
            return None
        try:
            response = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={'latlng': f'{lat},{lon}', 'key': api_key, 'language': 'tr'},
                timeout=(3, 4),
            )
            response.raise_for_status()
            results = response.json().get('results') or []
            return results[0].get('formatted_address') if results else None
        except (requests.RequestException, ValueError):
            return None
