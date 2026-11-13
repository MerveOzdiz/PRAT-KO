from datetime import date, datetime, timedelta
from io import BytesIO, StringIO
import csv

import pytest
from openpyxl import Workbook
from sqlalchemy import text

from controllers import owner_catalog_controller
from models.db import db
from services.market_service import MarketService
from services.owner_catalog_service import FIELDS
from test_ownership import PASSWORD, application, login, register


@pytest.fixture
def owner_context(app):
    admin, owner, other = (app.test_client() for _ in range(3))
    result = app.test_cli_runner().invoke(
        args=['create-admin', 'admin@example.test'], input=f'{PASSWORD}\n{PASSWORD}\n'
    )
    assert result.exit_code == 0
    login(admin, 'admin@example.test')
    branches = []
    for client, email, place in ((owner, 'owner@example.test', 'ChIJOwner'),
                                 (other, 'other@example.test', 'ChIJOther')):
        register(client, email)
        identifier = application(client, place)
        response = admin.patch(f'/api/v1/admin/ownership-applications/{identifier}', json={'status': 'APPROVED'})
        assert response.status_code == 200
        branches.append(response.json['branch_id'])
    return owner, f'/api/v1/owner/branches/{branches[0]}', f'/api/v1/owner/branches/{branches[1]}'


def product(**overrides):
    return {
        'name': 'Deneme Pirinç', 'brand': 'Deneme Marka', 'quantity': '1', 'unit': 'kg',
        'category_id': 4, 'price': '32,45', 'currency': 'TRY', 'price_scope': 'BRANCH',
        'valid_until': (date.today() + timedelta(days=30)).isoformat(), **overrides,
    }


def table(sql):
    with db.engine.connect() as connection:
        return connection.execute(text(sql)).all()


def csv_file(rows):
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, delimiter=';')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode('utf-8-sig')


def upload(client, path, content, filename='products.csv', **fields):
    return client.post(path, data={'file': (BytesIO(content), filename), **fields},
                       headers={'X-Pratiko-Import': '1'})


def test_single_submission_product_identity_and_previous_price(owner_context):
    client, own, _ = owner_context
    first = client.post(own + '/products', json=product())
    assert first.status_code == 201
    assert first.json['status'] == 'PENDING'
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE price_submission SET status = 'APPROVED' WHERE id = :id"), first.json)
    second = client.post(own + '/products', json=product(
        name='deneme  pirinç', quantity='1000', unit='g', price='33.75', price_scope='BRANCH'
    ))
    assert second.status_code == 201
    assert second.json['catalog_product_id'] == first.json['catalog_product_id']
    third = client.post(own + '/products', json=product(quantity='500', unit='g', price_scope='CAMPAIGN'))
    assert third.status_code == 201
    assert third.json['catalog_product_id'] != first.json['catalog_product_id']
    online = client.post(own + '/products', json=product(price_scope='ONLINE'))
    assert online.status_code == 201
    assert table('SELECT price_minor, price_scope, status FROM price_submission ORDER BY id') == [
        (3245, 'BRANCH', 'APPROVED'), (3375, 'BRANCH', 'PENDING'),
        (3245, 'CAMPAIGN', 'PENDING'), (3245, 'ONLINE', 'PENDING'),
    ]


def test_branch_authorization_and_invalid_single_rows(app, owner_context):
    owner, own, other = owner_context
    normal = app.test_client()
    register(normal, 'normal@example.test')
    assert normal.post(own + '/products', json=product()).status_code == 403
    assert owner.post(other + '/products', json=product()).status_code == 403
    content = csv_file([product()])
    for path in ('preview', 'commit'):
        assert upload(owner, other + '/imports/' + path, content).status_code == 403
    assert owner.post(own + '/imports/preview', data={'file': (BytesIO(content), 'products.csv')}).status_code == 403
    assert owner.post(own + '/imports/preview', data={'file': (BytesIO(content), 'products.csv')},
                      headers={'Origin': 'https://other.test', 'X-Pratiko-Import': '1'}).status_code == 403
    for bad in ({'price': '-10'}, {'price': '0'}, {'price': 'abc'}, {'price': '1.123'},
                {'quantity': ''}, {'valid_until': '2026-02-30'}, {'category_id': 999}):
        assert owner.post(own + '/products', json=product(**bad)).status_code == 400
    assert table('SELECT * FROM price_submission') == []


def test_csv_preview_partial_commit_and_replay(owner_context):
    client, own, _ = owner_context
    content = csv_file([product(), product(name='', price='20'), product(price='-3'),
                        product(quantity=''), product(valid_until='bad-date')])
    content += b'too;few;columns\n'
    response = upload(client, own + '/imports/preview', content)
    assert response.status_code == 200, response.json
    preview = response.json
    assert [row['row'] for row in preview['valid_rows']] == [2]
    assert [row['row'] for row in preview['invalid_rows']] == [3, 4, 5, 6, 7]
    assert [row['error'].split()[0] for row in preview['invalid_rows']] == [
        'Ürün', 'Fiyat', 'Miktar', 'Geçerlilik', 'Satırdaki',
    ]
    assert table('SELECT * FROM catalog_product') == []
    assert table('SELECT * FROM import_batch') == []
    assert upload(client, own + '/imports/commit', content, token=preview['token']).status_code == 400
    assert upload(client, own + '/imports/commit', content + b'\n', token=preview['token'],
                  accept_partial='true').status_code == 400
    assert table('SELECT * FROM price_submission') == []
    response = upload(client, own + '/imports/commit', content, token=preview['token'], accept_partial='true')
    assert response.status_code == 201
    assert response.json['batch']['accepted_rows'] == 1
    assert response.json['batch']['rejected_rows'] == 5
    assert table('SELECT status, price_minor FROM price_submission') == [('PENDING', 3245)]
    assert upload(client, own + '/imports/preview', content, filename='renamed.csv').json['already_imported']
    replay = upload(client, own + '/imports/commit', content, token=preview['token'], accept_partial='true')
    assert replay.status_code == 200
    assert replay.json['already_imported']
    assert table('SELECT COUNT(*) FROM price_submission') == [(1,)]


def test_xlsx_date_formula_type_and_size_limits(owner_context):
    client, own, _ = owner_context
    book = Workbook()
    sheet = book.active
    sheet.append(FIELDS)
    data = product(valid_until=datetime.combine(date.today() + timedelta(days=30), datetime.min.time()))
    sheet.append([data[field] for field in FIELDS])
    sheet.append([product(price='=1+2')[field] for field in FIELDS])
    buffer = BytesIO()
    book.save(buffer)
    content = buffer.getvalue()
    response = upload(client, own + '/imports/preview', content, filename='products.xlsx')
    assert response.status_code == 200, response.json
    assert len(response.json['valid_rows']) == 1
    assert response.json['valid_rows'][0]['data']['valid_until'] == data['valid_until'].date().isoformat()
    assert 'Formül' in response.json['invalid_rows'][0]['error']
    committed = upload(client, own + '/imports/commit', content, filename='products.xlsx',
                       token=response.json['token'], accept_partial='true')
    assert committed.status_code == 201
    assert upload(client, own + '/imports/preview', b'<html>bad</html>', filename='fake.xlsx').status_code == 400
    assert upload(client, own + '/imports/preview', content, filename='macro.xlsm').status_code == 400
    assert upload(client, own + '/imports/preview', b'0' * (1024 * 1024 + 1)).status_code == 413
    large_csv = csv_file([product(name=f'Ürün {index} ' + 'a' * 80, brand='b' * 100) for index in range(300)])
    assert len(large_csv) > 65536
    large_preview = upload(client, own + '/imports/preview', large_csv)
    assert large_preview.status_code == 200
    assert len(large_preview.json['valid_rows']) == 300


def test_import_failure_rolls_back_and_can_be_retried(owner_context, monkeypatch):
    client, own, _ = owner_context
    content = csv_file([product(), product(name='İkinci ürün')])
    token = upload(client, own + '/imports/preview', content).json['token']
    real_save = owner_catalog_controller.save_pending

    def fail_second(connection, branch, user, data, import_id):
        if data['name'] == 'İkinci ürün':
            raise RuntimeError('test-only write failure')
        return real_save(connection, branch, user, data, import_id)

    with monkeypatch.context() as patch:
        patch.setattr(owner_catalog_controller, 'save_pending', fail_second)
        with pytest.raises(RuntimeError, match='test-only write failure'):
            upload(client, own + '/imports/commit', content, token=token)
    for name in ('catalog_product', 'price_submission', 'import_batch'):
        assert table(f'SELECT COUNT(*) FROM {name}') == [(0,)]
    assert upload(client, own + '/imports/commit', content, token=token).status_code == 201
    assert table('SELECT COUNT(*) FROM price_submission') == [(2,)]


def test_pending_prices_do_not_enter_public_search(app, owner_context, monkeypatch):
    client, own, _ = owner_context
    assert client.post(own + '/products', json=product(name='PRATIKO_PENDING_SENTINEL')).status_code == 201
    monkeypatch.setattr(MarketService, 'get_sorted_nearby_markets', lambda *_: [{
        'id': 'ChIJOwner', 'google_place_id': 'ChIJOwner', 'name': 'Doğrulanmış Şube',
        'distance_km': 0.2,
    }])
    public = app.test_client()
    legacy = public.get('/api/product-search?query=PRATIKO_PENDING_SENTINEL')
    assert legacy.status_code == 200
    assert legacy.json == []
    result = public.get('/api/v1/market-search?lat=41.1&lon=29.2&query=PRATIKO_PENDING_SENTINEL')
    assert result.status_code == 200
    assert result.json['results']
    assert all(item['price_status'] == 'UNAVAILABLE' and item['price'] is None for item in result.json['results'])
