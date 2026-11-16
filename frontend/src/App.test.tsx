import { render, screen } from '@testing-library/react';

import App from './App';
import { tokens } from './api/tokens';

describe('App', () => {
  it('shows the welcome screen when there is no session', async () => {
    tokens.clear();
    render(<App />);

    expect(
      await screen.findByRole('heading', { name: 'Bienvenido a entrenanutricion' }),
    ).toBeInTheDocument();
    expect(screen.getByTestId('welcome-register')).toHaveTextContent('Registrarse');
    expect(screen.getByTestId('welcome-login')).toHaveTextContent('Iniciar sesión');
    // It renders the whole app: its role queries need more than the default 5 s on a busy machine.
  }, 20_000);
});
