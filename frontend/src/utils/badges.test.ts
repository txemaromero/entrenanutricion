import i18n from 'i18next';

import { newBadgesText } from './badges';

describe('newBadgesText', () => {
  it('announces the badges a request has just awarded', () => {
    const t = i18n.getFixedT('es');
    expect(newBadgesText(t, [])).toBe('');
    expect(newBadgesText(t, undefined)).toBe('');
    expect(newBadgesText(t, ['first_workout'])).toBe('¡Nueva insignia: Primer paso!');
    expect(newBadgesText(t, ['workouts_10', 'perfect_week'])).toBe(
      '¡Nuevas insignias: Constancia, Semana perfecta!',
    );
    expect(newBadgesText(i18n.getFixedT('en'), ['goal_reached'])).toBe('New badge: Goal reached!');
  });
});
