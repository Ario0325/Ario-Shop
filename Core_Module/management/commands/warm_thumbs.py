"""ساخت پیشاپیش بندانگشتی‌های WebP برای تصاویر موجود."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from Core_Module.thumbnails import THUMB_DIR_NAME, thumb_path
from Products_Module.models import Category, ProductImage

WIDTHS = (480, 400, 208, 128, 96)


class Command(BaseCommand):
    help = 'Generate WebP thumbnails for existing product and category images.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--widths',
            default=','.join(str(w) for w in WIDTHS),
            help='Comma separated widths (default: 480,400,208,128,96).',
        )

    def handle(self, *args, **options):
        widths = [int(w) for w in options['widths'].split(',') if w.strip()]
        thumb_dir = Path(settings.MEDIA_ROOT) / THUMB_DIR_NAME
        before = sum(p.stat().st_size for p in thumb_dir.glob('*.webp')) if thumb_dir.is_dir() else 0

        fields = []
        fields.extend(
            obj.image for obj in ProductImage.objects.only('id', 'image').iterator() if obj.image
        )
        fields.extend(
            obj.image for obj in Category.objects.only('id', 'image').iterator() if obj.image
        )

        ok = failed = 0
        for field in fields:
            for width in widths:
                if thumb_path(field, width) is None:
                    failed += 1
                else:
                    ok += 1

        after = sum(p.stat().st_size for p in thumb_dir.glob('*.webp')) if thumb_dir.is_dir() else 0
        self.stdout.write(
            f'widths: {widths} · images: {len(fields)} · variants ready: {ok} · failed: {failed}'
        )
        self.stdout.write(
            f'thumbs on disk: {after / 1024:.1f} KB (new {max(after - before, 0) / 1024:.1f} KB)'
        )
