from unittest.mock import Mock

from app import PratikoRequestHandler
from services.market_service import MarketService
from test_owner_catalog import csv_file, product, upload
from test_ownership import PASSWORD, application, login, register


def test_fresh_install_hybrid_workflow(app, monkeypatch):
    visitor, owner, admin = (app.test_client() for _ in range(3))
    categories = visitor.get('/api/categories').json
    assert len(categories) == 7
    assert sum(len(category['sub_categories']) for category in categories) == 66

    result = app.test_cli_runner().invoke(
        args=['create-admin', 'qa-admin@example.test'], input=f'{PASSWORD}\n{PASSWORD}\n'
    )
    assert result.exit_code == 0
    register(owner, 'qa-owner@example.test')
    assert owner.post('/api/v1/auth/logout', json={}).status_code == 204
    assert login(owner, 'qa-owner@example.test').status_code == 200
    assert login(admin, 'qa-admin@example.test').status_code == 200
    claim_id = application(owner, 'ChIJPratikoDemo')
    assert owner.get('/api/v1/owner/branches').status_code == 403
    decision = admin.patch(f'/api/v1/admin/ownership-applications/{claim_id}', json={'status': 'APPROVED'})
    assert decision.status_code == 200
    branch_id = decision.json['branch_id']
    branch = f'/api/v1/owner/branches/{branch_id}'
    assert [row['id'] for row in owner.get('/api/v1/owner/branches').json] == [branch_id]
    assert owner.get('/api/v1/owner/branches/999').status_code == 403
    assert owner.post('/api/v1/owner/branches/999/products', json=product()).status_code == 403

    single = owner.post(branch + '/products', json=product(price='89,90'))
    assert single.status_code == 201
    content = csv_file([product(price='74,50', price_scope='CAMPAIGN')])
    preview = upload(owner, branch + '/imports/preview', content)
    assert preview.status_code == 200 and len(preview.json['valid_rows']) == 1
    commit = upload(owner, branch + '/imports/commit', content, token=preview.json['token'])
    assert commit.status_code == 201
    queue = admin.get('/api/v1/admin/price-submissions').json['items']
    assert [row['submission_source'] for row in queue] == ['IMPORT', 'SINGLE']

    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [{
        'id': 'ChIJPratikoDemo', 'google_place_id': 'ChIJPratikoDemo',
        'name': 'Doğrulanmış Şube', 'distance_km': 0.1,
    }])
    query = '/api/v1/market-search?lat=41.1&lon=29.2&query=pirinç'
    assert all(item['price'] is None for item in visitor.get(query).json['results'])
    assert admin.patch(f"/api/v1/admin/price-submissions/{single.json['id']}",
                       json={'status': 'APPROVED'}).status_code == 200
    assert admin.patch(f"/api/v1/admin/price-submissions/{queue[0]['id']}", json={
        'status': 'REJECTED', 'rejection_reason': 'Kampanya bitiş tarihi teyit edilemedi.',
    }).status_code == 200
    visible = visitor.get(query).json['results']
    assert [(item['price'], item['source'], item['price_scope']) for item in visible] == [
        (89.90, 'MARKET_OWNER', 'BRANCH'),
    ]
    history = owner.get(branch + '/price-submissions').json['items']
    assert [row['status'] for row in history] == ['REJECTED', 'APPROVED']
    assert history[0]['rejection_reason'] == 'Kampanya bitiş tarihi teyit edilemedi.'


def test_request_log_omits_sensitive_query_string():
    handler = object.__new__(PratikoRequestHandler)
    handler.command = 'POST'
    handler.path = '/api/v1/auth/login?password=test-only&lat=41.1'
    handler.log = Mock()
    handler.log_request(200)
    handler.log.assert_called_once_with('info', '%s %s %s', 'POST', '/api/v1/auth/login', 200)
