from datetime import datetime

from flask import abort
from sqlalchemy import text

from models.db import db
from services.account_service import query_all
from services.owner_catalog_service import TURKEY_TIME


PRICE_DETAILS = """
    SELECT s.id, s.branch_id, s.price_minor, s.currency, s.price_scope, s.status,
           s.valid_until, s.created_at, s.reviewed_at, s.rejection_reason,
           p.name, p.brand, p.quantity, p.unit, b.name AS branch_name,
           COALESCE(chain.name, claim.business_name, b.name) AS market_name,
           CASE WHEN s.import_batch_id IS NULL THEN 'SINGLE' ELSE 'IMPORT' END AS submission_source
    FROM price_submission AS s
    JOIN catalog_product AS p ON p.id = s.catalog_product_id
    JOIN branch AS b ON b.id = s.branch_id
    LEFT JOIN market_chain AS chain ON chain.id = b.market_chain_id
    LEFT JOIN branch_membership AS membership ON membership.branch_id = b.id
    LEFT JOIN ownership_application AS claim ON claim.id = membership.application_id
"""


def price_page(filters, before_id=None, owner_id=None, branch_id=None):
    params = {'limit': 51}
    conditions = []
    if owner_id is None:
        conditions.append("s.status = 'PENDING'")
        for key, expression in (
            ('market', 'instr(pratiko_normalize(COALESCE(chain.name, claim.business_name, b.name)), pratiko_normalize(:market)) > 0'),
            ('branch', 'instr(pratiko_normalize(b.name), pratiko_normalize(:branch)) > 0'),
            ('price_scope', 's.price_scope = :price_scope'),
            ('submitted_on', "date(s.created_at, '+3 hours') = :submitted_on"),
        ):
            if filters.get(key):
                conditions.append(expression)
                params[key] = filters[key]
    else:
        conditions.extend((
            's.branch_id = :branch_id', 's.submitted_by = :owner_id',
            'membership.user_id = :owner_id', 'b.is_active = 1',
        ))
        params.update(owner_id=owner_id, branch_id=branch_id)
    if before_id is not None:
        conditions.append('s.id < :before_id')
        params['before_id'] = before_id
    rows = query_all(PRICE_DETAILS + ' WHERE ' + ' AND '.join(conditions)
                     + ' ORDER BY s.id DESC LIMIT :limit', **params)
    return {'items': rows[:50], 'next_before_id': rows[49]['id'] if len(rows) == 51 else None}


def review_price(submission_id, reviewer, status, reason):
    with db.engine.begin() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        submission = connection.execute(text("""
            SELECT s.status, s.valid_until, b.is_active, membership.user_id = s.submitted_by AS owner_matches
            FROM price_submission AS s JOIN branch AS b ON b.id = s.branch_id
            LEFT JOIN branch_membership AS membership ON membership.branch_id = s.branch_id
            WHERE s.id = :id
        """), {'id': submission_id}).mappings().first()
        if submission is None:
            abort(404, 'Fiyat kaydı bulunamadı.')
        if submission['status'] != 'PENDING':
            abort(409, 'Bu fiyat kaydı daha önce sonuçlandırılmış.')
        if status == 'APPROVED':
            if submission['valid_until'] < datetime.now(TURKEY_TIME).date().isoformat():
                abort(409, 'Geçerlilik tarihi dolmuş fiyat onaylanamaz.')
            if not submission['is_active'] or not submission['owner_matches']:
                abort(409, 'Şube veya gönderenin şube yetkisi artık etkin değil.')
        connection.execute(text("""
            UPDATE price_submission
            SET status = :status, reviewed_by = :reviewer, reviewed_at = CURRENT_TIMESTAMP,
                rejection_reason = :reason
            WHERE id = :id
        """), dict(id=submission_id, status=status, reviewer=reviewer, reason=reason))
    return {'id': submission_id, 'status': status}
