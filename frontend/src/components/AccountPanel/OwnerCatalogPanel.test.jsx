import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import OwnerCatalogPanel from './OwnerCatalogPanel';
import { getCategories } from '../../services/api';
import { accountRequest } from '../../services/accounts';

vi.mock('../../services/api', () => ({ getCategories: vi.fn() }));
vi.mock('../../services/accounts', () => ({ accountRequest: vi.fn() }));

test('shows row errors and commits the valid subset after the owner confirms', async () => {
  getCategories.mockResolvedValue([{ id: 1, name: 'Temel Gıda', sub_categories: [] }]);
  accountRequest.mockResolvedValueOnce({
    token: 'preview-token',
    valid_rows: [{ row: 2, data: {
      name: 'Test Ürünü', brand: 'Test', quantity: '500', unit: 'g',
      price_minor: 1200, currency: 'TRY', price_scope: 'BRANCH', valid_until: '2099-01-01',
    } }],
    invalid_rows: [{ row: 3, error: 'Fiyat sıfırdan büyük olmalı.' }],
  }).mockResolvedValueOnce({ batch: { accepted_rows: 1 }, already_imported: false });
  render(<OwnerCatalogPanel branches={[{ id: 7, name: 'Şube A', address: 'Test adresi' }]} />);
  await screen.findByRole('option', { name: 'Temel Gıda (1)' });
  const file = new File(['test'], 'products.csv', { type: 'text/csv' });
  fireEvent.change(screen.getByLabelText('CSV veya XLSX dosyası'), { target: { files: [file] } });
  fireEvent.click(screen.getByRole('button', { name: 'Önizle' }));
  expect(await screen.findByText(/Fiyat sıfırdan büyük olmalı/)).toBeInTheDocument();
  expect(screen.getByText(/Test Ürünü/)).toBeInTheDocument();
  expect(accountRequest).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Yalnızca 1 geçerli satırı onaya gönder' }));
  await waitFor(() => expect(accountRequest).toHaveBeenCalledTimes(2));
  const [path, method, data] = accountRequest.mock.calls[1];
  expect([path, method, data.get('token'), data.get('accept_partial')]).toEqual([
    '/owner/branches/7/imports/commit', 'POST', 'preview-token', 'true',
  ]);
  expect(await screen.findByText('1 fiyat kaydı onay bekliyor.')).toBeInTheDocument();
});
