"""Upload naming and validation of the real file type (no reliance on the client's extension or MIME)."""

import warnings
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image, UnidentifiedImageError

IMAGE_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4"}


@deconstructible
class UUIDUploadTo:
    """Store uploads as `<folder>/<uuid4><ext>` so names never collide nor leak user input."""

    def __init__(self, folder: str):
        self.folder = folder

    def __call__(self, instance, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
            ext = ""
        return f"{self.folder}/{uuid4().hex}{ext}"

    def __eq__(self, other):
        return isinstance(other, UUIDUploadTo) and other.folder == self.folder


def _extension(file) -> str:
    return Path(getattr(file, "name", "") or "").suffix.lower()


def _read_head(file, size: int) -> bytes:
    position = file.tell() if hasattr(file, "tell") else 0
    file.seek(0)
    head = file.read(size)
    file.seek(position)
    return head


def is_mp4(file) -> bool:
    head = _read_head(file, 12)
    return len(head) >= 12 and head[4:8] == b"ftyp"


def _image_too_large() -> ValidationError:
    megapixels = settings.MAX_IMAGE_PIXELS // 1_000_000
    return ValidationError(
        f"Images must be {megapixels} megapixels or smaller.", code="image_too_large"
    )


def check_image_pixels(image: Image.Image) -> None:
    """Refuse images that would fill the memory once decoded (decompression bombs).

    The 5 MB limit is not enough: a plain-colour PNG of 100 megapixels weighs a few kB.
    """
    if image.width * image.height > settings.MAX_IMAGE_PIXELS:
        raise _image_too_large()


def validate_image_file(file) -> None:
    if _extension(file) not in IMAGE_EXTENSIONS:
        raise ValidationError("Only JPG, PNG or WEBP images are allowed.", code="invalid_file_type")
    if file.size > settings.MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError("Images must be 5 MB or smaller.", code="file_too_large")
    try:
        file.seek(0)
        with warnings.catch_warnings():
            # Above its own limit Pillow only warns (it fails above twice it): both are refusals.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(file) as image:
                image_format = image.format
                check_image_pixels(image)
                image.verify()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise _image_too_large() from exc
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValidationError("The file is not a valid image.", code="invalid_file_type") from exc
    finally:
        file.seek(0)
    if image_format not in IMAGE_FORMATS:
        raise ValidationError("Only JPG, PNG or WEBP images are allowed.", code="invalid_file_type")


def validate_video_file(file) -> None:
    if _extension(file) not in VIDEO_EXTENSIONS or not is_mp4(file):
        raise ValidationError("Only MP4 videos are allowed.", code="invalid_file_type")
    if file.size > settings.MAX_VIDEO_UPLOAD_BYTES:
        raise ValidationError("Videos must be 50 MB or smaller.", code="file_too_large")


def validate_media_file(file) -> str:
    """Validate an image-or-video upload and return its kind ("image" or "video")."""
    if _extension(file) in VIDEO_EXTENSIONS:
        validate_video_file(file)
        return "video"
    validate_image_file(file)
    return "image"


def media_kind(name: str) -> str:
    return "video" if Path(name or "").suffix.lower() in VIDEO_EXTENSIONS else "image"
