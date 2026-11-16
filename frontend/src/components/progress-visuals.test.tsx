import { render, screen, within } from '@testing-library/react';

import type { WeekDay } from '../api/types';
import { ProgressRing } from './ProgressRing';
import { WeekStrip } from './training/WeekStrip';

describe('ProgressRing', () => {
  it('draws the share done, capped at a full ring, with a label for screen readers', () => {
    const { rerender } = render(
      <ProgressRing ratio={0.25} label="Plan: 25 %" testId="ring">
        <strong>25%</strong>
      </ProgressRing>,
    );
    expect(screen.getByTestId('ring')).toHaveAttribute('data-ratio', '0.25');
    expect(screen.getByRole('img', { name: 'Plan: 25 %' })).toBeInTheDocument();

    rerender(<ProgressRing ratio={1.4} label="Calorías" testId="ring" />);
    expect(screen.getByTestId('ring')).toHaveAttribute('data-ratio', '1.00');

    // Nothing to divide by (no target): an empty ring rather than NaN.
    rerender(<ProgressRing ratio={0 / 0} label="Sin objetivo" testId="ring" />);
    expect(screen.getByTestId('ring')).toHaveAttribute('data-ratio', '0.00');
  });
});

describe('WeekStrip', () => {
  const day = (date: string, scheduled: boolean, completed: boolean): WeekDay => ({
    date,
    scheduled,
    completed,
  });

  it('tells trained, missed, planned and rest days apart and marks today', () => {
    const days = [
      day('2026-11-09', true, true),
      day('2026-11-10', false, true),
      day('2026-11-11', true, false),
      day('2026-11-12', false, false),
      day('2026-11-13', true, false),
      day('2026-11-14', false, false),
      day('2026-11-15', false, false),
    ];

    render(<WeekStrip days={days} today="2026-11-12" />);

    const states = days.map((_, index) =>
      screen.getByTestId(`week-day-${index}`).getAttribute('data-state'),
    );
    expect(states).toEqual(['done', 'done', 'missed', 'rest', 'planned', 'rest', 'rest']);
    const today = screen.getByTestId('week-day-3');
    expect(today).toHaveClass('week-day--today');
    expect(today).toHaveTextContent('jueves, 12 nov: Descanso, hoy');
    expect(within(screen.getByTestId('week-day-2')).getByText(/Sin hacer/)).toBeInTheDocument();
  });
});
