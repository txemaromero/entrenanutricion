import { render, screen, within } from '@testing-library/react';

import { progressApi } from '../../api/client-features';
import type { TrainingStats as Stats } from '../../api/types';
import { TrainingStats } from './TrainingStats';

// Chart.js needs a canvas; the charts are checked through the data they receive.
vi.mock('react-chartjs-2', () => ({
  Bar: (props: { data: { labels: string[]; datasets: { data: number[] }[] } }) => (
    <pre data-testid="bar-chart">{JSON.stringify(props.data)}</pre>
  ),
  Line: (props: { data: { labels: string[]; datasets: { data: number[] }[] } }) => (
    <pre data-testid="line-chart">{JSON.stringify(props.data)}</pre>
  ),
}));

vi.mock('../../api/client-features', () => ({ progressApi: { stats: vi.fn() } }));

const week = (start: string, sessions = 0, minutes = 0, volumeKg = 0) => ({
  start,
  sessions,
  minutes,
  volumeKg,
});

const stats = (overrides: Partial<Stats> = {}): Stats => ({
  weeks: [week('2026-11-02', 3, 80, 0), week('2026-11-09', 2, 70, 1100)],
  muscleGroups: [
    { slug: 'chest', name: 'Pecho', sets: 7 },
    { slug: 'biceps', name: 'Bíceps', sets: 3 },
  ],
  ...overrides,
});

const parse = (element: HTMLElement) => JSON.parse(element.textContent!);

describe('TrainingStats', () => {
  it('shows the totals, the weekly charts and the muscles worked', async () => {
    vi.mocked(progressApi.stats).mockResolvedValue(stats());

    render(<TrainingStats />);

    const totals = await screen.findByTestId('training-totals');
    expect(within(totals).getByTestId('stat-sessions')).toHaveTextContent('5Sesiones');
    expect(within(totals).getByTestId('stat-time')).toHaveTextContent('2,5 h');
    expect(within(totals).getByTestId('stat-volume')).toHaveTextContent('1100 kg');
    expect(within(totals).getByTestId('stat-per-week')).toHaveTextContent('2,5');

    // The charts are loaded on demand (code splitting).
    const [sessions, muscles] = (await screen.findAllByTestId('bar-chart')).map(parse);
    expect(sessions.labels).toEqual(['2 nov', '9 nov']);
    expect(sessions.datasets[0].data).toEqual([3, 2]);
    expect(parse(await screen.findByTestId('line-chart')).datasets[0].data).toEqual([0, 1100]);
    expect(muscles.datasets[0].data).toEqual([7, 3]);
    expect(muscles.labels).toHaveLength(2);

    // The values are also there as tables, with the same wording as the tooltips.
    const table = within(screen.getByTestId('sessions-per-week')).getByRole('table');
    expect(table).toHaveTextContent('2 sesiones · 70 min');
    expect(within(screen.getByTestId('muscles-worked')).getByRole('table')).toHaveTextContent(
      '7 series',
    );
  });

  it('explains how to fill the charts that have no data yet', async () => {
    vi.mocked(progressApi.stats).mockResolvedValue(
      stats({ weeks: [week('2026-11-09', 1, 30, 0)], muscleGroups: [] }),
    );

    render(<TrainingStats />);

    expect(await screen.findByTestId('volume-per-week')).toHaveTextContent(
      'Anota los kilos de tus series',
    );
    expect(screen.getByTestId('muscles-worked')).toHaveTextContent('Completa entrenamientos');
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
  });
});
