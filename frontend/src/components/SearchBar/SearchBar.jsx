import React, { useState } from 'react';

function SearchBar({ onSearch }) {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchTerm);
    }
  };

  return (
    <form className="relative flex items-center w-full" onSubmit={handleSubmit}>
      <div className="absolute left-4 text-slate-400 pointer-events-none">
        🔍
      </div>
      <input
        type="text"
        placeholder="Hangi ürünü arıyorsunuz? (ör. Nutella, Süt, Yağ)..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full pl-11 pr-24 py-2.5 bg-slate-100/80 border border-slate-200 rounded-full text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all shadow-inner"
      />
      <button
        type="submit"
        className="absolute right-1.5 px-5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-full shadow-sm shadow-emerald-600/30 transition-all active:scale-95"
      >
        Ara
      </button>
    </form>
  );
}

export default SearchBar;
