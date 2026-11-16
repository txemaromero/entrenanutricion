import { weekdayLabel } from './format';

describe('weekdayLabel', () => {
  it('names the weekdays from Monday = 0, like the API', () => {
    expect(weekdayLabel(0, 'es')).toBe('lunes');
    expect(weekdayLabel(6, 'en')).toBe('Sunday');
    expect(weekdayLabel(2, 'ca')).toBe('dimecres');
    expect(weekdayLabel(4, 'es', 'short')).toBe('vie');
  });
});
