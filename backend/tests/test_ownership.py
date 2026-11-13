from flask import jsonify
from sqlalchemy import text
from werkzeug.security import check_password_hash

from app import create_app
from migrations import apply_sqlite_migrations
from models.db import db
from services.account_service import query_one, require_account, require_branch_owner

PASSWORD = 'test account password'
BASE = '/api/v1'


def register(client, email):
    response = client.post(BASE + '/auth/register', json={
        'email': email, 'password': PASSWORD, 'role': 'ADMIN',
    })
    assert response.status_code == 201
    assert response.json['role'] == 'USER'
    return response.json['id']


def login(client, email):
    return client.post(BASE + '/auth/login', json={'email': email, 'password': PASSWORD})


def application(client, place='ChIJTestBranch'):
    response = client.post(BASE + '/ownership-applications', json={
        'business_name': 'Örnek Market', 'branch_name': 'Doğrulanmış Şube', 'address': 'Test Caddesi 1',
        'google_place_id': place, 'latitude': 41.1, 'longitude': 29.2,
        'verification_note': 'İşletmenin kayıtlı telefonuyla teyit edilebilir.',
    })
    assert response.status_code == 201
    return response.json['id']


def test_register_login_logout_and_csrf(app, client):
    account_id = register(client, '  Example@Example.test  ')
    account = query_one('SELECT * FROM user_account WHERE id = :id', id=account_id)
    assert account['email'] == 'example@example.test'
    assert account['password_hash'] != PASSWORD
    assert check_password_hash(account['password_hash'], PASSWORD)
    assert client.get(BASE + '/auth/me').json['role'] == 'USER'
    assert client.post(BASE + '/auth/logout', json={}, headers={'Origin': 'https://other.test'}).status_code == 403
    assert client.post(BASE + '/auth/logout', data={}).status_code == 415
    cookie_name = app.config['SESSION_COOKIE_NAME']
    cookie = client.get_cookie(cookie_name).value
    assert client.post(BASE + '/auth/logout', json={}).status_code == 204
    assert client.get(BASE + '/auth/me').status_code == 401
    replay = app.test_client()
    replay.set_cookie(cookie_name, cookie)
    assert replay.get(BASE + '/auth/me').status_code == 401
    assert client.post(BASE + '/auth/login', json={
        'email': account['email'], 'password': 'wrong long password',
    }).status_code == 401
    assert login(client, account['email']).status_code == 200


def test_approval_rejection_and_branch_write_scope(app):
    @app.post('/__test__/branches/<int:branch_id>/write')
    @require_account('OWNER')
    def test_write(branch_id):
        # Test-only write probe exercises the guard intended for subsequent write endpoints.
        with db.engine.begin() as connection:
            connection.exec_driver_sql('BEGIN IMMEDIATE')
            require_branch_owner(branch_id, connection)
            connection.execute(text('UPDATE branch SET phone = :phone WHERE id = :id'),
                               dict(phone='TEST WRITE', id=branch_id))
        return jsonify(ok=True)

    with db.engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO branch (id, name, latitude, longitude, google_place_id, is_active)
            VALUES (10, 'Existing', 40, 28, 'ChIJTestBranch', 1),
                   (20, 'Other', 40, 28, 'ChIJOther', 1)
        """))
    admin = app.test_client()
    applicant = app.test_client()
    second = app.test_client()
    result = app.test_cli_runner().invoke(args=['create-admin', 'admin@example.test'], input=f'{PASSWORD}\n{PASSWORD}\n')
    assert result.exit_code == 0, result.output
    assert login(admin, 'admin@example.test').status_code == 200
    register(applicant, 'owner@example.test')
    register(second, 'second@example.test')
    first = application(applicant)
    contested = application(second)
    rejected = application(second, 'ChIJRejected')
    assert applicant.get(BASE + '/owner/branches').status_code == 403
    assert applicant.post('/__test__/branches/10/write').status_code == 403
    assert applicant.patch(f'{BASE}/admin/ownership-applications/{first}', json={'status': 'APPROVED'}).status_code == 403
    assert len(admin.get(BASE + '/admin/ownership-applications').json) == 3
    assert len(second.get(BASE + '/ownership-applications/mine').json) == 2

    decision = admin.patch(f'{BASE}/admin/ownership-applications/{first}', json={'status': 'APPROVED'})
    assert decision.status_code == 200
    assert decision.json['branch_id'] == 10
    assert applicant.get(BASE + '/auth/me').json['role'] == 'OWNER'
    assert [row['id'] for row in applicant.get(BASE + '/owner/branches').json] == [10]
    assert applicant.get(BASE + '/owner/branches/10').json['name'] == 'Doğrulanmış Şube'
    assert applicant.get(BASE + '/owner/branches/20').status_code == 403
    assert applicant.post('/__test__/branches/10/write').status_code == 200
    assert applicant.post('/__test__/branches/20/write').status_code == 403
    assert query_one('SELECT phone FROM branch WHERE id = 10')['phone'] == 'TEST WRITE'
    assert query_one('SELECT phone FROM branch WHERE id = 20')['phone'] is None

    assert admin.patch(f'{BASE}/admin/ownership-applications/{contested}', json={'status': 'APPROVED'}).status_code == 409
    assert second.get(BASE + '/auth/me').json['role'] == 'USER'
    assert admin.patch(f'{BASE}/admin/ownership-applications/{rejected}', json={'status': 'REJECTED'}).status_code == 400
    reason = 'Şube sahipliği doğrulanamadı.'
    response = admin.patch(f'{BASE}/admin/ownership-applications/{rejected}', json={
        'status': 'REJECTED', 'rejection_reason': reason,
    })
    assert response.status_code == 200
    assert admin.patch(f'{BASE}/admin/ownership-applications/{rejected}', json={'status': 'APPROVED'}).status_code == 409
    mine = {item['id']: item for item in second.get(BASE + '/ownership-applications/mine').json}
    assert mine[rejected]['rejection_reason'] == reason
    assert mine[contested]['status'] == 'PENDING'
    assert second.post('/__test__/branches/10/write').status_code == 403

    new_application = application(second, 'ChIJNewBranch')
    response = admin.patch(f'{BASE}/admin/ownership-applications/{new_application}', json={'status': 'APPROVED'})
    assert response.status_code == 200
    new_branch = response.json['branch_id']
    assert query_one('SELECT google_place_id FROM branch WHERE id = :id', id=new_branch)['google_place_id'] == 'ChIJNewBranch'
    assert second.post(f'/__test__/branches/{new_branch}/write').status_code == 200
    assert applicant.post(f'/__test__/branches/{new_branch}/write').status_code == 403


def test_migration_preserves_legacy_rows_and_is_repeatable(tmp_path):
    import sqlite3

    path = tmp_path / 'legacy.db'
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE market (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        INSERT INTO market VALUES (1, 'Legacy Market');
        CREATE TABLE category (id INTEGER PRIMARY KEY, name TEXT NOT NULL, parent_id INTEGER);
        INSERT INTO category VALUES (7, 'Legacy Category', NULL);
        CREATE TABLE product (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL,
                              market_id INTEGER NOT NULL, category_id INTEGER NOT NULL);
        INSERT INTO product VALUES (3, 'Legacy Product', 10.25, 1, 7);
    """)
    before = {table: connection.execute(f'SELECT * FROM {table}').fetchall()
              for table in ('market', 'product', 'category')}
    connection.close()

    class LegacyConfig:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{path.as_posix()}'

    migrated = create_app(LegacyConfig)
    with migrated.app_context():
        with db.engine.connect() as reader:
            seeded = reader.exec_driver_sql('SELECT * FROM category ORDER BY id').all()
        apply_sqlite_migrations(db.engine)
        with db.engine.connect() as reader:
            for table in ('market', 'product'):
                assert reader.exec_driver_sql(f'SELECT * FROM {table}').all() == before[table]
            assert reader.exec_driver_sql('SELECT * FROM category ORDER BY id').all() == seeded
            assert set(before['category']) <= set(seeded)
            assert sum(row.parent_id is None for row in seeded) == 8  # 7 standard + legacy
            assert sum(row.parent_id is not None for row in seeded) == 66
            assert reader.exec_driver_sql('SELECT version FROM schema_migration ORDER BY version').scalars().all() == [
                '001_accounts_and_ownership', '002_owner_catalog_and_imports', '003_price_review',
                '004_seed_categories', '005_account_sessions', '006_complete_categories',
            ]
            assert reader.exec_driver_sql('PRAGMA integrity_check').scalar() == 'ok'


def test_create_admin_command_manages_its_own_app_context():
    from conftest import TestConfig

    app = create_app(TestConfig)
    email = 'cli-admin@example.test'
    result = app.test_cli_runner().invoke(
        args=['create-admin', email], input=f'{PASSWORD}\n{PASSWORD}\n',
    )
    assert result.exit_code == 0, result.output
    response = login(app.test_client(), email)
    assert response.status_code == 200
    assert response.json['role'] == 'ADMIN'
