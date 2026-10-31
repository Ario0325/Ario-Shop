"""تولید تصاویر بندانگشتی WebP برای کارت‌ها، سبد و پیشنهادها.

نسخه‌ها در ``MEDIA_ROOT/thumbs`` ساخته می‌شوند و نامشان شامل هش نام فایل،
زمان تغییر و عرض است، بنابراین تغییر تصویر اصلی URL تازه می‌دهد (سرویس‌ورکر
مسیر ``/media/`` را cache-first نگه می‌دارد).
"""
import hashlib
import logging
import os
import tempfile
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

THUMB_DIR_NAME = 'thumbs'
DEFAULT_QUALITY = 76


def _thumb_dir():
    return Path(settings.MEDIA_ROOT) / THUMB_DIR_NAME


def _source_path(image_field):
    try:
        path = Path(image_field.path)
    except (AttributeError, NotImplementedError, ValueError):
        return None
    return path if path.is_file() else None


def _encode(source, target, width, quality):
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.width > width:
            height = max(round(image.height * width / image.width), 1)
            image = image.resize((width, height), Image.LANCZOS)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        elif image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] == 255:
            image = image.convert('RGB')

        fd, temp_name = tempfile.mkstemp(suffix='.webp.tmp', dir=str(target.parent))
        os.close(fd)
        try:
            image.save(temp_name, 'WEBP', quality=quality, method=4)
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def thumb_path(image_field, width=480, quality=DEFAULT_QUALITY):
    """مسیر فایل بندانگشتی را برمی‌گرداند و در صورت نیاز می‌سازد.

    در هر خطا ``None`` برمی‌گردد تا فراخوان به تصویر اصلی برگردد.
    """
    if not image_field or not getattr(image_field, 'name', ''):
        return None

    source = _source_path(image_field)
    if source is None:
        return None

    try:
        stat = source.stat()
    except OSError:
        return None

    digest = hashlib.md5(
        f'{image_field.name}:{stat.st_mtime_ns}:{width}:{quality}'.encode('utf-8')
    ).hexdigest()[:10]
    target = _thumb_dir() / f'{source.stem}-{int(width)}-{digest}.webp'

    if target.is_file():
        return target

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        _encode(source, target, int(width), quality)
        return target
    except Exception:
        logger.warning('thumbnail generation failed for %s', image_field.name, exc_info=True)
        try:
            if target.exists():
                target.unlink()
        except OSError:
            pass
        return None


def thumb_url(image_field, width=480, quality=DEFAULT_QUALITY):
    """URL بندانگشتی یا URL تصویر اصلی در صورت خطا."""
    target = thumb_path(image_field, width, quality)
    if target is None:
        try:
            return image_field.url if image_field else ''
        except ValueError:
            return ''
    return f'{settings.MEDIA_URL}{THUMB_DIR_NAME}/{target.name}'
