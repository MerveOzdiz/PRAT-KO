import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { getNearbyMarkets, getReverseGeocode, searchUnifiedMarkets } from './services/api';

vi.mock('./services/accounts', () => ({
  accountRequest: vi.fn().mockRejectedValue({ response: { status: 401 } }),
}));

vi.mock('./services/api', async (original) => ({
  ...await original(),
  getReverseGeocode: vi.fn().mockResolvedValue({ address: 'Test bölgesi' }),
  getNearbyMarkets: vi.fn().mockResolvedValue([]),
  searchUnifiedMarkets: vi.fn().mockResolvedValue({ results: [], total_pages: 0 }),
}));

beforeEach(() => {
  getReverseGeocode.mockResolvedValue({ address: 'Test bölgesi' });
  getNearbyMarkets.mockResolvedValue([]);
  searchUnifiedMarkets.mockResolvedValue({ results: [], total_pages: 0 });
});

afterEach(() => {
  vi.clearAllMocks();
  delete navigator.geolocation;
});

test('reports denied location without discovering markets at a fallback address', async () => {
  navigator.geolocation = { getCurrentPosition: (_, fail) => fail() };
  render(<App />);
  expect(await screen.findByText(/tarayıcıdan konum izni/i)).toBeInTheDocument();
  expect(getNearbyMarkets).not.toHaveBeenCalled();
});

test('uses the browser coordinates and sends the selected category and radius', async () => {
  navigator.geolocation = {
    getCurrentPosition: (success) => success({ coords: { latitude: 41, longitude: 29 } }),
  };
  render(<App />);
  await waitFor(() => expect(getNearbyMarkets).toHaveBeenCalledWith(41, 29));
  fireEvent.click(screen.getByRole('button', { name: /^Temel Gıda/ }));
  await waitFor(() => expect(searchUnifiedMarkets).toHaveBeenLastCalledWith(
    '', 41, 29, 3, 1, 'Temel Gıda', expect.any(AbortSignal), 'price',
  ));
  expect(await screen.findByText(/uygun sonuç bulunamadı/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '500 Metre' }));
  await waitFor(() => expect(searchUnifiedMarkets).toHaveBeenLastCalledWith(
    '', 41, 29, 0.5, 1, 'Temel Gıda', expect.any(AbortSignal), 'price',
  ));
});

test('the account view replaces all discovery controls and returning preserves the radius', async () => {
  navigator.geolocation = { getCurrentPosition: (_, fail) => fail() };
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: '500 Metre' }));
  fireEvent.click(screen.getByRole('button', { name: 'Hesap', exact: true }));
  expect(await screen.findByRole('form', { name: 'Giriş formu' })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Yakındaki Market Şubeleri' })).not.toBeInTheDocument();
  expect(screen.queryByPlaceholderText(/Hangi ürünü/)).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '500 Metre' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /^Temel Gıda/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Ana sayfa', exact: true }));
  expect(screen.getByRole('button', { name: '500 Metre', pressed: true })).toBeInTheDocument();
});
