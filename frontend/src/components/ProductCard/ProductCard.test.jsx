import { render, screen } from '@testing-library/react';
import ProductCard from './ProductCard';

test('renders ProductCard with market name and price', () => {
  const dummyProduct = {
    market_name: 'Migros Jet',
    branch_name: 'Kadıköy Moda Şubesi',
    distance_meters: 430,
    product_name: 'Nutella Fındık Kreması 750 gr',
    price: 219.00,
    is_in_stock: true,
    price_status: 'AVAILABLE'
  };

  render(<ProductCard item={dummyProduct} isCheapest={true} />);

  expect(screen.getByText(/Migros Jet/i)).toBeInTheDocument();
  expect(screen.getByText(/Nutella Fındık Kreması 750 gr/i)).toBeInTheDocument();
  expect(screen.getByText(/₺219.00/i)).toBeInTheDocument();
  expect(screen.getByText(/EN UCUZ GERÇEK FİYAT/i)).toBeInTheDocument();
});
