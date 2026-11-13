from adapters.bim_adapter import BimAdapter
from services.catalog_categories import matches_category
from services.market_service import MarketService


def test_market_search_endpoint(client, monkeypatch):
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [
        {'id': 'local', 'name': 'Mahalle Marketi', 'distance_km': 0.4},
        {'id': 'file', 'name': 'File Market', 'distance_km': 0.6},
    ])
    response = client.get('/api/v1/market-search?category=Süt&lat=41&lon=29&radius_km=0.5&page_size=1')
    assert response.status_code == 200
    data = response.json
    assert data['total_results'] == 0
    assert data['total_pages'] == 0
    assert data['category'] == 'Süt'
    assert data['results'] == []

    second = client.get('/api/v1/market-search?query=sut&lat=41&lon=29&page_size=1&page=2').json
    assert second['total_pages'] == 2
    assert second['results'][0]['market_code'] == 'FILE'
    assert second['results'][0]['price_status'] == 'UNAVAILABLE'


def test_catalog_category_matching():
    assert matches_category({'product_name': 'Efsane Osmancık Pirinç 5 kg'}, 'Temel Gıda')
    assert not matches_category({'product_name': 'Efsane Osmancık Pirinç 5 kg'}, 'İçecek')


def test_invalid_search_and_cors(client):
    for params in ('lat=nan&lon=29', 'lat=41&lon=91&page_size=0', 'lat=41&lon=29&radius_km=4'):
        assert client.get('/api/v1/market-search?query=sut&' + params).status_code == 400
    health = '/api/v1/health'
    assert 'Access-Control-Allow-Origin' not in client.get(health, headers={'Origin': 'https://example.com'}).headers
    assert client.get(health, headers={'Origin': 'http://localhost:3000'}).headers[
        'Access-Control-Allow-Origin'
    ] == 'http://localhost:3000'


def test_category_selection_filters_priced_and_unpriced_catalog_products(client, monkeypatch):
    from dataclasses import replace
    from adapters.local_adapter import LocalMarketAdapter

    branch = {'id': 'bim', 'name': 'BİM Market', 'distance_km': 0.1}
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [branch])
    template = LocalMarketAdapter().search_products('fixture', '')[0]
    names = ['Kırmızı Elma', 'Biber Turşusu', 'Patates Cipsi', 'Limon Kolonyası',
             'Süt Dolgulu Kek', 'Portakal Suyu', 'Somon Fileto', 'Tam Yağlı Süt']
    offers = [replace(template, product_id=str(i), product_name=name,
                      category_name='', brand='', source='BIM_OFFICIAL_CATALOG',
                      price_scope='CATALOG', price_status='UNAVAILABLE' if i in (0, 1) else 'AVAILABLE',
                      price=None if i in (0, 1) else 10)
              for i, name in enumerate(names)]
    monkeypatch.setattr(BimAdapter, 'search_products', lambda *_: offers)
    expected = {
        'Meyve ve Sebze': {names[0]}, 'Temel Gıda': {names[1]},
        'Atıştırmalık ve Tatlı': {names[2], names[4]},
        'Temizlik ve Kişisel Bakım Ürünleri': {names[3]},
        'İçecek': {names[5]}, 'Et, Tavuk ve Balık': {names[6]},
        'Süt Ürünleri ve Kahvaltılık': {names[7]},
    }
    for category, products in expected.items():
        response = client.get('/api/v1/market-search', query_string={'category': category, 'lat': 41, 'lon': 29})
        assert response.status_code == 200
        assert {row['product_name'] for row in response.json['results']} == products
        assert not any(row['is_cheapest'] for row in response.json['results'])


def test_sort_applies_before_pagination(client, monkeypatch):
    from dataclasses import replace
    from adapters.local_adapter import LocalMarketAdapter

    template = LocalMarketAdapter().search_products('fixture', '')[0]
    offers = [
        replace(template, product_id='near', branch_id='near', distance_meters=100,
                price=20, price_scope='BRANCH', price_status='AVAILABLE'),
        replace(template, product_id='cheap', branch_id='cheap', distance_meters=200,
                price=10, price_scope='BRANCH', price_status='AVAILABLE'),
    ]
    monkeypatch.setattr('controllers.provider_controller.published_owner_prices',
                        lambda *_: [offer.to_dict() for offer in offers])
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [])
    for sort_by, expected in [('price', 'cheap'), ('distance', 'near')]:
        data = client.get('/api/v1/market-search', query_string={
            'lat': 41, 'lon': 29, 'query': 'test', 'page_size': 1, 'sort_by': sort_by,
        }).json
        assert data['total_results'] == 2
        assert data['results'][0]['product_id'] == expected
