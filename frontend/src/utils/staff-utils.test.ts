import { renderHook } from '@testing-library/react';

import { useFormInit } from '../hooks/useFormInit';
import { moveItem, queryParam, returnToParam } from './lists';
import { checkMediaFile } from './media';
import { caloriesMismatch, distributionSum, macrosKcal } from './nutrition';
import { toNumber } from './numbers';

describe('nutrition helpers (same as the backend)', () => {
  it('computes kcal from macros', () => {
    expect(macrosKcal(150, 150, 55)).toBe(1695);
    expect(macrosKcal()).toBe(0);
  });

  it('flags calories more than 10 % away from the macros', () => {
    expect(caloriesMismatch(1864, 150, 150, 55)).toBe(false);
    expect(caloriesMismatch(1866, 150, 150, 55)).toBe(true);
    expect(caloriesMismatch(1525, 150, 150, 55)).toBe(true);
    expect(caloriesMismatch(undefined, 150, 150, 55)).toBe(false);
  });

  it('adds up the meal distribution', () => {
    expect(distributionSum({ breakfast: 20, lunch: 30, dinner: 30, snacks: 20 })).toBe(100);
    expect(distributionSum({ breakfast: 50 })).toBe(50);
  });
});

describe('list and form helpers', () => {
  it('moves items inside bounds only', () => {
    expect(moveItem(['a', 'b', 'c'], 0, 1)).toEqual(['b', 'a', 'c']);
    expect(moveItem(['a', 'b', 'c'], 2, -2)).toEqual(['c', 'a', 'b']);
    expect(moveItem(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
  });

  it('reads query parameters', () => {
    expect(queryParam('?returnTo=%2Fapp%2Fassignments%2F5&x=1', 'returnTo')).toBe(
      '/app/assignments/5',
    );
    expect(queryParam('', 'tab')).toBeNull();
  });

  it('only returns to pages of the app', () => {
    const returnTo = (value: string) => returnToParam(`?returnTo=${encodeURIComponent(value)}`);

    expect(returnTo('/app/assignments/5')).toBe('/app/assignments/5');
    expect(returnTo('/app/meal-plans')).toBe('/app/meal-plans');
    for (const value of [
      'https://evil.example/app',
      '//evil.example/app',
      '/\\evil.example',
      'javascript:alert(1)',
      '/app/../login',
      '/app/assignments/5?mealPlan=1',
      '/app//evil.example',
      '/welcome',
    ]) {
      expect(returnTo(value)).toBeNull();
    }
    expect(returnToParam('')).toBeNull();
  });

  it('parses typed numbers with a decimal comma', () => {
    expect(toNumber('77,5')).toBe(77.5);
    expect(toNumber(' 12 ')).toBe(12);
    expect(toNumber('')).toBeUndefined();
    expect(toNumber('abc')).toBeUndefined();
  });

  it('pre-checks media files by type and size', () => {
    const file = (type: string, size: number) => new File([new Uint8Array(size)], 'f', { type });
    expect(checkMediaFile(file('image/png', 10))).toBeNull();
    expect(checkMediaFile(file('video/mp4', 10))).toBeNull();
    expect(checkMediaFile(file('image/gif', 10))).toBe('errors.invalid_file_type');
    expect(checkMediaFile(file('image/jpeg', 6 * 1024 * 1024))).toBe('errors.file_too_large');
  });

  it('fills an edit form once per entity, ignoring reloads of the same one', () => {
    const reset = vi.fn();
    const toForm = (data: { id: number; name: string }) => ({ name: data.name });
    const { rerender } = renderHook(({ data }) => useFormInit(data, reset, toForm), {
      initialProps: { data: undefined as { id: number; name: string } | undefined },
    });

    rerender({ data: { id: 1, name: 'A' } });
    rerender({ data: { id: 1, name: 'A (reloaded)' } });
    rerender({ data: { id: 2, name: 'B' } });

    expect(reset.mock.calls).toEqual([[{ name: 'A' }], [{ name: 'B' }]]);
  });
});
