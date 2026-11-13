import math
import re

from flask import Blueprint, abort, current_app, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from models.db import db
from services.owner_import_service import MAX_FILE_BYTES
from services.account_service import (
    account_credentials, create_account, end_account_session, query_all, query_one,
    require_account, require_branch_owner, start_account_session,
)

account_bp = Blueprint('accounts', __name__, url_prefix='/api/v1')
DUMMY_HASH = generate_password_hash('unused-password-for-timing')


@account_bp.before_request
def protect_account_requests():
    if request.method == 'OPTIONS':
        return
    if len(current_app.secret_key or '') < 32 or db.engine.dialect.name != 'sqlite':
        abort(503, 'Hesap sistemi yapılandırılmamış.')
    if request.method in ('POST', 'PATCH'):
        origin = request.headers.get('Origin')
        if origin is not None and origin not in current_app.config['CORS_ORIGINS']:
            abort(403, 'İstek kaynağına izin verilmiyor.')
        if request.endpoint in {
            'accounts.owner_catalog.preview_import', 'accounts.owner_catalog.commit_import',
        }:
            if request.headers.get('X-Pratiko-Import') != '1':
                abort(403, 'Dosya aktarımı için geçerli istek başlığı gerekli.')
            if request.mimetype != 'multipart/form-data':
                abort(415, 'Dosya yükleme biçimi geçersiz.')
            request.max_content_length = MAX_FILE_BYTES + 65536
            request.max_form_memory_size = 131072
            request.max_form_parts = 4
        else:
            if not request.is_json:
                abort(415, 'JSON içerik gerekli.')
            request.max_content_length = 16384


@account_bp.after_request
def prevent_caching(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@account_bp.errorhandler(HTTPException)
def account_error(error):
    return jsonify(error=error.description), error.code


def body():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400, 'Geçerli bir JSON nesnesi gerekli.')
    return data


def credentials():
    try:
        return account_credentials(body())
    except ValueError as exc:
        abort(400, str(exc))


@account_bp.post('/auth/register')
def register():
    email, password = credentials()
    try:
        account_id = create_account(email, password)
    except IntegrityError:
        abort(409, 'Bu e-posta zaten kayıtlı.')
    start_account_session(account_id)
    return jsonify(id=account_id, email=email, role='USER'), 201


@account_bp.post('/auth/login')
def login():
    email, password = credentials()
    account = query_one('SELECT * FROM user_account WHERE email = :email', email=email)
    valid = check_password_hash(account['password_hash'] if account else DUMMY_HASH, password)
    if not valid or account is None:
        abort(401, 'E-posta veya parola hatalı.')
    start_account_session(account['id'])
    return jsonify(id=account['id'], email=account['email'], role=account['role'])


@account_bp.post('/auth/logout')
def logout():
    end_account_session()
    return '', 204


@account_bp.get('/auth/me')
@require_account()
def me():
    return jsonify(dict(g.account))


def required_text(data, field, label, limit):
    value = data.get(field)
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
        abort(400, f'{label} 1–{limit} karakter olmalı.')
    return value.strip()


@account_bp.post('/ownership-applications')
@require_account('USER', 'OWNER')
def submit_application():
    data = body()
    fields = {
        'business_name': ('İşletme adı', 150),
        'branch_name': ('Şube adı', 150),
        'address': ('Şube adresi', 255),
        'google_place_id': ('Google Place ID', 100),
        'verification_note': ('Doğrulama bilgisi', 1000),
    }
    application = {field: required_text(data, field, *limits) for field, limits in fields.items()}
    if not re.fullmatch(r'[A-Za-z0-9_-]+', application['google_place_id']):
        abort(400, 'Google Place ID biçimi geçersiz.')
    for field, bound in (('latitude', 90), ('longitude', 180)):
        value = data.get(field)
        if type(value) not in (int, float) or not -bound <= value <= bound or not math.isfinite(value):
            abort(400, 'Şube koordinatları geçersiz.')
        application[field] = value
    application['applicant_id'] = g.account['id']
    try:
        with db.engine.begin() as connection:
            application_id = connection.execute(text("""
                INSERT INTO ownership_application
                    (applicant_id, business_name, branch_name, address, latitude, longitude,
                     google_place_id, verification_note)
                VALUES (:applicant_id, :business_name, :branch_name, :address, :latitude, :longitude,
                        :google_place_id, :verification_note)
            """), application).lastrowid
    except IntegrityError:
        abort(409, 'Bu şube için bekleyen başvurunuz var.')
    return jsonify(id=application_id, status='PENDING'), 201


@account_bp.get('/ownership-applications/mine')
@require_account('USER', 'OWNER')
def my_applications():
    return jsonify(query_all("""
        SELECT id, business_name, branch_name, status, rejection_reason, branch_id, created_at
        FROM ownership_application WHERE applicant_id = :id ORDER BY id DESC
    """, id=g.account['id']))


@account_bp.get('/owner/branches')
@require_account('OWNER')
def owner_branches():
    return jsonify(query_all("""
        SELECT branch.id, branch.name, branch.address, branch.google_place_id
        FROM branch_membership JOIN branch ON branch.id = branch_membership.branch_id
        WHERE branch_membership.user_id = :id AND branch.is_active = 1
        ORDER BY branch.name, branch.id
    """, id=g.account['id']))


@account_bp.get('/owner/branches/<int:branch_id>')
@require_account('OWNER')
def owner_branch(branch_id):
    return jsonify(dict(require_branch_owner(branch_id)))


@account_bp.get('/admin/ownership-applications')
@require_account('ADMIN')
def review_queue():
    return jsonify(query_all("""
        SELECT application.*, account.email AS applicant_email
        FROM ownership_application AS application
        JOIN user_account AS account ON account.id = application.applicant_id
        WHERE application.status = 'PENDING' ORDER BY application.id LIMIT 100
    """))


def grant_branch(connection, application):
    branch = connection.execute(text("""
        SELECT id, is_active FROM branch WHERE google_place_id = :google_place_id
    """), dict(application)).mappings().first()
    details = {
        'name': application['branch_name'], 'address': application['address'],
        'latitude': application['latitude'], 'longitude': application['longitude'],
        'place_id': application['google_place_id'],
    }
    if branch is None:
        branch_id = connection.execute(text("""
            INSERT INTO branch (name, address, latitude, longitude, google_place_id,
                                is_active, created_at, updated_at)
            VALUES (:name, :address, :latitude, :longitude, :place_id,
                    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), details).lastrowid
    else:
        if not branch['is_active']:
            abort(409, 'Şube etkin değil.')
        branch_id = branch['id']
        if connection.execute(text(
            'SELECT 1 FROM branch_membership WHERE branch_id = :id'
        ), dict(id=branch_id)).first():
            abort(409, 'Bu şube için bir sahip zaten onaylandı.')
        connection.execute(text("""
            UPDATE branch SET name = :name, address = :address, latitude = :latitude,
                longitude = :longitude, updated_at = CURRENT_TIMESTAMP WHERE id = :id
        """), {**details, 'id': branch_id})

    connection.execute(text("""
        INSERT INTO branch_membership (branch_id, user_id, application_id)
        VALUES (:branch_id, :applicant_id, :id)
    """), {**dict(application), 'branch_id': branch_id})
    connection.execute(text("""
        UPDATE user_account SET role = 'OWNER' WHERE id = :applicant_id AND role = 'USER'
    """), dict(application))
    return branch_id


@account_bp.patch('/admin/ownership-applications/<int:application_id>')
@require_account('ADMIN')
def decide_application(application_id):
    data = body()
    decision = data.get('status')
    if decision not in ('APPROVED', 'REJECTED'):
        abort(400, 'Geçerli bir karar seçin.')
    reason = (required_text(data, 'rejection_reason', 'Ret gerekçesi', 1000)
              if decision == 'REJECTED' else None)

    with db.engine.begin() as connection:
        # Serialize ownership decisions before reading the pending application or its branch.
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        application = connection.execute(text("""
            SELECT * FROM ownership_application WHERE id = :id
        """), dict(id=application_id)).mappings().first()
        if application is None:
            abort(404, 'Başvuru bulunamadı.')
        if application['status'] != 'PENDING':
            abort(409, 'Başvuru zaten sonuçlandırılmış.')
        branch_id = grant_branch(connection, application) if decision == 'APPROVED' else None
        connection.execute(text("""
            UPDATE ownership_application
            SET status = :status, decided_by = :admin_id, decided_at = CURRENT_TIMESTAMP,
                rejection_reason = :reason, branch_id = :branch_id
            WHERE id = :id
        """), dict(id=application_id, status=decision, admin_id=g.account['id'],
                   reason=reason, branch_id=branch_id))
    return jsonify(id=application_id, status=decision, branch_id=branch_id)
