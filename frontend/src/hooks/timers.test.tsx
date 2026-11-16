import { act, fireEvent, render, renderHook, screen } from '@testing-library/react';

import { RestTimer } from '../components/training/RestTimer';
import { dayProgress } from '../utils/training';
import { countdownParts } from './useNow';
import { formatClock, useRestTimer } from './useRestTimer';

describe('rest timer', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('counts down, pauses, resumes and reports the end', () => {
    const onFinish = vi.fn();
    const { result } = renderHook(() => useRestTimer(3, onFinish));

    act(() => result.current.start());
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current.remaining).toBe(2);

    act(() => result.current.pause());
    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.remaining).toBe(2);
    expect(result.current.running).toBe(false);

    act(() => result.current.start());
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current.remaining).toBe(0);
    expect(result.current.finished).toBe(true);
    expect(onFinish).toHaveBeenCalledTimes(1);
  });

  it('resets to the preloaded rest', () => {
    const { result } = renderHook(() => useRestTimer(90));
    act(() => result.current.start());
    act(() => vi.advanceTimersByTime(10_000));

    act(() => result.current.reset());

    expect(result.current.remaining).toBe(90);
    expect(result.current.running).toBe(false);
  });

  it('renders the clock with start and reset buttons', () => {
    render(<RestTimer seconds={75} />);
    expect(screen.getByTestId('rest-timer-clock')).toHaveTextContent('01:15');

    fireEvent.click(screen.getByTestId('rest-timer-start'));
    act(() => vi.advanceTimersByTime(5000));

    expect(screen.getByTestId('rest-timer-clock')).toHaveTextContent('01:10');
    expect(screen.getByTestId('rest-timer-pause')).toBeInTheDocument();
  });

  it('formats mm:ss', () => {
    expect(formatClock(0)).toBe('00:00');
    expect(formatClock(605)).toBe('10:05');
  });
});

describe('countdown and day progress', () => {
  it('splits the time left until the target', () => {
    const now = new Date(2026, 10, 2, 10, 0, 0);
    expect(countdownParts(new Date(2026, 10, 3, 12, 30, 15), now)).toEqual({
      days: 1,
      hours: 2,
      minutes: 30,
      seconds: 15,
      done: false,
    });
    expect(countdownParts(new Date(2026, 10, 2, 9, 0), now).done).toBe(true);
  });

  it('computes the % of the day from ticked exercises', () => {
    expect(dayProgress([{ completed: true }, { completed: false }, { completed: true }])).toEqual({
      completed: 2,
      total: 3,
      percent: 67,
    });
    expect(dayProgress([]).percent).toBe(0);
  });
});
