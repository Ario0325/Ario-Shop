"""فشرده‌سازی تصاویر ارجاع‌دار media. به‌صورت پیش‌فرض فقط گزارش می‌دهد."""
import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from Core_Module.images import optimize_image_bytes, referenced_media_names


class Command(BaseCommand):
    help = 'Report or apply compression to media images referenced by the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually rewrite files (a backup is created outside the repo).',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        media_root = Path(settings.MEDIA_ROOT)
        names = sorted(referenced_media_names())

        backup_root = Path(settings.BASE_DIR).parent / f'media_backup_{date.today():%Y%m%d}'
        total_before = 0
        total_after = 0
        changed = 0
        missing = []

        for name in names:
            path = media_root / name
            if not path.is_file():
                missing.append(name)
                continue

            before = path.stat().st_size
            optimized = optimize_image_bytes(path.read_bytes())
            if optimized is None:
                continue

            changed += 1
            total_before += before
            total_after += len(optimized)

            if apply:
                backup_path = backup_root / name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_path)
                path.write_bytes(optimized)

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(f'[{mode}] referenced images: {len(names)}')
        self.stdout.write(f'[{mode}] compressible images: {changed}')
        self.stdout.write(
            f'[{mode}] size: {total_before / 1024:.1f} KB -> {total_after / 1024:.1f} KB'
        )
        if apply and changed:
            self.stdout.write(f'Backup: {backup_root}')
        if missing:
            self.stdout.write(self.style.WARNING(f'Missing files: {len(missing)}'))
            for name in missing[:20]:
                self.stdout.write(f'  {name}')
