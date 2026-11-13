import React, { useEffect, useState } from 'react';
import { getCategories } from '../../services/api';
import { accountRequest } from '../../services/accounts';
import PriceReviewPanel from './PriceReviewPanel';

const inputStyle = 'w-full rounded-lg border border-slate-300 p-2';
const buttonStyle = 'rounded-lg bg-emerald-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60';
const scopes = { BRANCH: 'Şube fiyatı', ONLINE: 'Online fiyat', CAMPAIGN: 'Kampanya fiyatı' };

function OwnerSubmissionForm({ branchId }) {
  const [categories, setCategories] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const base = '/owner/branches/' + branchId;

  useEffect(() => {
    let active = true;
    getCategories().then((items) => {
      if (active) setCategories(items.flatMap((item) => [
        item, ...item.sub_categories.map((child) => ({ ...child, name: item.name + ' / ' + child.name })),
      ]));
    }).catch(() => {
      if (active) setError('Kategoriler alınamadı.');
    });
    return () => { active = false; };
  }, []);

  async function run(action) {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      await action();
    } catch (failure) {
      setError(failure.response?.data?.error || 'İşlem tamamlanamadı.');
    } finally {
      setBusy(false);
    }
  }

  function fileData() {
    const data = new FormData();
    data.append('file', file);
    return data;
  }

  function reviewFile() {
    setPreview(null);
    run(async () => setPreview(await accountRequest(base + '/imports/preview', 'POST', fileData())));
  }

  function sendFile() {
    run(async () => {
      const data = fileData();
      data.append('token', preview.token);
      data.append('accept_partial', String(preview.invalid_rows.length > 0));
      const result = await accountRequest(base + '/imports/commit', 'POST', data);
      setPreview(null);
      setMessage(result.already_imported
        ? 'Bu dosya bu şubeye daha önce gönderilmiş.'
        : result.batch.accepted_rows + ' fiyat kaydı onay bekliyor.');
    });
  }

  return (
    <div className="space-y-5">
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {message && <p role="status" className="text-sm text-emerald-800">{message}</p>}
      <form className="space-y-3" onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const data = Object.fromEntries(new FormData(form));
        run(async () => {
          await accountRequest(base + '/products', 'POST', data);
          form.reset();
          setMessage('Ürün ve fiyat onay için gönderildi.');
        });
      }}>
        <h4 className="font-semibold">Tekli ürün ve fiyat girişi</h4>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label>Ürün adı<input name="name" className={inputStyle} required maxLength={100} /></label>
          <label>Marka<input name="brand" className={inputStyle} required maxLength={100} /></label>
          <label>Miktar / gramaj<input name="quantity" className={inputStyle} required inputMode="decimal" /></label>
          <label>Birim<select name="unit" className={inputStyle}>
            {['g', 'kg', 'ml', 'l', 'adet'].map((unit) => <option key={unit}>{unit}</option>)}
          </select></label>
          <label>Kategori<select name="category_id" className={inputStyle} required>
            <option value="">Kategori seçin</option>
            {categories.map((category) => <option key={category.id} value={category.id}>
              {category.name} ({category.id})
            </option>)}
          </select></label>
          <label>Fiyat<input name="price" className={inputStyle} required inputMode="decimal" /></label>
          <label>Para birimi<select name="currency" className={inputStyle}>
            {['TRY', 'EUR', 'USD'].map((currency) => <option key={currency}>{currency}</option>)}
          </select></label>
          <label>Fiyat türü<select name="price_scope" className={inputStyle}>
            {Object.entries(scopes).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
          <label>Son geçerlilik tarihi<input name="valid_until" type="date" className={inputStyle} required /></label>
        </div>
        <button className={buttonStyle} disabled={busy}>Onaya gönder</button>
      </form>
      <section className="space-y-3 border-t border-slate-200 pt-4" aria-labelledby="import-heading">
        <h4 id="import-heading" className="font-semibold">CSV / Excel aktarımı</h4>
        <p className="text-sm text-slate-600">UTF-8 CSV veya tek sayfalı XLSX yükleyin. En çok 1 MiB ve 500 veri satırı.</p>
        <code className="block break-all text-xs text-slate-600">
          name, brand, quantity, unit, category_id, price, currency, price_scope, valid_until
        </code>
        <p className="text-xs text-slate-600">
          Kategori numaraları üstteki seçim alanında görünür. Fiyat türü BRANCH, ONLINE veya CAMPAIGN,
          tarih biçimi YYYY-AA-GG olmalı.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <label>CSV veya XLSX dosyası<input className={inputStyle} type="file" accept=".csv,.xlsx" disabled={busy}
            onChange={(event) => {
              setFile(event.target.files[0] || null);
              setPreview(null);
              setError('');
              setMessage('');
            }} /></label>
          <button type="button" className={buttonStyle} disabled={!file || busy} onClick={reviewFile}>Önizle</button>
        </div>
        {preview?.already_imported && <p role="status">Bu dosya bu şubeye daha önce gönderilmiş.</p>}
        {preview && !preview.already_imported && (
          <div className="space-y-3">
            <h5 className="font-semibold">Geçerli satırlar ({preview.valid_rows.length})</h5>
            <ul className="max-h-52 list-disc overflow-auto pl-5 text-sm">
              {preview.valid_rows.map(({ row, data }) => (
                <li key={row}>
                  {row}. {data.name} · {data.brand} · {data.quantity} {data.unit} ·{' '}
                  {(data.price_minor / 100).toFixed(2)} {data.currency} · {scopes[data.price_scope]} · {data.valid_until}
                </li>
              ))}
            </ul>
            <h5 className="font-semibold">Hatalı satırlar ({preview.invalid_rows.length})</h5>
            <ul className="max-h-52 list-disc overflow-auto pl-5 text-sm text-red-700">
              {preview.invalid_rows.map(({ row, error: reason }) => <li key={row}>{row}. {reason}</li>)}
            </ul>
            <button type="button" className={buttonStyle} disabled={busy || !preview.valid_rows.length} onClick={sendFile}>
              {preview.invalid_rows.length
                ? 'Yalnızca ' + preview.valid_rows.length + ' geçerli satırı onaya gönder'
                : 'Tüm geçerli satırları onaya gönder'}
            </button>
          </div>
        )}
      </section>
      <button type="button" className={buttonStyle} onClick={() => setShowHistory(!showHistory)}>
        {showHistory ? 'Fiyat geçmişini gizle' : 'Fiyat geçmişini göster'}
      </button>
      {showHistory && <PriceReviewPanel branchId={branchId} />}
    </div>
  );
}

export default function OwnerCatalogPanel({ branches }) {
  const [selectedId, setSelectedId] = useState(null);
  const branch = branches.find((item) => item.id === selectedId) || branches[0];
  return (
    <section className="space-y-3 rounded-xl border border-slate-200 p-4">
      <h3 className="font-semibold">Yetkili olduğunuz şubeler</h3>
      {branch ? (
        <>
          <label>Şube<select className={inputStyle} value={branch.id}
            onChange={(event) => setSelectedId(Number(event.target.value))}>
            {branches.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.address}</option>)}
          </select></label>
          <OwnerSubmissionForm key={branch.id} branchId={branch.id} />
        </>
      ) : <p>Aktif şube yetkiniz yok.</p>}
    </section>
  );
}
