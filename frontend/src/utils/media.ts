import type { MediaKind } from '../api/types';

export const MEDIA_ACCEPT = 'image/jpeg,image/png,image/webp,video/mp4';
const LIMITS: Record<MediaKind, number> = { image: 5 * 1024 * 1024, video: 50 * 1024 * 1024 };

export const mediaKindOf = (file: File): MediaKind | null => {
  if (file.type === 'video/mp4') return 'video';
  if (['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return 'image';
  return null;
};

/** Client-side pre-check; the backend validates the real file type again. */
export const checkMediaFile = (file: File): string | null => {
  const kind = mediaKindOf(file);
  if (!kind) return 'errors.invalid_file_type';
  if (file.size > LIMITS[kind]) return 'errors.file_too_large';
  return null;
};
