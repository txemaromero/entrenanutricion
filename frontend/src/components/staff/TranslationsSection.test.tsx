import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { useForm } from 'react-hook-form';

import type { TranslationsInput } from '../../api/types';
import { useResource } from '../../hooks/useResource';
import i18n from '../../i18n';
import { baseText, translationsForm } from '../../utils/translations';
import { TranslationsSection } from './TranslationsSection';

interface Form {
  name: string;
  steps: { text: string }[];
  translations: TranslationsInput;
}

const typeInto = (testId: string, value: string) =>
  fireEvent(
    screen.getByTestId(testId),
    new CustomEvent('ionInput', { detail: { value }, bubbles: true }),
  );

describe('translations of the catalog', () => {
  afterEach(async () => {
    await act(() => i18n.changeLanguage('es'));
  });

  it('edits the English and Catalan texts with the Spanish one as a hint', () => {
    let values: Form | undefined;
    const Harness = () => {
      const { control, watch } = useForm<Form>({
        defaultValues: {
          name: 'Sentadilla',
          steps: [{ text: 'Ponte de pie' }],
          translations: { en: { name: 'Squat' }, ca: {} },
        },
      });
      values = watch();
      return (
        <TranslationsSection
          control={control}
          stepsField="steps"
          fields={[{ key: 'name', label: 'Nombre' }]}
        />
      );
    };
    render(<Harness />);

    expect(screen.getByTestId('translation-en-name')).toHaveProperty('value', 'Squat');
    expect(screen.getByTestId('translation-en-name')).toHaveAttribute(
      'helper-text',
      'En español: Sentadilla',
    );
    typeInto('translation-en-step-0', 'Stand up');
    expect(values?.translations.en.steps).toEqual(['Stand up']);

    fireEvent(
      screen.getByTestId('translations-language'),
      new CustomEvent('ionChange', { detail: { value: 'ca' } }),
    );
    typeInto('translation-ca-name', 'Esquat');
    expect(values?.translations.ca.name).toBe('Esquat');
    expect(values?.translations.en.name).toBe('Squat');
  });

  it('the Spanish text to edit comes from translations.es', () => {
    const item = {
      translations: { es: { name: 'Sentadilla', steps: ['Baja'] }, en: { name: 'Squat' } },
    };
    expect(baseText(item, 'name', 'Squat (screen language)')).toBe('Sentadilla');
    expect(baseText({}, 'name', 'Fallback')).toBe('Fallback');
    expect(translationsForm(item.translations)).toEqual({ en: { name: 'Squat' }, ca: {} });
    expect(translationsForm(item.translations, { steps: true })).toEqual({
      en: { name: 'Squat', steps: [] },
      ca: { steps: [] },
    });
  });

  it('screens ask for their data again when the language changes', async () => {
    const loader = vi.fn().mockResolvedValue('data');
    renderHook(() => useResource(loader));
    await waitFor(() => expect(loader).toHaveBeenCalledTimes(1));

    await act(() => i18n.changeLanguage('en'));

    await waitFor(() => expect(loader).toHaveBeenCalledTimes(2));
  });
});
