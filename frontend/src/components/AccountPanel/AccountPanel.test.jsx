import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import AccountPanel from './AccountPanel';
import { accountRequest } from '../../services/accounts';

vi.mock('../../services/accounts', () => ({ accountRequest: vi.fn() }));

test('a signed-in user can apply without opening the owner panel', async () => {
  accountRequest.mockImplementation(async (path) => {
    if (path === '/auth/me') return { email: 'user@example.test', role: 'USER' };
    if (path === '/ownership-applications/mine') return [];
    throw new Error('Unexpected endpoint: ' + path);
  });
  render(<AccountPanel markets={[]} onClose={() => {}} />);
  expect(await screen.findByRole('heading', { name: 'Market sahipliği başvurusu' })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Yetkili olduğunuz şubeler' })).not.toBeInTheDocument();
  expect(accountRequest).not.toHaveBeenCalledWith('/owner/branches');
});


test('returns to login after a newly registered user signs out', async () => {
  let signedIn = false;
  accountRequest.mockImplementation(async (path) => {
    if (path === '/auth/me') {
      if (!signedIn) throw { response: { status: 401 } };
      return { email: 'user@example.test', role: 'USER' };
    }
    if (path === '/auth/register') signedIn = true;
    if (path === '/auth/logout') signedIn = false;
    if (path === '/ownership-applications/mine') return [];
  });
  render(<AccountPanel markets={[]} onClose={() => {}} />);
  fireEvent.click(screen.getByRole('button', { name: 'Hesap oluştur' }));
  fireEvent.change(screen.getByLabelText('E-posta'), { target: { value: 'user@example.test' } });
  fireEvent.change(screen.getByLabelText('Parola'), { target: { value: 'Test-only password' } });
  const register = screen.getByRole('button', { name: 'Kayıt ol' });
  await waitFor(() => expect(register).toBeEnabled());
  fireEvent.click(register);
  fireEvent.click(await screen.findByRole('button', { name: 'Çıkış yap' }));
  expect(await screen.findByRole('form', { name: 'Giriş formu' })).toBeInTheDocument();
});
test('an initial 401 opens the login form without showing an error', async () => {
  accountRequest.mockRejectedValue({ response: { status: 401 } });
  render(<AccountPanel markets={[]} />);
  await waitFor(() => expect(within(screen.getByRole('form', { name: 'Giriş formu' })).getByRole('button', { name: 'Giriş yap' })).toBeEnabled());
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Hesap oluştur' }));
  expect(screen.getByRole('form', { name: 'Hesap oluşturma formu' })).toBeInTheDocument();
});
