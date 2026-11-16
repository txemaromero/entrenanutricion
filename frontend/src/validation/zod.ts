import { z } from 'zod';

// Zod would probe `new Function` to compile faster validators, and the Content-Security-Policy
// forbids eval. Every schema imports `z` from here so the setting applies before any is built.
z.config({ jitless: true });

export { z };
