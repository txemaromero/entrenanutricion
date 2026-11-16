import { render, screen } from '@testing-library/react';

import type { AdherenceRow } from '../../api/types';
import { AdherenceCard } from './Adherence';

const row = (overrides: Partial<AdherenceRow> = {}): AdherenceRow => ({
  user: { id: 4, fullName: 'Lucía Fernández', email: 'lucia@example.com', profilePhotoUrl: null },
  planName: 'Hipertrofia 4 días',
  planStarted: '2026-01-05',
  sessions: 5,
  scheduled: 11,
  adherencePercent: 45,
  lastSessionDate: '2026-03-27',
  daysSinceLastSession: 3,
  currentWeightKg: 78,
  weightChangeKg: -1.2,
  status: 'at_risk',
  ...overrides,
});

describe('AdherenceCard', () => {
  it('shows adherence, last session and weight change', () => {
    render(<AdherenceCard row={row()} />);

    const card = screen.getByTestId('adherence-4');
    expect(card).toHaveAttribute('data-status', 'at_risk');
    expect(card).toHaveTextContent('45 % de adherencia');
    expect(card).toHaveTextContent('5 de 11 entrenos');
    expect(screen.getByTestId('adherence-status')).toHaveTextContent('En riesgo');
    expect(screen.getByTestId('adherence-last-session')).toHaveTextContent(
      'Último entreno: hace 3 días · Peso: 78 kg (-1,2 kg en 4 semanas)',
    );
  });

  it('a new plan has nothing scheduled and no sessions yet', () => {
    render(
      <AdherenceCard
        row={row({
          sessions: 0,
          scheduled: 0,
          adherencePercent: null,
          lastSessionDate: null,
          daysSinceLastSession: null,
          currentWeightKg: null,
          weightChangeKg: null,
          status: 'on_track',
        })}
      />,
    );

    expect(screen.getByTestId('adherence-4')).toHaveTextContent(
      'Aún no tiene entrenos programados',
    );
    expect(screen.getByTestId('adherence-last-session')).toHaveTextContent(
      'Todavía no ha entrenado',
    );
  });

  it('one day ago and today', () => {
    const { rerender } = render(<AdherenceCard row={row({ daysSinceLastSession: 1 })} />);
    expect(screen.getByTestId('adherence-last-session')).toHaveTextContent('hace 1 día ·');

    rerender(<AdherenceCard row={row({ daysSinceLastSession: 0 })} />);
    expect(screen.getByTestId('adherence-last-session')).toHaveTextContent('Último entreno: hoy');
  });
});
