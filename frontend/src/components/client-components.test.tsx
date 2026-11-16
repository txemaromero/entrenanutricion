import { fireEvent, render, screen, within } from '@testing-library/react';
import { useForm } from 'react-hook-form';

import type { Macros, MealRow, WeightSummary } from '../api/types';
import { ChipMultiSelect, PasswordRequirements } from './form/fields';
import { MacroBreakdown } from './nutrition/MacroBreakdown';
import { MonthCalendar } from './progress/MonthCalendar';

// Chart.js needs a canvas; the components are checked through the props they pass.
vi.mock('react-chartjs-2', () => ({
  Line: (props: { data: { datasets: { label: string; data: number[] }[] } }) => (
    <pre data-testid="line-chart">{JSON.stringify(props.data.datasets)}</pre>
  ),
  Doughnut: (props: { data: { labels: string[]; datasets: { data: number[] }[] } }) => (
    <pre data-testid="donut-chart">{JSON.stringify(props.data)}</pre>
  ),
  Bar: () => <pre data-testid="bar-chart" />,
}));

describe('PasswordRequirements', () => {
  it('ticks each rule as it is met', () => {
    const { rerender } = render(<PasswordRequirements value="abc" />);
    expect(screen.getByTestId('rule-password_no_lower')).toHaveAttribute('data-ok', 'true');
    expect(screen.getByTestId('rule-password_no_upper')).toHaveAttribute('data-ok', 'false');

    rerender(<PasswordRequirements value="Str0ng#Pass" />);

    ['too_short', 'no_upper', 'no_lower', 'no_digit', 'no_symbol'].forEach((rule) =>
      expect(screen.getByTestId(`rule-password_${rule}`)).toHaveAttribute('data-ok', 'true'),
    );
  });
});

describe('ChipMultiSelect', () => {
  const Harness = ({ onValue }: { onValue: (value: string[]) => void }) => {
    const { control, watch } = useForm<{ items: string[] }>({ defaultValues: { items: [] } });
    onValue(watch('items'));
    return (
      <ChipMultiSelect
        control={control}
        name="items"
        label="Items"
        exclusive={['none']}
        options={[
          { value: 'a', label: 'A' },
          { value: 'b', label: 'B' },
          { value: 'none', label: 'None' },
        ]}
      />
    );
  };

  it('keeps "none" exclusive', () => {
    let value: string[] = [];
    render(<Harness onValue={(current) => (value = current)} />);

    fireEvent.click(screen.getByTestId('option-items-a'));
    fireEvent.click(screen.getByTestId('option-items-b'));
    expect(value).toEqual(['a', 'b']);

    fireEvent.click(screen.getByTestId('option-items-none'));
    expect(value).toEqual(['none']);

    fireEvent.click(screen.getByTestId('option-items-a'));
    expect(value).toEqual(['a']);
    expect(screen.getByTestId('option-items-a')).toHaveAttribute('aria-checked', 'true');
  });

  it('works with the keyboard (Space and Enter) without a listener on the Ionic chip', () => {
    let value: string[] = [];
    render(<Harness onValue={(current) => (value = current)} />);

    fireEvent.keyDown(screen.getByTestId('option-items-b'), { key: ' ' });
    expect(value).toEqual(['b']);
    fireEvent.keyDown(screen.getByTestId('option-items-a'), { key: 'Enter' });
    expect(value).toEqual(['b', 'a']);
    fireEvent.keyDown(screen.getByTestId('option-items-a'), { key: 'Tab' });
    expect(value).toEqual(['b', 'a']);
  });
});

describe('MonthCalendar', () => {
  it('marks completed and scheduled days and navigates months', () => {
    const onChange = vi.fn();
    render(
      <MonthCalendar
        month="2026-11"
        completedDays={['2026-11-02']}
        scheduledDays={['2026-11-02', '2026-11-04']}
        onChangeMonth={onChange}
      />,
    );

    const calendar = screen.getByTestId('month-calendar');
    expect(calendar.querySelector('[data-date="2026-11-02"]')).toHaveAttribute(
      'data-state',
      'completed',
    );
    expect(calendar.querySelector('[data-date="2026-11-04"]')).toHaveAttribute(
      'data-state',
      'scheduled',
    );
    expect(calendar.querySelector('[data-date="2026-11-05"]')).toHaveAttribute(
      'data-state',
      'none',
    );
    expect(calendar.querySelectorAll('[data-date]')).toHaveLength(30);
    // Header row + 6 weeks (1 Nov 2026 is a Sunday).
    expect(calendar.querySelectorAll('[role="row"]')).toHaveLength(7);

    fireEvent.click(screen.getByLabelText('Mes siguiente'));
    expect(onChange).toHaveBeenCalledWith('2026-12');
    fireEvent.click(screen.getByLabelText('Mes anterior'));
    expect(onChange).toHaveBeenCalledWith('2026-10');
  });
});

describe('charts', () => {
  const summary = (weights: number[]): WeightSummary => ({
    goal: 'lose_weight',
    initialWeightKg: 80,
    targetWeightKg: 75,
    currentWeightKg: weights.at(-1) ?? null,
    records: weights.map((weightKg, index) => ({
      id: index,
      date: `2026-0${index + 1}-01`,
      weightKg,
    })),
  });

  it('draws the weight series with initial and target lines and redraws on new data', async () => {
    const { default: WeightChart } = await import('./charts/WeightChart');
    const { rerender } = render(<WeightChart summary={summary([80, 79])} />);

    const datasets = JSON.parse(screen.getByTestId('line-chart').textContent!);
    expect(datasets.map((set: { label: string }) => set.label)).toEqual([
      'Peso',
      'Peso inicial',
      'Peso objetivo',
    ]);
    expect(datasets[0].data).toEqual([80, 79]);
    expect(datasets[1].data).toEqual([80, 80]);
    expect(datasets[2].data).toEqual([75, 75]);

    // Regression #7: a new record re-renders the chart without reloading.
    rerender(<WeightChart summary={summary([80, 79, 78.4])} />);
    expect(JSON.parse(screen.getByTestId('line-chart').textContent!)[0].data).toEqual([
      80, 79, 78.4,
    ]);
  });

  it('shows macro cards, donut percentages and the meal table translated', async () => {
    const macros: Macros = {
      proteins: { grams: 150, kcal: 600, pct: 35.4 },
      carbs: { grams: 150, kcal: 600, pct: 35.4 },
      fats: { grams: 55, kcal: 495, pct: 29.2 },
      totalKcal: 1695,
    };
    const meals: MealRow[] = [
      { meal: 'breakfast', pct: 20, kcal: 340, proteinsG: 30, carbsG: 30, fatsG: 11 },
      { meal: 'snacks', pct: 20, kcal: 340, proteinsG: 30, carbsG: 30, fatsG: 11 },
    ];

    render(<MacroBreakdown macros={macros} meals={meals} />);

    expect(screen.getByTestId('macro-card-proteins')).toHaveTextContent('Proteínas150 g600 kcal');
    const donut = JSON.parse((await screen.findByTestId('donut-chart')).textContent!);
    expect(donut.labels).toEqual([
      'Carbohidratos (35,4 %)',
      'Proteínas (35,4 %)',
      'Grasas (29,2 %)',
    ]);
    const table = screen.getByTestId('meal-table');
    expect(within(table).getByText('Desayuno')).toBeInTheDocument();
    expect(within(table).getByText('Snacks')).toBeInTheDocument();
    expect(table).not.toHaveTextContent('breakfast');
  });
});
