"""Opt-in live smoke test. Run from backend with python check_live_sources.py."""
import requests

from app import app
from adapters.bim_adapter import BimAdapter


def main():
    sources = {
        'Migros': 'https://www.migros.com.tr/rest/products/search?q=Nutella',
        'Migros Toptan (koli)': 'https://toptan.migros.com.tr/nutella-400-g-p-07155050',
        'CarrefourSA': 'https://www.carrefoursa.com/search/?text=Nutella',
        'CarrefourSA marka sayfası': 'https://www.carrefoursa.com/nutella/evinizin-temel-ihtiyaclari/b/9407',
        'ŞOK': 'https://www.sokmarket.com.tr/',
        'A101': 'https://www.a101.com.tr/market',
        'BİM': 'https://www.bim.com.tr/',
        'FİLE': 'https://www.file.com.tr/icerik/8/file-online-satis',
    }
    for name, url in sources.items():
        try:
            response = requests.get(url, timeout=(3, 6))
            print(f'{name}: HTTP {response.status_code}')
        except requests.RequestException as exc:
            print(f'{name}: {type(exc).__name__}')

    query = {'lat': 41.0082, 'lon': 28.9784}
    client = app.test_client()
    nearby = client.get('/api/nearby-markets', query_string=query)
    print('Google Places:', nearby.status_code)
    assert nearby.status_code == 200, 'Live Places requires a configured key and network access.'
    branches = nearby.json
    assert branches and all(branch['distance_km'] <= 3 for branch in branches)
    assert len({branch['id'] for branch in branches}) == len(branches)
    print('Unique branches:', len(branches), '| maximum km:', round(max(
        branch['distance_km'] for branch in branches
    ), 3))

    catalog = BimAdapter().search_products(None, '')
    assert catalog, 'BİM homepage returned no parseable catalog prices.'
    print('BİM published prices:', len(catalog))
    for item in catalog[:3]:
        print(item.product_name, item.price, item.currency, item.campaign_label, item.product_url)
    response = client.get('/api/v1/market-search', query_string={
        **query, 'query': catalog[0].product_name.split()[0],
    })
    assert response.status_code == 200
    offers = [item for item in response.json['results'] if item['price_scope'] == 'CATALOG']
    assert offers and all(item['branch_id'] is None and not item['is_cheapest'] for item in offers)
    print('Live search catalog offers:', len(offers))


if __name__ == '__main__':
    main()
