import React, { useState } from 'react';
import SearchBar from '../SearchBar/SearchBar';
import CategoryNav from '../CategoryNav/CategoryNav';

function Header({ categories, userAddress, onSearch, onSelectCategory, onAccount, onHome, accountOpen }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/90 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-3">
        {/* Logo */}
        <button type="button" aria-label="Pratiko ana sayfa" className="flex items-center gap-2.5 text-left group flex-shrink-0"
          onClick={() => { setMobileMenuOpen(false); onHome(); }}>
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center text-white font-black text-lg sm:text-xl shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            ✓
          </div>
          <div>
            <span className="text-xl sm:text-2xl font-extrabold bg-gradient-to-r from-emerald-600 to-green-500 bg-clip-text text-transparent tracking-tight">
              Pratiko
            </span>
            <span className="block text-[9px] sm:text-[10px] uppercase font-bold tracking-widest text-slate-400 -mt-1">
              Market & Fiyat
            </span>
          </div>
        </button>

        {!accountOpen && <>
          {/* Search Bar (Desktop) */}
          <div className="hidden md:block flex-grow max-w-xl mx-4">
            <SearchBar onSearch={onSearch} />
          </div>

          {/* Address Pill (Desktop) */}
          <div className="hidden lg:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100/90 border border-slate-200 text-xs font-medium text-slate-700 max-w-xs truncate shadow-inner">
            <span className="flex-shrink-0 text-emerald-600 animate-pulse">📍</span>
            <span className="truncate">{userAddress || 'Konum alınıyor...'}</span>
          </div>

        </>}

        <button type="button" onClick={() => { setMobileMenuOpen(false); (accountOpen ? onHome : onAccount)(); }}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
          {accountOpen ? 'Ana sayfa' : 'Hesap'}
        </button>

        {/* Mobile Menu Toggle Button */}
        {!accountOpen && <button type="button" aria-label="Arama menüsü" aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
        >
          {mobileMenuOpen ? '✕' : '☰'}
        </button>}
      </div>

      {/* Mobile Search & Address Drawer */}
      {!accountOpen && mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 p-4 bg-white space-y-3 shadow-lg">
          <SearchBar onSearch={onSearch} />
          {userAddress && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
              <span>📍 Konum:</span>
              <span className="truncate">{userAddress}</span>
            </div>
          )}
        </div>
      )}

      {/* Category Nav Bar */}
      {!accountOpen && <CategoryNav categories={categories} onSelectCategory={onSelectCategory} />}
    </header>
  );
}

export default Header;
