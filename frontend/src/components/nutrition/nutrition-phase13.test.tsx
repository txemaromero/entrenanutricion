import { render, screen, within } from '@testing-library/react';

import type { DiarySummary, Menu } from '../../api/types';
import {
  deviationPct,
  formatGrams,
  per100Of,
  portionOf,
  sumNutrients,
} from '../../utils/nutrition';
import { menuSchema, portionSchema } from '../../validation/nutrition';
import { DiarySummaryCard } from './DiarySummaryCard';
import { MenuView } from './MenuView';

// Chart.js needs a canvas; the chart is checked through the data it receives.
vi.mock('react-chartjs-2', () => ({
  Bar: (props: { data: { datasets: { data: number[] }[] } }) => (
    <pre data-testid="bar-chart">{JSON.stringify(props.data.datasets[0].data)}</pre>
  ),
}));

const nutrients = (calories: number, proteinsG = 0, carbsG = 0, fatsG = 0) => ({
  calories,
  proteinsG,
  carbsG,
  fatsG,
});

describe('nutrition helpers', () => {
  it('formats grams and kilos', () => {
    expect(formatGrams(450, 'es')).toBe('450 g');
    expect(formatGrams(1050, 'es')).toBe('1,1 kg');
    expect(formatGrams(2000, 'en')).toBe('2 kg');
  });

  it('works out portions, per 100 g, sums and deviations', () => {
    const oats = nutrients(380, 13, 60, 7);
    expect(portionOf(oats, 80)).toEqual(nutrients(304, 10.4, 48, 5.6));
    expect(per100Of(nutrients(304, 10.4, 48, 5.6), 80)).toEqual(oats);
    expect(sumNutrients([nutrients(100, 1, 2, 3), nutrients(50, 1, 1, 1)])).toEqual(
      nutrients(150, 2, 3, 4),
    );
    expect(deviationPct(952, 1700)).toBe(-44);
    expect(deviationPct(100, null)).toBeNull();
  });

  it('validates portions and menus like the backend', () => {
    expect(portionSchema.safeParse({ grams: 150 }).success).toBe(true);
    expect(portionSchema.safeParse({ grams: 0 }).success).toBe(false);
    expect(portionSchema.safeParse({ grams: 2001 }).success).toBe(false);
    expect(portionSchema.safeParse({ grams: 1.5 }).success).toBe(false);
    const row = { meal: 'lunch', foodId: 1, grams: 100 };
    expect(menuSchema.safeParse({ items: [row] }).success).toBe(true);
    expect(menuSchema.safeParse({ items: [{ ...row, meal: 'brunch' }] }).success).toBe(false);
    expect(menuSchema.safeParse({ items: Array(61).fill(row) }).success).toBe(false);
  });
});

describe('MenuView', () => {
  const menu: Menu = {
    hasMenu: true,
    meals: [
      {
        meal: 'breakfast',
        items: [
          {
            id: 1,
            food: { id: 7, name: 'Copos de avena', category: 'grains' },
            grams: 80,
            ...nutrients(304, 10.4, 48, 5.6),
          },
        ],
        totals: nutrients(304, 10.4, 48, 5.6),
        target: nutrients(340, 30, 30, 11),
      },
      { meal: 'lunch', items: [], totals: nutrients(0), target: nutrients(510) },
      { meal: 'dinner', items: [], totals: nutrients(0), target: nutrients(510) },
      { meal: 'snacks', items: [], totals: nutrients(0), target: nutrients(340) },
    ],
    totals: nutrients(304, 10.4, 48, 5.6),
    target: nutrients(1700, 150, 150, 55),
    caloriesDeviationPct: -82.1,
    withinTolerance: false,
  };

  it('shows only the meals with foods and the deviation for the staff', () => {
    render(<MenuView menu={menu} showDeviation />);

    const breakfast = screen.getByTestId('menu-meal-breakfast');
    expect(within(breakfast).getByText('Copos de avena')).toBeInTheDocument();
    expect(breakfast).toHaveTextContent('80 g · 304 kcal');
    expect(breakfast).toHaveTextContent('304 / 340 kcal');
    expect(screen.queryByTestId('menu-meal-lunch')).not.toBeInTheDocument();
    expect(screen.getByTestId('menu-deviation')).toHaveTextContent('Fuera del objetivo (-82,1 %)');
  });
});

describe('DiarySummaryCard', () => {
  const day = (date: string, calories: number, entries: number) => ({
    date,
    entries,
    ...nutrients(calories),
  });

  it('summarises the logged days against the target', async () => {
    const summary: DiarySummary = {
      targetCalories: 1700,
      daysLogged: 2,
      averageCalories: 1650,
      days: [day('2026-03-01', 1600, 5), day('2026-03-02', 0, 0), day('2026-03-03', 1700, 6)],
    };

    render(<DiarySummaryCard summary={summary} title="Últimos días" />);

    expect(screen.getByTestId('diary-summary-text')).toHaveTextContent(
      '2 días anotados de 3: media de 1650 kcal. Objetivo: 1700 kcal.',
    );
    // A bar per day (the chart is loaded on demand), with the target line in the legend.
    expect(JSON.parse((await screen.findByTestId('bar-chart')).textContent!)).toEqual([
      1600, 0, 1700,
    ]);
    expect(screen.getByTestId('diary-summary')).toHaveTextContent('Objetivo · 1700 kcal');
    const rows = screen.getAllByTestId('diary-summary-day');
    expect(rows[1]).toHaveTextContent('—');
    expect(rows[2]).toHaveTextContent('1700 kcal');
  });
});
