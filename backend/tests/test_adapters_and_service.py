from dataclasses import replace
from unittest.mock import Mock

import requests

from adapters.bim_adapter import BimAdapter
from adapters.migros_adapter import MigrosAdapter
from adapters.carrefour_adapter import CarrefourAdapter
from services.cache_service import SimpleTTLCache
from services.google_maps_service import GoogleMapsService
from services.market_service import MarketService
from services.product_comparison import mark_cheapest


def test_migros_fixture(monkeypatch):
    response = Mock()
    response.json.return_value = {'data': {'storeProductInfos': [
        None, {'name': 'Eksik veri'}, {'name': 'Nutella 750 g', 'sku': '123', 'shownPrice': 20000},
    ]}}
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: response)
    [item] = MigrosAdapter().search_products('branch', 'Nutella')
    assert item.price == 200
    assert item.price_scope == 'ONLINE'
    assert item.branch_id is None and item.barcode is None


def test_carrefour_fixture_and_comparison(monkeypatch):
    html = '''<div class="product-card"><span class="item-name">Nutella 750 g</span>
        <span class="item-price">149,95 TL</span><a href="/nutella-p-456">Ürün</a></div>'''
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: Mock(text=html))
    [offer] = CarrefourAdapter().search_products('branch', 'Nutella')
    assert offer.price == 149.95 and offer.stock_status == 'UNKNOWN'
    products = [item.to_dict() for item in (
        offer, replace(offer, market_code='MIGROS', price=170),
        replace(offer, market_code='MIGROS', product_name='Nutella 400 g', price=40),
        replace(offer, market_code='BIM', price_scope='CATALOG', price=5),
        replace(offer, market_code='LOCAL', price=None, price_status='UNAVAILABLE'),
    )]
    mark_cheapest(products)
    assert [item['is_cheapest'] for item in products] == [True, False, False, False, False]


def test_bim_fixture():
    html = '''<section class="aktuelArea"><div class="tabArea">
        <a class="subButton active">3 Kasım</a></div><div class="productArea">
        <div class="product"><div class="imageArea"><a href="/aktuel-urunler/test/aktuel.aspx"></a></div>
        <div class="descArea"><h2 class="title">Test süt</h2><h2 class="subTitle">Marka</h2>
        <div class="gramajadet">• 1 L</div></div><div class="priceArea">
        <a class="gButton">39, <span>90</span> ₺</a></div></div></div></section>'''
    [item] = BimAdapter.parse_catalog(html)
    assert (item.price, item.price_scope, item.branch_id, item.campaign_label) == (39.9, 'CATALOG', None, '3 Kasım')


def test_market_discovery_3km_and_ids(monkeypatch):
    def place(id, lat, types=None):
        return {'id': id, 'displayName': {'text': 'Mahalle Marketi'},
                'formattedAddress': 'Aynı Cadde', 'types': types or ['grocery_store'],
                'location': {'latitude': lat, 'longitude': 29}}
    response = Mock()
    response.json.return_value = {'places': [
        place('a', 41.001), place('a', 41.001), place('b', 41.00101),
        place('outside', 41.03), place('gas', 41.002, ['gas_station', 'convenience_store']),
    ]}

    def post(*args, **kwargs):
        assert kwargs['json']['locationRestriction']['circle']['radius'] == 3000
        return response
    monkeypatch.setattr(requests, 'post', post)
    branches = MarketService.get_sorted_nearby_markets(41, 29, 'fixture')
    assert [item['id'] for item in branches] == ['a', 'b']


def test_timeout_no_fake_branches(client, monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, 'post', timeout)
    for url in ('/api/nearby-markets?lat=41&lon=29', '/api/v1/market-search?lat=41&lon=29&query=sut'):
        response = client.get(url)
        assert response.status_code == 503
        assert response.json['code'] == 'PLACES_UNAVAILABLE'


def test_cache_expiry_and_size():
    cache = SimpleTTLCache(max_entries=1)
    cache.set('expired', 42, ttl_seconds=0)
    assert cache.get('expired') is None
    cache.set('old', 1)
    cache.set('new', 2)
    assert cache.get('old') is None
    assert cache.get('new') == 2


def test_saturated_nearby_adds_bounded_text_queries(monkeypatch):
    def place(place_id, latitude):
        return {
            'id': place_id, 'displayName': {'text': 'Mahalle Marketi'},
            'types': ['grocery_store'], 'location': {'latitude': latitude, 'longitude': 29},
        }

    calls = []

    def post(url, **kwargs):
        payload = kwargs['json']
        calls.append(payload)
        if url.endswith(':searchNearby'):
            return Mock(json=Mock(return_value={'places': [place('same', 41.001)] * 20}))
        if payload['textQuery'] == 'bakkal':
            raise requests.Timeout()
        return Mock(json=Mock(return_value={'places': [
            place('same', 41.001), place('other', 41.01), place('out', 41.03),
        ], 'nextPageToken': 'not-followed'}))

    monkeypatch.setattr(requests, 'post', post)
    branches = MarketService.get_sorted_nearby_markets(41, 29, 'fixture')
    assert [branch['id'] for branch in branches] == ['same', 'other']
    assert len(calls) == 4
    assert {call.get('textQuery') for call in calls} == {None, 'bakkal', 'süpermarket'}