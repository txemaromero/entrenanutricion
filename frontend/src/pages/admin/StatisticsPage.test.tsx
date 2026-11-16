import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { statisticsApi } from '../../api/staff';
import type { StatisticsSummary } from '../../api/types';
import StatisticsPage from './StatisticsPage';

// Chart.js needs a canvas; the charts are checked through the data they receive.
vi.mock('react-chartjs-2', () => ({
  Bar: (props: {
    'aria-label': string;
    data: { labels: string[]; datasets: { data: number[] }[] };
  }) => (
    <pre data-testid="bar-chart" data-label={props['aria-label']}>
      {JSON.stringify(props.data)}
    </pre>
  ),
  Doughnut: (props: {
    'aria-label': string;
    data: { labels: string[]; datasets: { data: number[] }[] };
  }) => (
    <pre data-testid="donut-chart" data-label={props['aria-label']}>
      {JSON.stringify(props.data)}
    </pre>
  ),
}));

vi.mock('../../auth/useAuth', () => ({
  useAuth: () => ({ user: { role: 'admin', emailVerified: true, fullName: 'Laura Admin' } }),
}));

vi.mock('../../api/staff', () => ({
  statisticsApi: {
    summary: vi.fn(),
    years: vi.fn(),
    popularity: vi.fn(),
    growth: vi.fn(),
    sessions: vi.fn(),
    planPopularity: vi.fn(),
  },
}));

const months = (counts: number[]) => counts.map((count, index) => ({ month: index + 1, count }));

const summary: StatisticsSummary = {
  usersByRole: { client: 30, trainer: 1, nutritionist: 2, admin: 1 },
  activeClients: 20,
  pendingAssignment: 6,
  pendingOnboarding: 4,
  sessionsThisMonth: 40,
  sessionsPreviousPeriod: 46,
  newClientsThisMonth: 5,
  newClientsPreviousPeriod: 2,
  // As the API layer leaves it: camelCase keys.
  clientsByGoal: { loseWeight: 12, gainMuscle: 5, maintain: 3 },
};

describe('StatisticsPage', () => {
  beforeEach(() => {
    vi.mocked(statisticsApi.summary).mockResolvedValue(summary);
    vi.mocked(statisticsApi.years).mockResolvedValue([2026]);
    vi.mocked(statisticsApi.popularity).mockResolvedValue([
      { exerciseId: 1, name: 'Sentadilla', count: 9 },
    ]);
    vi.mocked(statisticsApi.growth).mockResolvedValue(months([1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 5, 0]));
    vi.mocked(statisticsApi.sessions).mockResolvedValue(
      months([8, 9, 7, 0, 0, 0, 0, 0, 0, 0, 40, 0]),
    );
    vi.mocked(statisticsApi.planPopularity).mockResolvedValue({
      training: [{ planId: 1, name: 'Quema grasa 3 días', count: 12 }],
      nutrition: [],
    });
  });

  it('shows the figures with their trend and the clients by status and goal', async () => {
    render(
      <MemoryRouter>
        <StatisticsPage />
      </MemoryRouter>,
    );

    const clients = await screen.findByTestId('kpi-clients');
    expect(clients).toHaveTextContent('30Clientes5 altas este mes');
    expect(within(clients).getByText(/altas/).closest('[data-direction]')).toHaveAttribute(
      'data-direction',
      'up',
    );
    const sessions = screen.getByTestId('kpi-sessions');
    expect(sessions).toHaveTextContent('6 menos que el mes pasado');
    expect(within(sessions).getByText(/menos/).closest('[data-direction]')).toHaveAttribute(
      'data-direction',
      'down',
    );
    expect(screen.getByTestId('kpi-team')).toHaveTextContent(
      '4Equipo1 entrenador · 2 nutricionistas · 1 administrador',
    );

    const donuts = await screen.findAllByTestId('donut-chart');
    const byLabel = (charts: HTMLElement[], label: string) =>
      JSON.parse(charts.find((chart) => chart.dataset.label === label)!.textContent!);
    expect(byLabel(donuts, 'Clientes por estado').datasets[0].data).toEqual([20, 6, 4]);
    const goals = byLabel(donuts, 'Clientes activos por objetivo');
    expect(goals.labels).toEqual(['Perder peso', 'Ganar masa muscular', 'Mantener el peso']);
    expect(goals.datasets[0].data).toEqual([12, 5, 3]);

    const bars = await screen.findAllByTestId('bar-chart');
    expect(byLabel(bars, 'Sesiones completadas por mes en 2026').datasets[0].data[10]).toBe(40);
    expect(byLabel(bars, 'Planes de entrenamiento con más clientes').labels).toEqual([
      'Quema grasa 3 días',
    ]);
    expect(await screen.findByText('Todavía no hay planes asignados.')).toBeInTheDocument();
  });
});
