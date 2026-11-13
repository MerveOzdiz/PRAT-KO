import React, { useEffect, useState } from 'react';
import { accountRequest } from '../../services/accounts';
import OwnerCatalogPanel from './OwnerCatalogPanel';
import PriceReviewPanel from './PriceReviewPanel';

const inputStyle = 'w-full rounded-lg border border-slate-300 p-2';
const buttonStyle = 'rounded-lg bg-emerald-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60';
const applicationFields = [
  ['business_name', 'İşletme adı', 150],
  ['branch_name', 'Şube adı', 150],
  ['address', 'Şube adresi', 255],
  ['google_place_id', 'Google Place ID', 100],
  ['latitude', 'Enlem'],
  ['longitude', 'Boylam'],
  ['verification_note', 'İşletmeyi ve şubeyi doğrulama bilgisi', 1000],
];
const statusLabels = { PENDING: 'Bekliyor', APPROVED: 'Onaylandı', REJECTED: 'Reddedildi' };
const roleLabels = { USER: 'Kullanıcı', OWNER: 'Market sahibi', ADMIN: 'Yönetici' };

function ApplicationForm({ markets, disabled, onSubmit }) {
  const [draft, setDraft] = useState({});
  const selectMarket = (placeId) => {
    const market = markets.find((item) => item.google_place_id === placeId);
    if (!market) return;
    setDraft((previous) => ({
      ...previous,
      google_place_id: placeId,
      branch_name: market.name,
      address: market.address,
      latitude: market.latitude,
      longitude: market.longitude,
    }));
  };

  return (
    <form className="space-y-3" onSubmit={(event) => {
      event.preventDefault();
      onSubmit({
        ...draft,
        latitude: Number(draft.latitude),
        longitude: Number(draft.longitude),
      });
    }}>
      <h3 className="font-semibold">Market sahipliği başvurusu</h3>
      {markets.some((market) => market.google_place_id) && (
        <label className="block">
          Yakındaki şubelerden doldur
          <select className={inputStyle} onChange={(event) => selectMarket(event.target.value)}>
            <option value="">Şube seçin</option>
            {markets.filter((market) => market.google_place_id).map((market) => (
              <option key={market.id} value={market.google_place_id}>{market.name} · {market.address}</option>
            ))}
          </select>
        </label>
      )}
      <p className="text-sm text-slate-600">
        Şube bilgilerini doğrulayın. Doğrulama alanına işletmenin herkese açık sitesi veya
        yöneticinin şubeyi teyit edebileceği bir açıklama yazın.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {applicationFields.map(([name, label, maxLength]) => (
          <label key={name}>
            {label}
            <input className={inputStyle} required maxLength={maxLength} value={draft[name] ?? ''}
              type={maxLength ? 'text' : 'number'} step={maxLength ? undefined : 'any'}
              onChange={(event) => setDraft({ ...draft, [name]: event.target.value })} />
          </label>
        ))}
      </div>
      <button className={buttonStyle} disabled={disabled}>Başvuru gönder</button>
    </form>
  );
}

function AdminQueue({ applications, disabled, onDecision }) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold">Bekleyen sahiplik başvuruları</h3>
      {!applications.length && <p>Bekleyen başvuru yok.</p>}
      {applications.map((item) => (
        <article className="space-y-2 rounded-xl border border-slate-200 p-3" key={item.id}>
          <h4 className="font-semibold">{item.business_name} · {item.branch_name}</h4>
          <p>{item.address} · {item.latitude}, {item.longitude}</p>
          <p>Başvuran: {item.applicant_email}</p>
          <p className="break-all">Google Place ID: {item.google_place_id}</p>
          <p className="break-words">Doğrulama bilgisi: {item.verification_note}</p>
          <button type="button" className={buttonStyle} disabled={disabled}
            onClick={() => onDecision(item.id, { status: 'APPROVED' })}>Onayla</button>
          <form className="flex flex-wrap items-end gap-2" onSubmit={(event) => {
            event.preventDefault();
            const rejection_reason = new FormData(event.currentTarget).get('reason');
            onDecision(item.id, { status: 'REJECTED', rejection_reason });
          }}>
            <label>Ret gerekçesi
              <input className={inputStyle} name="reason" required maxLength={1000} />
            </label>
            <button className={buttonStyle} disabled={disabled}>Reddet</button>
          </form>
        </article>
      ))}
    </div>
  );
}

async function loadPanel() {
  const user = await accountRequest('/auth/me').catch((failure) => {
    if (failure.response?.status === 401) return null;
    throw failure;
  });
  if (!user) return null;
  if (user.role === 'ADMIN') {
    return { user, applications: await accountRequest('/admin/ownership-applications'), branches: [] };
  }
  const [applications, branches] = await Promise.all([
    accountRequest('/ownership-applications/mine'),
    user.role === 'OWNER' ? accountRequest('/owner/branches') : [],
  ]);
  return { user, applications, branches };
}

export default function AccountPanel({ markets }) {
  const [panel, setPanel] = useState(null);
  const [registering, setRegistering] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    loadPanel().then((data) => {
      if (active) setPanel(data);
    }).catch((failure) => {
      if (active) {
        setError(failure.response?.data?.error || (!failure.response || failure.response.status >= 500
          ? 'Pratiko sunucusuna ulaşılamadı. Backend çalışıyorsa sayfayı yenileyin.'
          : 'Hesap bilgileri alınamadı.'));
      }
    }).finally(() => {
      if (active) setBusy(false);
    });
    return () => { active = false; };
  }, []);

  const run = async (action, success = '') => {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      await action();
      setMessage(success);
    } catch (failure) {
      setError(failure.response?.data?.error || 'İşlem tamamlanamadı.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="account-heading"
      className={`mx-auto space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7 ${panel ? '' : 'max-w-lg'}`}>
      <div className={panel ? '' : 'rounded-xl bg-emerald-50 px-5 py-6'}>
        <h1 id="account-heading" className="text-2xl font-bold text-slate-800">
          {panel ? 'Hesap ve market sahipliği' : 'Pratiko hesabı'}
        </h1>
        {!panel && (
          <p className="mt-2 text-sm text-slate-600">
            Hesabınıza giriş yapın veya yeni bir hesap oluşturun.
          </p>
        )}
      </div>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      {message && <p role="status" className="text-emerald-800">{message}</p>}
      {!panel ? (
        <>
          <div role="group" aria-label="Hesap işlemi" className="grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 text-sm font-semibold">
            {[[false, 'Giriş yap'], [true, 'Hesap oluştur']].map(([value, label]) => (
              <button key={label} type="button" aria-pressed={registering === value}
                className={`rounded-lg px-2 py-2 ${registering === value ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-600'}`}
                onClick={() => { setRegistering(value); setError(''); }}>{label}</button>
            ))}
          </div>
          <form aria-label={registering ? "Hesap oluşturma formu" : "Giriş formu"} className="space-y-4" onSubmit={(event) => {
            event.preventDefault();
            const data = Object.fromEntries(new FormData(event.currentTarget));
            run(async () => {
              await accountRequest(registering ? '/auth/register' : '/auth/login', 'POST', data);
              setRegistering(false);
              setPanel(await loadPanel());
            });
          }}>
            <label className="block">E-posta<input className={inputStyle} name="email" type="email" autoComplete="email" required /></label>
            <label className="block">Parola<input className={inputStyle} name="password" type="password" required
              minLength={12} maxLength={128} autoComplete={registering ? 'new-password' : 'current-password'} /></label>
            <button className={`${buttonStyle} w-full`} disabled={busy}>{registering ? 'Kayıt ol' : 'Giriş yap'}</button>
          </form>
        </>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <p>{panel.user.email} · {roleLabels[panel.user.role]}</p>
            <button type="button" disabled={busy} onClick={() => run(async () => setPanel(await loadPanel()))}>Yenile</button>
            <button type="button" disabled={busy} onClick={() => run(async () => {
              await accountRequest('/auth/logout', 'POST', {});
              setPanel(null);
            })}>Çıkış yap</button>
          </div>
          {panel.user.role === 'ADMIN' ? (
            <>
              <AdminQueue applications={panel.applications} disabled={busy} onDecision={(id, decision) => run(async () => {
                await accountRequest('/admin/ownership-applications/' + id, 'PATCH', decision);
                setPanel(await loadPanel());
              }, 'Başvuru kararı kaydedildi.')} />
              <PriceReviewPanel />
            </>
          ) : (
            <>
              {panel.user.role === 'OWNER' && <OwnerCatalogPanel branches={panel.branches} />}
              <ApplicationForm markets={markets} disabled={busy} onSubmit={(data) => run(async () => {
                await accountRequest('/ownership-applications', 'POST', data);
                setPanel(await loadPanel());
              }, 'Başvurunuz incelemeye alındı.')} />
              <h3 className="font-semibold">Başvurularım</h3>
              {!panel.applications.length && <p>Henüz başvurunuz yok.</p>}
              <ul className="list-disc pl-5">
                {panel.applications.map((item) => (
                  <li key={item.id}>
                    {item.branch_name} · {statusLabels[item.status]}
                    {item.rejection_reason && <p className="break-words">{item.rejection_reason}</p>}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  );
}
