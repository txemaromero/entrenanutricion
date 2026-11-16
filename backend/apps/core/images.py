"""Uploaded images are re-encoded before they are stored (phase 11).

- WebP with a bounded size: a 5 MB phone photo becomes a few hundred kB, enough for the screens
  (profile photos 512 px, exercise/workout/plan images 1600 px).
- No metadata: EXIF can carry the GPS position and the device of whoever took the photo.
- The EXIF orientation is applied first, so photos keep the way they were taken.
- Bounded memory (phase 15): no image above `MAX_IMAGE_PIXELS`, and JPEGs are decoded straight at a
  reduced scale (1/2 to 1/8) when they are much bigger than the result.
"""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from apps.core.files import check_image_pixels

PHOTO_MAX_PX = 512
MEDIA_MAX_PX = 1600
WEBP_QUALITY = 82


def _has_alpha(image: Image.Image) -> bool:
    return "A" in image.getbands() or (image.mode == "P" and "transparency" in image.info)


def optimize_image(upload, max_px: int) -> ContentFile:
    """WebP copy of an (already validated) image upload, at most `max_px` on its longest side."""
    upload.seek(0)
    with Image.open(upload) as source:
        check_image_pixels(source)  # also when the caller skipped the validation
        # Before loading: JPEG's decoder skips detail the thumbnail would throw away anyway.
        source.draft(None, (max_px, max_px))
        image = ImageOps.exif_transpose(source)
        image.load()
    image = image.convert("RGBA" if _has_alpha(image) else "RGB")
    image.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    # No `exif=` argument: Pillow writes the WebP without any metadata.
    image.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=6)
    stem = Path(getattr(upload, "name", "") or "image").stem or "image"
    return ContentFile(buffer.getvalue(), name=f"{stem}.webp")
