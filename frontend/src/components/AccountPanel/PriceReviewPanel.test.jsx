import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PriceReviewPanel from './PriceReviewPanel';
import { accountRequest } from '../../services/accounts';

vi.mock('../../services/accounts', () => ({ accountRequest: vi.fn() }));

const item = {
  id: 12, name: 'Test Pirinç', brand: 'Test Marka', quantity: '500', unit: 'g',
  market_name: 'Test Market', branch_name: 'Şube A', price_minor: 1540,
  currency: 'EUR', price_scope: 'ONLINE', status: 'PENDING', submission_source: 'IMPORT',
  created_at: '2026-11-05 12:00:00', valid_until: '2099-01-01',
};

test('filters the admin queue and submits the rejection reason', async () => {
  let pending = [item];
  accountRequest.mockImplementation(async (_, method) => {
    if (method === 'PATCH') {
      pending = [];
      return {};
    }
    return { items: pending, next_before_id: null };
  });
  render(<PriceReviewPanel />);
  expect(await screen.findByText(/Dosya aktarımı/)).toBeInTheDocument();
  expect(screen.getByText(/15.40 EUR/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Market'), { target: { value: 'Test Market' } });
  fireEvent.change(screen.getByLabelText('Fiyat türü'), { target: { value: 'ONLINE' } });
  fireEvent.click(screen.getByRole('button', { name: 'Filtrele' }));
  await waitFor(() => expect(accountRequest.mock.lastCall[0]).toContain('market=Test+Market'));
  await screen.findByRole('button', { name: 'Fiyatı reddet' });
  fireEvent.change(screen.getByLabelText('Fiyat ret gerekçesi'), { target: { value: 'Etiket okunamadı.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Fiyatı reddet' }));
  await waitFor(() => expect(accountRequest).toHaveBeenCalledWith(
    '/admin/price-submissions/12', 'PATCH', { status: 'REJECTED', rejection_reason: 'Etiket okunamadı.' },
  ));
  expect(await screen.findByText('Gösterilecek fiyat kaydı yok.')).toBeInTheDocument();
});

test('shows the branch rejection reason in owner history', async () => {
  accountRequest.mockResolvedValue({
    items: [{ ...item, status: 'REJECTED', rejection_reason: 'Etiket okunamadı.',
      reviewed_at: '2026-11-05 13:00:00' }],
    next_before_id: null,
  });
  render(<PriceReviewPanel branchId={7} />);
  expect(await screen.findByText(/Etiket okunamadı/)).toBeInTheDocument();
  expect(screen.getByText(/Reddedildi/)).toBeInTheDocument();
  expect(accountRequest).toHaveBeenLastCalledWith('/owner/branches/7/price-submissions');
  expect(screen.queryByRole('button', { name: 'Fiyatı onayla' })).not.toBeInTheDocument();
});
