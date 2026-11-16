import { tokens } from './tokens';

const FLAG = 'entrenanutricion.session';
const LEGACY = 'entrenanutricion.refresh';

describe('session tokens', () => {
  beforeEach(() => {
    tokens.clear();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('keeps the access token in memory only', () => {
    tokens.setAccess('access-1');
    expect(tokens.getAccess()).toBe('access-1');
    expect(localStorage.length + sessionStorage.length).toBe(0);
  });

  it('never stores a refresh token, only a flag that a session may exist', () => {
    expect(tokens.hasSession()).toBe(false);

    tokens.startSession('access-1');

    expect(tokens.getAccess()).toBe('access-1');
    expect(localStorage.getItem(FLAG)).toBe('1');
    expect(Object.keys(localStorage)).toEqual([FLAG]);
    expect(tokens.hasSession()).toBe(true);
  });

  it('deletes a refresh token left by an older version, without using it', () => {
    sessionStorage.setItem(LEGACY, 'old-refresh');
    localStorage.setItem(LEGACY, 'old-refresh');
    expect(tokens.hasSession()).toBe(false);

    tokens.startSession('access-1');

    expect(sessionStorage.getItem(LEGACY)).toBeNull();
    expect(localStorage.getItem(LEGACY)).toBeNull();
  });

  it('clears everything', () => {
    tokens.startSession('a');
    localStorage.setItem(LEGACY, 'old');
    tokens.clear();
    expect(tokens.getAccess()).toBeNull();
    expect(tokens.hasSession()).toBe(false);
    expect(localStorage.length).toBe(0);
  });

  it('survives unavailable storage', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    expect(tokens.hasSession()).toBe(false);
    spy.mockRestore();
  });
});
