import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import i18n from '../i18n';
import { LanguageMenu } from './LanguageMenu';

describe('LanguageMenu', () => {
  afterEach(async () => {
    await i18n.changeLanguage('es');
  });

  it('has an accessible label in the current language', () => {
    render(<LanguageMenu />);
    expect(screen.getByTestId('language-menu')).toHaveAttribute('aria-label', 'Cambiar idioma');
  });

  it('lists the three languages and switches on selection', async () => {
    render(<LanguageMenu />);

    fireEvent.click(screen.getByTestId('language-menu'));
    const option = await screen.findByTestId('language-option-en');
    expect(screen.getByTestId('language-option-es')).toHaveAttribute('aria-current', 'true');
    expect(screen.getByTestId('language-option-ca')).toHaveTextContent('Català');

    fireEvent.click(option);

    await waitFor(() => expect(i18n.language).toBe('en'));
    expect(screen.getByTestId('language-menu')).toHaveAttribute('aria-label', 'Change language');
  });
});
