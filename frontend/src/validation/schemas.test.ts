import {
  ageOn,
  birthDateSchema,
  displayDateToIso,
  emailSchema,
  failedPasswordRules,
  forgotPasswordSchema,
  nameSchema,
  loginSchema,
  MAX_PASSWORD_LENGTH,
  passwordSchema,
  resetPasswordSchema,
} from './schemas';

const messages = (result: { success: boolean; error?: { issues: { message: string }[] } }) =>
  result.success ? [] : (result.error?.issues.map((issue) => issue.message) ?? []);

describe('shared validation (same rules as the backend)', () => {
  it.each([
    ['Ab1#xyz', ['password_too_short']],
    ['lowercase1#', ['password_no_upper']],
    ['UPPERCASE1#', ['password_no_lower']],
    ['NoDigits#ab', ['password_no_digit']],
    ['NoSymbol123', ['password_no_symbol']],
    ['Str0ng#Pass', []],
    ['Ñandú#2025', []],
  ])('password %s', (password, failed) => {
    expect(failedPasswordRules(password)).toEqual(failed);
  });

  it.each(['Ana', 'María José', "O'Connor", 'Jean-Luc', 'Çelik', 'Núñez', 'Àngel'])(
    'accepts name %s',
    (name) => expect(nameSchema.safeParse(name).success).toBe(true),
  );

  it.each(['Ana3', 'Ana!', 'Ana  María', '-Ana', 'Ana_'])('rejects name %s', (name) => {
    expect(messages(nameSchema.safeParse(name))).toEqual(['errors.invalid_name']);
  });

  it('validates emails', () => {
    expect(emailSchema.safeParse('ana@example.com').success).toBe(true);
    expect(messages(emailSchema.safeParse('ana@'))).toEqual(['validation.email']);
    expect(messages(emailSchema.safeParse(''))).toEqual(['validation.required']);
  });

  it('parses dd/mm/aaaa dates', () => {
    expect(displayDateToIso('29/02/2024')).toBe('2024-02-29');
    expect(displayDateToIso('29/02/2023')).toBeNull();
    expect(displayDateToIso('2024-02-29')).toBeNull();
  });

  it('computes ages like the backend', () => {
    expect(ageOn(new Date(2000, 1, 29), new Date(2018, 1, 28))).toBe(17);
    expect(ageOn(new Date(2000, 1, 29), new Date(2018, 2, 1))).toBe(18);
  });

  it('checks the 18–120 age range', () => {
    const schema = birthDateSchema(() => new Date(2026, 5, 15));
    expect(schema.safeParse('15/06/2008').success).toBe(true);
    expect(messages(schema.safeParse('16/06/2008'))).toEqual(['errors.too_young']);
    expect(schema.safeParse('15/06/1906').success).toBe(true);
    expect(messages(schema.safeParse('15/06/1905'))).toEqual(['errors.too_old']);
    expect(messages(schema.safeParse('31/02/2000'))).toEqual(['validation.dateFormat']);
  });
});

describe('password recovery', () => {
  it('asks for a valid email', () => {
    expect(messages(forgotPasswordSchema.safeParse({ email: '' }))).toEqual([
      'validation.required',
    ]);
    expect(forgotPasswordSchema.safeParse({ email: ' ana@example.com ' }).success).toBe(true);
  });

  it('applies the password policy and requires both passwords to match', () => {
    expect(
      messages(resetPasswordSchema.safeParse({ newPassword: 'weak', confirmPassword: 'weak' })),
    ).toContain('errors.password_too_short');
    expect(
      messages(
        resetPasswordSchema.safeParse({
          newPassword: 'Str0ng#Pass',
          confirmPassword: 'Str0ng#Pas',
        }),
      ),
    ).toEqual(['errors.passwords_do_not_match']);
    expect(
      resetPasswordSchema.safeParse({ newPassword: 'Str0ng#Pass', confirmPassword: 'Str0ng#Pass' })
        .success,
    ).toBe(true);
  });
});

describe('password length', () => {
  const login = (password: string) =>
    loginSchema.safeParse({ email: 'ana@example.com', password, rememberMe: false });

  it('stops at the limit of the API', () => {
    const atLimit = 'Aa1#'.repeat(32);

    expect(atLimit).toHaveLength(MAX_PASSWORD_LENGTH);
    expect(passwordSchema.safeParse(atLimit).success).toBe(true);
    expect(login(atLimit).success).toBe(true);
    expect(passwordSchema.safeParse(`${atLimit}a`).success).toBe(false);
    expect(login(`${atLimit}a`).success).toBe(false);
  });
});
