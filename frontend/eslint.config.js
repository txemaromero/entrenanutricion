import js from '@eslint/js';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'playwright-report', 'test-results', 'public/sw.js'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // Ionic React probes compound native events (onKeyDown, onMouseEnter…) by creating an inline
      // handler, which the CSP blocks: listen on a native element instead (see ChipMultiSelect).
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'JSXOpeningElement[name.name=/^Ion/] > JSXAttribute[name.name=/^on(Key|Mouse|Pointer|Touch|Double|Context|Drag|Drop|Wheel|Composition|Animation|Transition)/]',
          message:
            'Ionic React probes this event with an inline handler that the CSP blocks: put the listener on a native element.',
        },
      ],
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'zod',
              importNames: ['z'],
              message: "Import z from 'src/validation/zod' (jitless mode for the CSP).",
            },
          ],
        },
      ],
    },
  },
  {
    files: ['src/validation/zod.ts'],
    rules: { 'no-restricted-imports': 'off' },
  },
);
