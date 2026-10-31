"""شناسایی فایل‌های media بدون ارجاع در دیتابیس. به‌صورت پیش‌فرض فقط گزارش می‌دهد."""
import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from Core_Module.images import referenced_media_names


class Command(BaseCommand):
    help = 'List (or with --delete and --backup, remove) media files not referenced by the database.'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete orphan files.')
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Copy orphans outside the repo before deleting (required with --delete).',
        )

    def handle(self, *args, **options):
        delete = options['delete']
        backup = options['backup']
        if delete and not backup:
            raise CommandError('--delete requires --backup.')

        media_root = Path(settings.MEDIA_ROOT)
        referenced = referenced_media_names()
        orphans = []
        total_bytes = 0
        for path in sorted(media_root.rglob('*')):
            if not path.is_file() or path.name.startswith('.'):
                continue
            name = path.relative_to(media_root).as_posix()
            if name in referenced:
                continue
            orphans.append(name)
            total_bytes += path.stat().st_size

        mode = 'DELETE' if delete else 'DRY-RUN'
        self.stdout.write(f'[{mode}] referenced files: {len(referenced)}')
        self.stdout.write(f'[{mode}] orphan files: {len(orphans)} ({total_bytes / 1024 / 1024:.2f} MB)')
        for name in orphans[:50]:
            self.stdout.write(f'  {name}')
        if len(orphans) > 50:
            self.stdout.write(f'  ... and {len(orphans) - 50} more')

        if not delete or not orphans:
            return

        backup_root = Path(settings.BASE_DIR).parent / f'media_orphans_backup_{date.today():%Y%m%d}'
        for name in orphans:
            source = media_root / name
            destination = backup_root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            source.unlink()
        self.stdout.write(f'Backup: {backup_root}')
