import { fireEvent, render, screen, within } from '@testing-library/react';
import ProductResults from './ProductResults';

test('shows campaign prices separately from normal prices and stock filters', () => {
  const base = {
    price_status: 'AVAILABLE', is_in_stock: false, stock_status: 'UNKNOWN',
    market_name: 'Test Market',
  };
  render(<ProductResults query="yağ" results={[
    { ...base, product_id: 'campaign', product_name: 'Katalog ürünü', price: 100,
      price_scope: 'CATALOG', is_cheapest: true },
    { ...base, product_id: 'owner-campaign', product_name: 'Sahip kampanyası', price: 120,
      price_scope: 'CAMPAIGN', is_cheapest: true, source: 'MARKET_OWNER',
      brand: 'Test', quantity: '500', unit: 'g' },
    { ...base, product_id: 'normal', product_name: 'Normal ürün', price: 150,
      price_scope: 'ONLINE', is_in_stock: true },
  ]} />);

  const campaigns = screen.getByRole('region', { name: 'Kampanya katalogları' });
  expect(within(campaigns).getByText('Katalog ürünü')).toBeInTheDocument();
  expect(within(campaigns).getByText('Sahip kampanyası')).toBeInTheDocument();
  expect(within(campaigns).getByText(/Market sahibi bildirimi/)).toBeInTheDocument();
  expect(within(campaigns).queryByText('Normal ürün')).not.toBeInTheDocument();
  expect(within(campaigns).queryByText(/EN UCUZ GERÇEK FİYAT/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Sadece Stokta Olanlar' }));
  expect(within(campaigns).getByText('₺100.00')).toBeInTheDocument();
  expect(screen.getByText('Normal ürün')).toBeInTheDocument();
});
