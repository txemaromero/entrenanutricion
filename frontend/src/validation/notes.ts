import { z } from './zod';

/** Same limit as the backend (`apps.notes.models.MAX_LENGTH`). */
export const NOTE_MAX_LENGTH = 2000;

export const noteSchema = z.object({
  body: z.string().trim().min(1, 'validation.required').max(NOTE_MAX_LENGTH, 'errors.max_length'),
});
export type NoteForm = z.infer<typeof noteSchema>;
