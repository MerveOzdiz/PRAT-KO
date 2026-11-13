import React, { useEffect, useState } from 'react';
import Header from './components/Header/Header';
import AccountPanel from './components/AccountPanel/AccountPanel';
import DistanceFilter from './components/DistanceFilter/DistanceFilter';
import MarketGrid from './components/MarketGrid/MarketGrid';
import ProductResults from './components/ProductResults/ProductResults';
import ProductDetailModal from './components/ProductDetailModal/ProductDetailModal';
import { DEFAULT_CATEGORIES } from './constants/categories';
import { getReverseGeocode, getNearbyMarkets, searchUnifiedMarkets, marketRequestError } from './services/api';

function App() {
  const [markets, setMarkets] = useState([]);
  const [accountOpen, setAccountOpen] = useState(false);
  const [coords, setCoords] = useState(null);
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [radius, setRadius] = useState(3);
  const [search, setSearch] = useState(null);
  const [results, setResults] = useState(null);
  const [searchError, setSearchError] = useState('');
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('price');
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    let active = true;
    const fail = () => {
      if (active) {
        setError('Konum alınamadı. Tarayıcıdan konum izni verip sayfayı yenileyin.');
        setAddress('Konum alınamadı');
        setLoading(false);
      }
    };
    if (!navigator.geolocation) {
      fail();
      return;
    }
    navigator.geolocation.getCurrentPosition(({ coords: position }) => {
      if (!active) return;
      const { latitude, longitude } = position;
      setCoords({ latitude, longitude });
      setAddress('Konum alındı');
      getReverseGeocode(latitude, longitude).then((data) => {
        if (active && data.address) setAddress(data.address);
      }).catch(() => {});
      getNearbyMarkets(latitude, longitude).then((data) => {
        if (active) setMarkets(data);
      }).catch((failure) => {
        if (active) setError(marketRequestError(failure, 'Market keşfi tamamlanamadı.'));
      }).finally(() => {
        if (active) setLoading(false);
      });
    }, fail, { timeout: 10000, maximumAge: 60000 });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!search || !coords) return;
    const controller = new AbortController();
    searchUnifiedMarkets(search.query, coords.latitude, coords.longitude,
      radius, page, search.category, controller.signal, sortBy).then((data) => {
      if (!controller.signal.aborted) setResults(data);
    }).catch((failure) => {
      if (!controller.signal.aborted) setSearchError(marketRequestError(failure, 'Arama tamamlanamadı. Tekrar deneyin.'));
    });
    return () => controller.abort();
  }, [search, coords, radius, page, sortBy]);

  const clearResults = () => {
    setResults(null);
    setSearchError('');
  };

  const startSearch = (query, category) => {
    clearResults();
    setPage(1);
    setDetail(null);
    setSearch(query || category ? { query, category } : null);
  };

  const selectRadius = (value) => {
    if (value === radius) return;
    clearResults();
    setPage(1);
    setRadius(value);
  };

  const changeSort = (value) => {
    if (value === sortBy) return;
    clearResults();
    setPage(1);
    setSortBy(value);
  };

  const changePage = (value) => {
    clearResults();
    setPage(value);
  };

  const visibleMarkets = markets.filter((market) => market.distance_km <= radius);
  const searchLabel = search?.query || search?.category;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header categories={DEFAULT_CATEGORIES} userAddress={address}
        accountOpen={accountOpen} onHome={() => setAccountOpen(false)}
        onAccount={() => { setDetail(null); setAccountOpen(true); }}
        onSearch={(query) => startSearch(query.trim(), null)}
        onSelectCategory={(category) => startSearch('', category)} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-grow w-full">
        {accountOpen ? <AccountPanel markets={markets} /> : (
          <div className="flex flex-col md:flex-row gap-6 items-start">
            <DistanceFilter selectedDistance={radius} onSelectDistance={selectRadius} />
            <div className="flex-grow w-full space-y-5">
              <div className="flex items-center justify-between bg-white rounded-2xl p-4 border border-slate-200/80 shadow-sm">
                <h2 className="text-lg font-extrabold text-slate-800 tracking-tight flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
                  <span>{searchLabel ? 'Arama ve Kategori · ' + searchLabel : 'Yakındaki Market Şubeleri'}</span>
                </h2>
              </div>
              {search ? (
                <>
                  <ProductResults query={searchLabel} results={results?.results || []}
                    sortBy={sortBy} onSort={changeSort}
                    loading={!results && !searchError && (loading || !!coords)}
                    error={searchError || (!coords ? error : '')}
                    onClearSearch={() => startSearch('', null)} onOpenDetail={setDetail} />
                  {results?.total_pages > 1 && (
                    <nav aria-label="Arama sonuçları sayfaları" className="flex justify-center gap-4">
                      <button disabled={page === 1} onClick={() => changePage(page - 1)}>Önceki</button>
                      <span>{page} / {results.total_pages}</span>
                      <button disabled={page === results.total_pages} onClick={() => changePage(page + 1)}>Sonraki</button>
                    </nav>
                )}
              </>
            ) : <MarketGrid markets={visibleMarkets} loading={loading} error={error} />}
          </div>
        </div>
        )}
      </main>

      <ProductDetailModal item={detail} isOpen={!!detail} onClose={() => setDetail(null)} />
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500 font-medium">
        © 2026 Pratiko · Konum Tabanlı Market ve Fiyat Karşılaştırma · Konum verisi: Google Maps
      </footer>
    </div>
  );
}

export default App;
