import React, { useMemo } from 'react';

function CartDrawer({ cartItems, isOpen, onClose, onUpdateQty, onRemoveItem, onClearCart }) {
  // Compute store totals
  const storeComparison = useMemo(() => {
    if (!cartItems || cartItems.length === 0) return [];

    const stores = {};
    cartItems.forEach((cartItem) => {
      const storeName = cartItem.market_name || 'Diğer Market';
      if (!stores[storeName]) {
        stores[storeName] = {
          market_name: storeName,
          total: 0,
          itemCount: 0
        };
      }
      stores[storeName].total += cartItem.price * cartItem.quantity;
      stores[storeName].itemCount += cartItem.quantity;
    });

    const storeList = Object.values(stores).sort((a, b) => a.total - b.total);
    return storeList;
  }, [cartItems]);

  if (!isOpen) return null;

  const cheapestStore = storeComparison[0];
  const mostExpensiveStore = storeComparison[storeComparison.length - 1];
  const maxSavings = (cheapestStore && mostExpensiveStore)
    ? (mostExpensiveStore.total - cheapestStore.total)
    : 0;

  const totalCartPrice = cartItems.reduce((acc, i) => acc + (i.price * i.quantity), 0);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200 flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between">

        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-extrabold text-lg">
              🛒
            </span>
            <div>
              <h3 className="font-extrabold text-slate-800 text-base tracking-tight">Alışveriş Sepetim</h3>
              <span className="text-xs text-slate-500 font-medium">
                {cartItems.length} farklı ürün eklendi
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-200/80 hover:bg-slate-300 text-slate-600 flex items-center justify-center font-bold text-sm transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-grow overflow-y-auto p-5 space-y-4">
          {/* Smart Cart Savings Banner */}
          {storeComparison.length > 0 && (
            <div className="bg-gradient-to-r from-emerald-600 to-green-500 text-white rounded-2xl p-4 shadow-md space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-extrabold tracking-wider uppercase bg-white/20 px-2.5 py-0.5 rounded-full">
                  🏆 En Ucuz Toplam Sepet
                </span>
                {maxSavings > 0 && (
                  <span className="text-xs font-black bg-emerald-950/40 text-emerald-200 px-2 py-0.5 rounded-full">
                    ₺{maxSavings.toFixed(2)} Tasarruf!
                  </span>
                )}
              </div>
              <div className="text-sm font-semibold">
                Bu sepet en uygun <strong className="underline decoration-emerald-300 font-extrabold">{cheapestStore?.market_name}</strong> şubesinde:
              </div>
              <div className="text-2xl font-black tracking-tight">
                ₺{cheapestStore?.total.toFixed(2)}
              </div>
            </div>
          )}

          {/* Cart Items List */}
          {cartItems.length === 0 ? (
            <div className="text-center py-16 space-y-3">
              <span className="text-5xl block">🛒</span>
              <p className="text-slate-500 font-semibold text-sm">Sepetiniz şu anda boş.</p>
              <p className="text-xs text-slate-400">Ürünlerin üzerindeki "+ Sepete Ekle" butonuna basarak sepetinizi doldurabilirsiniz.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {cartItems.map((item, idx) => (
                <div key={item.product_id || idx} className="flex items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white transition-colors shadow-sm">
                  <div className="flex-grow min-w-0">
                    <h5 className="font-bold text-slate-800 text-xs truncate">{item.product_name}</h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                        {item.market_name}
                      </span>
                      <span className="text-xs font-extrabold text-slate-900">
                        ₺{item.price.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Qty controls */}
                  <div className="flex items-center gap-2">
                    <div className="flex items-center border border-slate-200 rounded-lg bg-white overflow-hidden shadow-inner">
                      <button
                        onClick={() => onUpdateQty(item.product_id, item.quantity - 1)}
                        className="px-2 py-0.5 text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors"
                      >
                        -
                      </button>
                      <span className="px-2 text-xs font-extrabold text-slate-800">{item.quantity}</span>
                      <button
                        onClick={() => onUpdateQty(item.product_id, item.quantity + 1)}
                        className="px-2 py-0.5 text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors"
                      >
                        +
                      </button>
                    </div>

                    <button
                      onClick={() => onRemoveItem(item.product_id)}
                      className="text-slate-400 hover:text-rose-600 text-xs font-bold p-1 transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Checkout Bar */}
        {cartItems.length > 0 && (
          <div className="p-5 border-t border-slate-200 bg-white space-y-3">
            <div className="flex items-center justify-between text-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Toplam Sepet Tutarı:</span>
              <span className="text-2xl font-black text-emerald-600 tracking-tight">₺{totalCartPrice.toFixed(2)}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onClearCart}
                className="w-1/3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors"
              >
                Sepeti Temizle
              </button>
              <button
                onClick={() => alert("Sipariş modülü başarıyla aktifleştirildi!")}
                className="w-2/3 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs rounded-xl shadow-md shadow-emerald-600/30 transition-all active:scale-95 flex items-center justify-center gap-1.5"
              >
                <span>🚀</span>
                <span>Sepeti Tamamla</span>
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default CartDrawer;
