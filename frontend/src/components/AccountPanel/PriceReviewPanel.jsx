import React, { useEffect, useState } from 'react';
import { accountRequest } from '../../services/accounts';
import { formatPrice, priceScopeLabels } from '../../services/pricePresentation';

const inputStyle = 'w-full rounded-lg border border-slate-300 p-2';
const buttonStyle = 'rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60';
const labels = { PENDING: 'Bekliyor', APPROVED: 'Onaylandı', REJECTED: 'Reddedildi' };

function formatDate(value) {
  return new Date(value.replace(' ', 'T') + 'Z').toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
}

function ReviewActions({ item, busy, decide }) {
  return (
    <div className="space-y-2">
      <button type="button" className={buttonStyle} disabled={busy}
        onClick={() => decide(item.id, { status: 'APPROVED' })}>Fiyatı onayla</button>
      <form className="flex flex-wrap items-end gap-2" onSubmit={(event) => {
        event.preventDefault();
        const reason = new FormData(event.currentTarget).get('reason');
        decide(item.id, { status: 'REJECTED', rejection_reason: reason });
      }}>
        <label>Fiyat ret gerekçesi
          <input className={inputStyle} name="reason" required maxLength={1000} />
        </label>
        <button className={buttonStyle} disabled={busy}>Fiyatı reddet</button>
      </form>
    </div>
  );
}

export default function PriceReviewPanel({ branchId }) {
  const admin = branchId == null;
  const base = admin ? '/admin/price-submissions' : '/owner/branches/' + branchId + '/price-submissions';
  const [filters, setFilters] = useState('');
  const [beforeId, setBeforeId] = useState(null);
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState({ items: [], next_before_id: null });
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState('');
  const busy = loading || deciding;

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams(filters);
    if (beforeId) params.set('before_id', beforeId);
    setLoading(true);
    setError('');
    const query = params.toString();
    accountRequest(base + (query ? '?' + query : '')).then((data) => {
      if (active) setPage(data);
    }).catch((failure) => {
      if (active) {
        setPage({ items: [], next_before_id: null });
        setError(failure.response?.data?.error || 'Fiyat kayıtları alınamadı.');
      }
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [base, filters, beforeId, revision]);

  async function decide(id, decision) {
    setDeciding(true);
    setError('');
    try {
      await accountRequest(base + '/' + id, 'PATCH', decision);
      setPage((previous) => ({ ...previous, items: previous.items.filter((item) => item.id !== id) }));
      setRevision((previous) => previous + 1);
    } catch (failure) {
      setError(failure.response?.data?.error || 'Fiyat kararı kaydedilemedi.');
    } finally {
      setDeciding(false);
    }
  }

  return (
    <section className="space-y-3 rounded-xl border border-slate-200 p-4">
      <h3 className="font-semibold">{admin ? 'Bekleyen fiyat kayıtları' : 'Şube fiyat geçmişi'}</h3>
      {admin && (
        <form className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(event) => {
          event.preventDefault();
          setFilters(new URLSearchParams(new FormData(event.currentTarget)).toString());
          setBeforeId(null);
          setRevision((previous) => previous + 1);
        }}>
          <label>Market<input className={inputStyle} name="market" maxLength={150} /></label>
          <label>Şube<input className={inputStyle} name="branch" maxLength={150} /></label>
          <label>Fiyat türü<select className={inputStyle} name="price_scope">
            <option value="">Tümü</option>
            {['BRANCH', 'ONLINE', 'CAMPAIGN'].map((type) => (
              <option key={type} value={type}>{priceScopeLabels[type]}</option>
            ))}
          </select></label>
          <label>Gönderim tarihi<input className={inputStyle} name="submitted_on" type="date" /></label>
          <button className={buttonStyle} disabled={busy}>Filtrele</button>
        </form>
      )}
      <button type="button" className={buttonStyle} disabled={busy}
        onClick={() => { setBeforeId(null); setRevision((previous) => previous + 1); }}>Fiyat kayıtlarını yenile</button>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {loading && <p role="status">Fiyat kayıtları yükleniyor.</p>}
      {!loading && !error && !page.items.length && <p>Gösterilecek fiyat kaydı yok.</p>}
      {!loading && page.items.map((item) => (
        <article className="space-y-2 rounded-xl border border-slate-200 p-3 text-sm" key={item.id}>
          <h4 className="font-semibold">{item.name} · {item.brand} · {item.quantity} {item.unit}</h4>
          <p>{item.market_name} · {item.branch_name}</p>
          <p>{formatPrice(item.price_minor / 100, item.currency)} · {priceScopeLabels[item.price_scope]} · {labels[item.status]}</p>
          <p>Gönderim {formatDate(item.created_at)} · {item.submission_source === 'IMPORT' ? 'Dosya aktarımı' : 'Tekli giriş'}</p>
          <p>Son geçerlilik tarihi {item.valid_until}</p>
          {item.reviewed_at && <p>Karar zamanı {formatDate(item.reviewed_at)}</p>}
          {item.rejection_reason && <p className="break-words text-red-700">Ret gerekçesi · {item.rejection_reason}</p>}
          {admin && <ReviewActions item={item} busy={busy} decide={decide} />}
        </article>
      ))}
      {page.next_before_id && <button type="button" className={buttonStyle} disabled={busy}
        onClick={() => setBeforeId(page.next_before_id)}>Sonraki fiyat kayıtları</button>}
    </section>
  );
}
