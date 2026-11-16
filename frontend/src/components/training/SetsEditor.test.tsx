import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import type { DayExercise } from '../../api/types';
import { SetsEditor } from './SetsEditor';

const item = (overrides: Partial<DayExercise> = {}): DayExercise => ({
  id: 9,
  order: 1,
  sets: 3,
  reps: 10,
  restSeconds: 60,
  completed: false,
  loggedSets: [],
  lastSets: [
    { reps: 10, weightKg: 40 },
    { reps: 9, weightKg: 42.5 },
  ],
  exercise: { id: 3, name: 'Sentadilla' } as DayExercise['exercise'],
  ...overrides,
});

const typeInto = (testId: string, value: string) =>
  fireEvent(
    screen.getByTestId(testId),
    new CustomEvent('ionInput', { detail: { value }, bubbles: true }),
  );

describe('SetsEditor', () => {
  it('prefills the plan with last session loads and saves the edited sets', async () => {
    const onSave = vi.fn().mockResolvedValue(true);
    render(<SetsEditor item={item()} readOnly={false} onSave={onSave} />);

    fireEvent.click(screen.getByTestId('sets-toggle-1'));

    expect(screen.getByTestId('last-sets-1')).toHaveTextContent(
      'Última vez: 10 × 40 kg · 9 × 42,5 kg',
    );
    expect(screen.getAllByTestId(/^set-row-1-/)).toHaveLength(3);
    typeInto('set-reps-1-0', '12');
    typeInto('set-weight-1-2', '45');
    fireEvent.click(screen.getByTestId('remove-set-1-1'));
    fireEvent.submit(screen.getByTestId('sets-form-1'));

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith([
        { reps: 12, weightKg: 40 },
        { reps: 10, weightKg: 45 },
      ]),
    );
    await waitFor(() => expect(screen.queryByTestId('sets-form-1')).not.toBeInTheDocument());
  });

  it('does not save invalid sets', async () => {
    const onSave = vi.fn().mockResolvedValue(true);
    render(<SetsEditor item={item({ lastSets: null })} readOnly={false} onSave={onSave} />);

    fireEvent.click(screen.getByTestId('sets-toggle-1'));
    typeInto('set-reps-1-0', '500');
    fireEvent.submit(screen.getByTestId('sets-form-1'));

    await waitFor(() =>
      expect(screen.getByTestId('set-reps-1-0')).toHaveAttribute('aria-invalid', 'true'),
    );
    expect(onSave).not.toHaveBeenCalled();
  });

  it('a completed workout only shows the logged sets', () => {
    render(
      <SetsEditor
        item={item({ loggedSets: [{ reps: 8, weightKg: null }] })}
        readOnly
        onSave={vi.fn()}
      />,
    );

    expect(screen.getByTestId('logged-sets-1')).toHaveTextContent('Hecho: 8 rep.');
    expect(screen.queryByTestId('sets-toggle-1')).not.toBeInTheDocument();
  });
});
