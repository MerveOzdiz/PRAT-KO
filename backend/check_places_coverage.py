"""Compare Google Places strategies at fixed, public points. Each probe bills API calls."""
from math import cos, radians

import requests

from config.settings import Config
from utils.distance import haversine
from utils.market_filter import is_valid_market


BASE = 'https://places.googleapis.com/v1/places'
FIELDS = 'places.id,places.location,places.displayName,places.primaryType,places.types,places.businessStatus'


def probe(method, payload, center, max_pages=1):
    headers = {'X-Goog-Api-Key': Config.GOOGLE_MAPS_API_KEY, 'X-Goog-FieldMask': FIELDS}
    if method == 'searchText':
        headers['X-Goog-FieldMask'] += ',nextPageToken'
    ids, raw, eligible = set(), 0, 0
    for _ in range(max_pages):
        response = requests.post(f'{BASE}:{method}', headers=headers, json=payload, timeout=(3, 8))
        if not response.ok:
            return ids, f'HTTP {response.status_code}, {raw} ham, {len(ids)} uygun benzersiz'
        data = response.json()
        for place in data.get('places', []):
            raw += 1
            location = place.get('location')
            if not location or place.get('businessStatus') == 'CLOSED_PERMANENTLY':
                continue
            if haversine(*center, location['latitude'], location['longitude']) > 3:
                continue
            if is_valid_market({
                'name': place.get('displayName', {}).get('text', ''),
                'types': place.get('types', []), 'primary_type': place.get('primaryType'),
            }):
                eligible += 1
                ids.add(place['id'])
        token = data.get('nextPageToken')
        if not token:
            break
        payload = {**payload, 'pageToken': token}
    return ids, f'{raw} ham, {eligible} uygun, {len(ids)} benzersiz'


def main():
    if not Config.GOOGLE_MAPS_API_KEY:
        raise SystemExit('Google Places anahtarı gerekli.')
    for name, (lat, lon) in (
        ('İstanbul, Sultanahmet', (41.0082, 28.9784)),
        ('Konya, Alaaddin', (37.8716, 32.4959)),
    ):
        print(name)
        nearby_ids = set()
        for rank in ('POPULARITY', 'DISTANCE'):
            ids, summary = probe('searchNearby', {
                'includedTypes': ['supermarket', 'grocery_store', 'convenience_store'],
                'excludedPrimaryTypes': ['gas_station', 'restaurant', 'cafe'],
                'maxResultCount': 20, 'rankPreference': rank, 'languageCode': 'tr',
                'locationRestriction': {'circle': {
                    'center': {'latitude': lat, 'longitude': lon}, 'radius': 3000,
                }},
            }, (lat, lon))
            print(f'  Nearby {rank}: {summary}; öncekiyle çakışma: {len(ids & nearby_ids)}')
            nearby_ids |= ids
        print(f'  Nearby birleşimi: {len(nearby_ids)}')
        lat_delta = 0.028
        lon_delta = lat_delta / cos(radians(lat))
        for term in ('süpermarket', 'bakkal'):
            ids, summary = probe('searchText', {
                'textQuery': term, 'pageSize': 20, 'languageCode': 'tr',
                'locationRestriction': {'rectangle': {
                    'low': {'latitude': lat - lat_delta, 'longitude': lon - lon_delta},
                    'high': {'latitude': lat + lat_delta, 'longitude': lon + lon_delta},
                }},
            }, (lat, lon), max_pages=2)
            print(f'  Text {term}: {summary}; Nearby listesine ek: {len(ids - nearby_ids)}')


if __name__ == '__main__':
    main()
