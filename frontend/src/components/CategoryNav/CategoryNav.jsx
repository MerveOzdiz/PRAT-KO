import React, { useState } from 'react';

function CategoryNav({ categories, onSelectCategory }) {
  const [openCategoryId, setOpenCategoryId] = useState(null);

  const handleCategoryClick = (catName) => {
    if (onSelectCategory) {
      onSelectCategory(catName);
    }
  };

  const handleSubCategoryClick = (e, subName) => {
    e.preventDefault();
    e.stopPropagation();
    setOpenCategoryId(null);
    if (onSelectCategory) {
      onSelectCategory(subName);
    }
  };

  return (
    <div className="bg-slate-50 border-t border-slate-200/80 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-1 py-1 overflow-x-visible flex-wrap">
          {categories.map((cat) => {
            const isOpen = openCategoryId === cat.id;
            const hasSubs = cat.sub_categories && cat.sub_categories.length > 0;

            return (
              <div
                key={cat.id}
                className="relative my-1"
                onMouseEnter={() => setOpenCategoryId(cat.id)}
                onMouseLeave={() => setOpenCategoryId(null)}
              >
                <button
                  onClick={() => handleCategoryClick(cat.name)}
                  className={`flex items-center gap-1.5 pl-3.5 pr-6 py-2 rounded-xl text-xs font-semibold transition-all ${
                    isOpen
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                      : 'text-slate-700 hover:text-emerald-700 hover:bg-emerald-50/80'
                  }`}
                >
                  <span>{cat.name}</span>

                </button>

                {hasSubs && (
                  <button type="button" aria-label={'Alt kategoriler · ' + cat.name}
                    aria-expanded={isOpen} onClick={() => setOpenCategoryId(isOpen ? null : cat.id)}
                    className="absolute right-0 top-0 h-full px-1 text-xs text-slate-500">▾</button>
                )}

                {/* Subcategories Dropdown */}
                {isOpen && hasSubs && (
                  <div className="absolute top-full left-0 mt-1.5 w-64 bg-white rounded-2xl shadow-2xl border border-slate-200/90 py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                    <div className="max-h-64 overflow-y-auto">
                      {cat.sub_categories.map((sub) => (
                        <a
                          key={sub.id}
                          href={`#${sub.id}`}
                          onClick={(e) => handleSubCategoryClick(e, sub.name)}
                          className="flex items-center justify-between px-4 py-2 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition-colors group"
                        >
                          <span>{sub.name}</span>
                          <span className="text-[10px] text-slate-300 group-hover:text-emerald-500 transition-colors">→</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default CategoryNav;
