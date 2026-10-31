"""فشرده‌سازی تصاویر آپلودی و موجود در media با Pillow."""
import logging
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MAX_DIMENSION = 1600
JPEG_QUALITY = 82
MAX_BYTES = 300 * 1024
SUPPORTED_FORMATS = ('JPEG', 'PNG', 'WEBP')


def _encode(img, image_format, quality):
    buffer = BytesIO()
    if image_format == 'JPEG':
        if img.mode not in ('RGB', 'L'):
            if img.mode in ('RGBA', 'LA', 'P'):
                rgba = img.convert('RGBA')
                background = Image.new('RGB', rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[-1])
                img = background
            else:
                img = img.convert('RGB')
        save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True, 'progressive': True}
    elif image_format == 'WEBP':
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if 'A' in img.getbands() else 'RGB')
        save_kwargs = {'format': 'WEBP', 'quality': quality, 'method': 6}
    else:
        save_kwargs = {'format': 'PNG', 'optimize': True}

    img.save(buffer, **save_kwargs)
    return buffer.getvalue()


def optimize_image_bytes(data, max_dimension=MAX_DIMENSION, quality=JPEG_QUALITY):
    """نسخه فشرده‌شده تصویر را برمی‌گرداند یا None اگر صرفه‌ای نباشد."""
    try:
        with Image.open(BytesIO(data)) as source:
            image_format = source.format
            if image_format not in SUPPORTED_FORMATS or getattr(source, 'is_animated', False):
                return None
            if max(source.size) > max_dimension:
                source.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
            image = ImageOps.exif_transpose(source)

            best = None
            attempts = (quality, 75, 68, 60) if image_format in ('JPEG', 'WEBP') else (quality,)
            for attempt in attempts:
                candidate = _encode(image, image_format, attempt)
                if best is None or len(candidate) < len(best):
                    best = candidate
                if len(best) <= MAX_BYTES:
                    break
    except Exception:
        logger.warning('image optimization failed', exc_info=True)
        return None

    if not best or len(best) >= len(data):
        return None
    return best


def optimize_image_field(field_file, **kwargs):
    """فایل آپلودشده (هنوز ذخیره‌نشده) را در حافظه فشرده می‌کند."""
    if not field_file or getattr(field_file, '_committed', True):
        return False
    try:
        field_file.seek(0)
        original = field_file.read()
        optimized = optimize_image_bytes(original, **kwargs)
        if optimized is None:
            field_file.seek(0)
            return False
        name = field_file.name
        field_file.file = ContentFile(optimized, name=name)
        return True
    except Exception:
        logger.warning('uploaded image optimization failed', exc_info=True)
        return False


def optimize_uploaded_fields(instance, *field_names):
    """همه فیلدهای تصویری جدید همان مدل را قبل از ذخیره فشرده می‌کند."""
    for field_name in field_names:
        optimize_image_field(getattr(instance, field_name, None))


_IMAGE_FIELDS = (
    ('Products_Module', 'ProductImage', 'image'),
    ('Products_Module', 'Category', 'image'),
    ('Products_Module', 'Brand', 'logo'),
    ('AboutUs_Module', 'AboutPage', 'who_we_are_image_front'),
    ('AboutUs_Module', 'AboutPage', 'who_we_are_image_back'),
    ('AboutUs_Module', 'Brand', 'logo'),
    ('AboutUs_Module', 'TeamMember', 'photo'),
    ('AboutUs_Module', 'Testimonial', 'photo'),
)


def referenced_media_names():
    """نام فایل‌های media که در دیتابیس به آن‌ها ارجاع شده است."""
    from django.apps import apps

    names = set()
    for app_label, model_name, field_name in _IMAGE_FIELDS:
        model = apps.get_model(app_label, model_name)
        for name in model.objects.values_list(field_name, flat=True):
            if name:
                names.add(name)
    return names
