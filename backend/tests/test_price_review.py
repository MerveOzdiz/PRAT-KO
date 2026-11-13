from datetime import datetime

import pytest
from sqlalchemy import text

from models.db import db
from services.google_maps_service import PlacesUnavailable
from services.market_service import MarketService
from services.owner_catalog_service import TURKEY_TIME
from test_owner_catalog import csv_file, owner_context, product, table, upload
from test_ownership import login, register

ADMIN = '/api/v1/admin/price-submissions'


@pytest.fixture
def review_context(app, owner_context, monkeypatch):
    owner, own, other_path = owner_context
    admin, other, public = (app.test_client() for _ in range(3))
    assert login(admin, 'admin@example.test').status_code == 200
    assert login(other, 'other@example.test').status_code == 200
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [])
    return admin, owner, own, other, other_path, public


def submit(client, branch, **values):
    response = client.post(branch + '/products', json=product(**values))
    assert response.status_code == 201, response.json
    return response.json['id']


def decision(client, submission_id, status='APPROVED', **extra):
    return client.patch(f'{ADMIN}/{submission_id}', json={'status': status, **extra})


def search(client, **filters):
    response = client.get('/api/v1/market-search', query_string={
        'lat': 41.1, 'lon': 29.2, 'query': 'pirinç', **filters,
    })
    assert response.status_code == 200, response.json
    return [row for row in response.json['results'] if row['source'] == 'MARKET_OWNER']


def test_admin_only_decisions_and_private_rejection(app, review_context):
    admin, owner, own, other, other_path, public = review_context
    normal = app.test_client()
    register(normal, 'normal@example.test')
    approved = submit(owner, own, price='10')
    rejected = submit(owner, own, price='12')
    assert decision(public, approved).status_code == 401
    assert decision(normal, approved).status_code == 403
    assert decision(owner, approved).status_code == 403
    assert owner.get(ADMIN).status_code == 403
    assert decision(admin, rejected, 'REJECTED').status_code == 400
    assert search(public) == []
    assert decision(admin, approved).status_code == 200
    assert decision(admin, rejected, 'REJECTED', rejection_reason='Etiket okunamadı.').status_code == 200
    assert decision(admin, approved, 'REJECTED', rejection_reason='Tekrar').status_code == 409
    assert [row['price'] for row in search(public)] == [10]
    assert table("""
        SELECT s.status, account.role, s.reviewed_at IS NOT NULL
        FROM price_submission AS s JOIN user_account AS account ON account.id = s.reviewed_by
        ORDER BY s.id
    """) == [('APPROVED', 'ADMIN', 1), ('REJECTED', 'ADMIN', 1)]

    history = owner.get(own + '/price-submissions').json['items']
    assert [row['status'] for row in history] == ['REJECTED', 'APPROVED']
    assert history[0]['rejection_reason'] == 'Etiket okunamadı.'
    assert other.get(own + '/price-submissions').status_code == 403
    assert other.get(other_path + '/price-submissions').json['items'] == []
    assert normal.get(own + '/price-submissions').status_code == 403


def test_admin_filters_show_single_and_import_origin(review_context):
    admin, owner, own, _, _, _ = review_context
    single_id = submit(owner, own)
    content = csv_file([product(price_scope='ONLINE')])
    token = upload(owner, own + '/imports/preview', content).json['token']
    assert upload(owner, own + '/imports/commit', content, token=token).status_code == 201
    rows = admin.get(ADMIN, query_string={
        'market': 'örnek', 'branch': 'doğrulanmış',
        'submitted_on': datetime.now(TURKEY_TIME).date().isoformat(),
    }).json['items']
    assert [row['submission_source'] for row in rows] == ['IMPORT', 'SINGLE']
    assert admin.get(ADMIN, query_string={'price_scope': 'BRANCH'}).json['items'][0]['id'] == single_id
    assert admin.get(ADMIN, query_string={'market': 'başka'}).json['items'] == []
    assert admin.get(ADMIN, query_string={'submitted_on': '2026-02-30'}).status_code == 400
    assert admin.get(ADMIN, query_string={'price_scope': 'invalid'}).status_code == 400


def test_publication_keeps_prior_price_and_separates_comparisons(review_context, monkeypatch):
    admin, owner, own, other, other_path, public = review_context
    original = submit(owner, own, price='10')
    latest = submit(owner, own, price='25')
    competitor = submit(other, other_path, price='20')
    campaign = submit(owner, own, price='1', price_scope='CAMPAIGN')
    online = submit(owner, own, price='2', price_scope='ONLINE')
    small_pack = submit(owner, own, quantity='500', unit='g', price='3')
    foreign_currency = submit(owner, own, price='4', currency='EUR')
    for identifier in (original, competitor, campaign, online, small_pack, foreign_currency):
        assert decision(admin, identifier).status_code == 200
    offers = search(public)
    assert {row['price'] for row in offers} == {1, 2, 3, 4, 10, 20}
    assert {row['price_scope'] for row in offers} == {'BRANCH', 'ONLINE', 'CAMPAIGN'}
    assert [row['price'] for row in offers if row['is_cheapest']] == [10]
    assert all('rejection_reason' not in row and 'reviewed_by' not in row for row in offers)
    assert search(public, category='Temel Gıda')
    assert search(public, category='İçecek') == []
    assert search(public, lat=42) == []
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [{
        'id': 'ChIJOwner', 'google_place_id': 'ChIJOwner', 'name': 'Doğrulanmış Şube',
        'distance_km': 0.1,
    }])
    response = public.get('/api/v1/market-search?lat=41.1&lon=29.2&query=pirinç')
    assert all(row['source'] == 'MARKET_OWNER' for row in response.json['results'])

    assert decision(admin, latest).status_code == 200
    assert [row['price'] for row in search(public) if row['is_cheapest']] == [20]
    assert 10 not in {row['price'] for row in search(public)}
    assert [row for row in owner.get(own + '/price-submissions').json['items']
            if row['id'] == original][0]['status'] == 'APPROVED'
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE price_submission SET valid_until = '2000-01-01' WHERE id = :id"),
                           {'id': latest})
    assert {row['price'] for row in search(public)} == {1, 2, 3, 4, 20}

    def unavailable(*args):
        raise PlacesUnavailable()

    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', unavailable)
    assert {row['price'] for row in search(public)} == {1, 2, 3, 4, 20}


def test_expired_and_unaudited_prices_cannot_publish(review_context):
    admin, owner, own, _, _, public = review_context
    expired = submit(owner, own, price='8')
    unaudited = submit(owner, own, price='9')
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE price_submission SET valid_until = '2000-01-01' WHERE id = :id"),
                           {'id': expired})
        connection.execute(text("UPDATE price_submission SET status = 'APPROVED' WHERE id = :id"),
                           {'id': unaudited})
    assert decision(admin, expired).status_code == 409
    assert search(public) == []
