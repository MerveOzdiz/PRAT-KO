from datetime import date

from flask import Blueprint, abort, g, jsonify, request

from controllers.account_controller import body, required_text
from services.account_service import require_account, require_branch_owner
from services.price_review_service import price_page, review_price


price_review_bp = Blueprint('price_review', __name__)


def cursor():
    raw = request.args.get('before_id')
    if raw is None:
        return None
    if not raw.isascii() or not raw.isdecimal() or len(raw) > 19 or not 0 < int(raw) < 2**63:
        abort(400, 'Sayfalama değeri geçersiz.')
    return int(raw)


@price_review_bp.get('/admin/price-submissions')
@require_account('ADMIN')
def pending():
    filters = {key: request.args.get(key, '').strip() for key in (
        'market', 'branch', 'price_scope', 'submitted_on',
    )}
    if any(len(value) > 150 for value in filters.values()):
        abort(400, 'Filtre değeri çok uzun.')
    if filters['price_scope'] not in ('', 'BRANCH', 'ONLINE', 'CAMPAIGN'):
        abort(400, 'Fiyat türü geçersiz.')
    if filters['submitted_on']:
        try:
            if date.fromisoformat(filters['submitted_on']).isoformat() != filters['submitted_on']:
                raise ValueError
        except ValueError:
            abort(400, 'Gönderim tarihi geçersiz.')
    return jsonify(price_page(filters, cursor()))


@price_review_bp.patch('/admin/price-submissions/<int:submission_id>')
@require_account('ADMIN')
def decide(submission_id):
    if not 0 < submission_id < 2**63:
        abort(404, 'Fiyat kaydı bulunamadı.')
    data = body()
    status = data.get('status')
    if status not in ('APPROVED', 'REJECTED'):
        abort(400, 'Geçerli bir karar seçin.')
    reason = (required_text(data, 'rejection_reason', 'Ret gerekçesi', 1000)
              if status == 'REJECTED' else None)
    return jsonify(review_price(submission_id, g.account['id'], status, reason))


@price_review_bp.get('/owner/branches/<int:branch_id>/price-submissions')
@require_account('OWNER')
def history(branch_id):
    if not 0 < branch_id < 2**63:
        abort(404, 'Şube bulunamadı.')
    require_branch_owner(branch_id)
    return jsonify(price_page({}, cursor(), owner_id=g.account['id'], branch_id=branch_id))
