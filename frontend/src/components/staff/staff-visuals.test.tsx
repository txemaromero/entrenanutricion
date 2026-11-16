import { render, screen, within } from '@testing-library/react';

import type { AdherenceList } from '../../api/types';
import { AdherenceOverview } from './AdherenceOverview';
import { Avatar } from './UserProfileBlocks';

// Chart.js needs a canvas; the charts are checked through the data they receive.
vi.mock('react-chartjs-2', () => ({
  Bar: (props: { data: { labels: string[]; datasets: { data: number[] }[] } }) => (
    <pre data-testid="bar-chart">{JSON.stringify(props.data)}</pre>
  ),
  Doughnut: (props: { data: { labels: string[]; datasets: { data: number[] }[] } }) => (
    <pre data-testid="donut-chart">{JSON.stringify(props.data)}</pre>
  ),
}));

const list = (overrides: Partial<AdherenceList> = {}): AdherenceList => ({
  count: 6,
  next: null,
  previous: null,
  counts: [
    { status: 'inactive', count: 1 },
    { status: 'at_risk', count: 2 },
    { status: 'on_track', count: 3 },
  ],
  distribution: [
    { low: 0, high: 19, count: 1 },
    { low: 20, high: 39, count: 0 },
    { low: 40, high: 59, count: 2 },
    { low: 60, high: 79, count: 0 },
    { low: 80, high: 100, count: 3 },
  ],
  averagePercent: 64,
  results: [],
  ...overrides,
});

describe('AdherenceOverview', () => {
  it('sums up the whole list: figures, clients per status and per band', async () => {
    render(<AdherenceOverview data={list()} />);

    const overview = screen.getByTestId('adherence-overview');
    expect(within(overview).getByTestId('stat-average')).toHaveTextContent('64 %');
    expect(within(overview).getByTestId('stat-clients')).toHaveTextContent('6');
    expect(within(overview).getByTestId('stat-on-track')).toHaveTextContent('3Al día');
    expect(within(overview).getByTestId('stat-need-help')).toHaveTextContent('3Necesitan ayuda');

    const donut = JSON.parse((await screen.findByTestId('donut-chart')).textContent!);
    expect(donut.labels).toEqual(['Inactivo', 'En riesgo', 'Al día']);
    expect(donut.datasets[0].data).toEqual([1, 2, 3]);
    // The legend names every status next to its colour and value.
    expect(screen.getByTestId('adherence-donut')).toHaveTextContent('En riesgo2');

    const bands = JSON.parse((await screen.findByTestId('bar-chart')).textContent!);
    expect(bands.labels).toEqual(['0–19 %', '20–39 %', '40–59 %', '60–79 %', '80–100 %']);
    expect(bands.datasets[0].data).toEqual([1, 0, 2, 0, 3]);
  });

  it('shows only the figures when nobody has a plan', () => {
    render(
      <AdherenceOverview
        data={list({
          counts: list().counts.map((entry) => ({ ...entry, count: 0 })),
          averagePercent: null,
        })}
      />,
    );

    expect(screen.getByTestId('stat-average')).toHaveTextContent('—');
    expect(screen.queryByTestId('adherence-donut')).not.toBeInTheDocument();
  });
});

describe('Avatar', () => {
  it('shows the photo, or the initials on a colour that stays the same for each person', () => {
    const { rerender } = render(
      <Avatar user={{ profilePhotoUrl: null, fullName: 'Lucía Fernández', id: 4 }} />,
    );
    const initials = screen.getByTestId('avatar-initials');
    expect(initials).toHaveTextContent('LF');
    const colour = initials.style.background;

    rerender(<Avatar user={{ profilePhotoUrl: null, fullName: 'Lucía Fernández', id: 4 }} />);
    expect(screen.getByTestId('avatar-initials').style.background).toBe(colour);

    rerender(<Avatar user={{ profilePhotoUrl: '/media/photo.jpg', fullName: 'Lucía' }} />);
    expect(screen.queryByTestId('avatar-initials')).not.toBeInTheDocument();
    expect(document.querySelector('img')).toHaveAttribute('src', '/media/photo.jpg');
  });
});
