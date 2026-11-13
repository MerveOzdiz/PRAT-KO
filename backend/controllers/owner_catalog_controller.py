import hashlib
import json
from pathlib import Path

from flask import Blueprint, abort, current_app, g, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import text

from controllers.account_controller import body
from models.db import db
from services.account_service import query_one, require_account, require_branch_owner
from services.owner_catalog_service import save_pending, validate_rows
from services.owner_import_service import MAX_FILE_BYTES, SUPPORTED_EXTENSIONS, parse_upload


catalog_bp = Blueprint('owner_catalog', __name__, url_prefix='/owner/branches/<int:branch_id>')


def serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='owner-catalog-import-v1')


def fingerprint(value):
    return hashlib.sha256(value).hexdigest()


def upload():
    files = request.files.getlist('file')
    if len(files) != 1 or not files[0].filename:
        abort(400, 'Tek bir CSV veya XLSX dosyası yükleyin.')
    file = files[0]
    if Path(file.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        abort(400, 'Yalnızca CSV ve XLSX dosyaları desteklenir.')
    data = file.stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        abort(413, 'Dosya en çok 1 MiB olabilir.')
    if not data:
        abort(400, 'Dosya boş.')
    return file.filename, data


def parse_file(filename, content):
    try:
        return parse_upload(filename, content)
    except ValueError as exc:
        abort(400, str(exc))


def preview_context(branch_id, filename, content):
    return {
        'branch_id': branch_id, 'user_id': g.account['id'], 'session': g.session_digest,
        'digest': fingerprint(content), 'extension': Path(filename).suffix.lower(),
    }


def plan_fingerprint(plan):
    return fingerprint(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode())


@catalog_bp.post('/products')
@require_account('OWNER')
def submit_product(branch_id):
    with db.engine.begin() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        require_branch_owner(branch_id, connection)
        plan = validate_rows(connection, [(1, body(), None)])
        if plan['invalid_rows']:
            abort(400, plan['invalid_rows'][0]['error'])
        saved = save_pending(connection, branch_id, g.account['id'], plan['valid_rows'][0]['data'])
    return jsonify(saved), 201


@catalog_bp.post('/imports/preview')
@require_account('OWNER')
def preview_import(branch_id):
    require_branch_owner(branch_id)
    filename, content = upload()
    context = preview_context(branch_id, filename, content)
    duplicate = query_one("""
        SELECT id, accepted_rows, rejected_rows FROM import_batch
        WHERE branch_id = :branch_id AND file_digest = :digest
    """, **context)
    if duplicate is not None:
        return jsonify(already_imported=True, batch=dict(duplicate))
    rows = parse_file(filename, content)
    with db.engine.connect() as connection:
        plan = validate_rows(connection, rows)
    return jsonify(**plan, already_imported=False,
                   token=serializer().dumps({**context, 'plan': plan_fingerprint(plan)}))


@catalog_bp.post('/imports/commit')
@require_account('OWNER')
def commit_import(branch_id):
    require_branch_owner(branch_id)
    filename, content = upload()
    context = preview_context(branch_id, filename, content)
    try:
        token = serializer().loads(request.form.get('token', ''), max_age=900)
    except BadSignature:
        abort(400, 'Geçerli bir önizleme gerekli. Dosyayı yeniden önizleyin.')
    if not isinstance(token, dict) or any(token.get(key) != value for key, value in context.items()):
        abort(400, 'Dosya, oturum veya şube önizlemeyle eşleşmiyor.')

    rows = parse_file(filename, content)
    with db.engine.begin() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        require_branch_owner(branch_id, connection)
        duplicate = connection.execute(text("""
            SELECT id, accepted_rows, rejected_rows FROM import_batch
            WHERE branch_id = :branch_id AND file_digest = :digest
        """), context).mappings().first()
        if duplicate is not None:
            return jsonify(already_imported=True, batch=dict(duplicate))

        plan = validate_rows(connection, rows)
        if plan_fingerprint(plan) != token['plan']:
            abort(409, 'Önizleme değişti. Dosyayı yeniden önizleyin.')
        valid, invalid = plan['valid_rows'], plan['invalid_rows']
        if not valid:
            abort(400, 'Gönderilecek geçerli satır yok.')
        if invalid and request.form.get('accept_partial') != 'true':
            abort(400, 'Yalnızca geçerli satırların gönderilmesini onaylayın.')
        batch = {'accepted_rows': len(valid), 'rejected_rows': len(invalid)}
        batch['id'] = connection.execute(text("""
            INSERT INTO import_batch (branch_id, submitted_by, file_digest, accepted_rows, rejected_rows)
            VALUES (:branch_id, :user_id, :digest, :accepted_rows, :rejected_rows)
        """), {**context, **batch}).lastrowid
        for item in valid:
            save_pending(connection, branch_id, g.account['id'], item['data'], batch['id'])
    return jsonify(already_imported=False, batch=batch, status='PENDING'), 201
